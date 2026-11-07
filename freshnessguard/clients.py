"""Small HTTP clients. No secrets, prompts or source text are logged."""
import json
import math
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler


DEFAULT_HTTP_TIMEOUT = 20


class ServiceError(Exception):
    """Safe structured diagnostics; never includes an upstream body or headers."""
    def __init__(self, message, *, code="service_error", http_status=None):
        super().__init__(message)
        # Older fixtures/callers still construct this exception by message.
        legacy = re.fullmatch(r"Upstream HTTP ([1-5][0-9]{2})", message)
        self.http_status = http_status if http_status is not None else int(legacy[1]) if legacy else None
        self.code = "http_error" if self.http_status is not None else code

    def diagnostic(self, stage):
        return {"stage":stage, "category":"upstream_error" if self.http_status is not None else "unavailable",
                "code":self.code, "http_status":self.http_status,
                "retryable":self.http_status in (429, 500, 502, 503, 504) or self.code in ("network_error", "timeout")}


class RejectAPIRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never create a redirected request carrying API credentials or payloads.
        if fp is not None:
            fp.close()
        raise ServiceError("API redirect blocked", code="api_redirect_blocked")


urlopen = build_opener(RejectAPIRedirects()).open


def structured_json(content):
    """Accept an object or a single JSON fence; reject prose and duplicate keys."""
    if not isinstance(content, str):
        raise ServiceError("Model output is not text", code="empty_model_response" if content is None else "invalid_model_response")
    content = content.strip()
    if not content:
        raise ServiceError("Model returned empty output", code="empty_model_response")
    if content.startswith("```json\n") and content.endswith("\n```"):
        content = content[8:-4]
    elif content.startswith("```\n") and content.endswith("\n```"):
        content = content[4:-4]

    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(_):
        raise ValueError("Non-finite JSON number")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Non-finite JSON number")
        return number

    try:
        result = json.loads(content, object_pairs_hook=pairs, parse_constant=invalid_constant, parse_float=finite_float)
        if not isinstance(result, dict):
            raise ValueError("Expected object")
        return result
    except (ValueError, RecursionError):
        raise ServiceError("Model returned invalid structured output", code="invalid_model_json") from None


def post_json(url, body, headers=None, timeout=DEFAULT_HTTP_TIMEOUT):
    request = Request(url, data=json.dumps(body).encode(), method="POST",
                      headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ServiceError("Upstream response exceeds limit", code="response_too_large")
            if not raw.strip():
                raise ServiceError("Upstream returned an empty response", code="empty_http_response")
            try:
                return json.loads(raw)
            except (ValueError, RecursionError):
                raise ServiceError("Upstream returned invalid JSON", code="invalid_http_json") from None
    except HTTPError as exc:
        status = exc.code
        exc.close()
        raise ServiceError(f"Upstream HTTP {status}", http_status=status) from None
    except (URLError, TimeoutError, OSError) as exc:
        timed_out = isinstance(exc, TimeoutError) or isinstance(getattr(exc, "reason", None), TimeoutError)
        raise ServiceError("Upstream unavailable", code="timeout" if timed_out else "network_error") from None


class BifrostLLM:
    def __init__(self):
        self.url = os.environ.get("BIFROST_URL", "http://localhost:8080/openai/v1").rstrip("/")
        self.model = os.environ.get("BIFROST_MODEL", "")
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.usage_responses = 0
        if not self.model:
            raise ServiceError("Set BIFROST_MODEL to a configured provider/model")

    def complete(self, system, payload, *, timeout=DEFAULT_HTTP_TIMEOUT):
        headers = {"x-freshnessguard-internal": "1"}
        if os.environ.get("BIFROST_VIRTUAL_KEY"):
            headers["x-bf-vk"] = os.environ["BIFROST_VIRTUAL_KEY"]
        body = {
            "model": self.model, "stream": False, "temperature": 0,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": json.dumps(payload)}],
            "response_format": {"type": "json_object"}, "max_tokens": 2800,
        }
        # The configured Gemini 3 Flash supports minimal thinking. Keeping its
        # reasoning budget low prevents thinking from consuming the JSON budget.
        if self.model == "gemini/gemini-3-flash-preview":
            body["reasoning_effort"] = "minimal"
        result = post_json(self.url + "/chat/completions", body, headers, timeout=timeout)
        try:
            if not isinstance(result, dict):
                raise ServiceError("Invalid model response envelope", code="invalid_model_response")
            usage = result.get("usage")
            usage = usage if isinstance(usage, dict) else {}
            for key in self.usage:
                value = usage.get(key)
                if type(value) is int and value >= 0:
                    self.usage[key] += value
            if type(usage.get("total_tokens")) is int and usage["total_tokens"] >= 0:
                self.usage_responses += 1
            choices = result.get("choices")
            if choices == []:
                raise ServiceError("Model returned no choices", code="empty_model_response")
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                raise ServiceError("Invalid model response envelope", code="invalid_model_response")
            choice = choices[0]
            if choice.get("finish_reason") == "length":
                raise ServiceError("Model output was truncated", code="truncated_model_output")
            if choice.get("finish_reason") == "content_filter":
                raise ServiceError("Model output was filtered", code="filtered_model_output")
            return structured_json(choice["message"]["content"])
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            raise ServiceError("Model returned invalid structured output", code="invalid_model_response") from None


class TavilySearch:
    def __init__(self):
        self.key = os.environ.get("TAVILY_API_KEY", "")
        if not self.key:
            raise ServiceError("Set TAVILY_API_KEY for live verification")

    def search(self, query, *, include_domains=None, exclude_domains=None, max_results=4):
        return post_json("https://api.tavily.com/search", {
            "query": query, "search_depth": "basic", "max_results": min(8, max(1, max_results)),
            "include_answer": False, "include_raw_content": False,
            "include_usage": True, "include_published_date": True,
            "include_domains": include_domains or [],
            "exclude_domains": exclude_domains or [],
        }, {"Authorization": "Bearer " + self.key})
