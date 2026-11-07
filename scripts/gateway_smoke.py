"""Full local Bifrost HTTP roundtrip with scripted model and search evidence.

No provider API key, Tavily credit, or external model call is used.
"""
import json
import os
import secrets
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from freshnessguard.clients import BifrostLLM, post_json
from freshnessguard.engine import Verifier
from freshnessguard.fixtures import ANSWER, FixtureLLM, FixtureSearch
from freshnessguard.server import make_server


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    root = Path.cwd()
    binary = root / "work/build/bifrost-http"
    plugin = root / "work/build/freshnessguard.so"
    if not binary.is_file() or not plugin.is_file():
        raise SystemExit("Run scripts/build-gateway.sh first")
    calls = []

    class Provider(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            raw = json.dumps({"object":"list", "data":[{"id":"fixture-model", "object":"model", "created":1, "owned_by":"fixture"}]}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            messages = body["messages"]
            finish_reason = "stop"
            if messages[0]["role"] == "system":
                content = json.dumps(FixtureLLM().complete(messages[0]["content"], json.loads(messages[-1]["content"])))
                calls.append("internal")
            else:
                content = ANSWER
                calls.append("generation")
                if messages[-1]["content"] == "TRUNCATED_FIXTURE":
                    content, finish_reason = "The latest stable", "length"
            raw = json.dumps({"id":"fixture", "object":"chat.completion", "created":1, "model":"fixture-model",
                "choices":[{"index":0, "message":{"role":"assistant", "content":content}, "finish_reason":finish_reason}],
                "usage":{"prompt_tokens":10, "completion_tokens":10, "total_tokens":20}}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    port = free_port()
    token = secrets.token_urlsafe(32)
    os.environ["BIFROST_URL"] = f"http://127.0.0.1:{port}/openai/v1"
    os.environ["BIFROST_MODEL"] = "openai/fixture-model"
    os.environ.pop("BIFROST_VIRTUAL_KEY", None)
    service = make_server(lambda: Verifier(BifrostLLM(), FixtureSearch(), mode="synthetic_gateway_fixture",
                         clock=lambda: "2026-11-05T12:00:00+00:00"), token)
    service_thread = threading.Thread(target=service.serve_forever, daemon=True)
    service_thread.start()
    appdir = root / "work/gateway-smoke" / secrets.token_hex(4)
    appdir.mkdir(parents=True)
    config = {"setup_token":secrets.token_urlsafe(32),
        "providers":{"openai":{"keys":[{"name":"synthetic-local", "value":"fixture-not-a-provider-key", "models":["*"], "weight":1}],
                    "network_config":{"base_url":f"http://127.0.0.1:{upstream.server_port}/v1"}}},
        "plugins":[{"name":"freshnessguard", "enabled":True, "path":str(plugin), "config":{"service_url":"http://127.0.0.1:8765"}}],
        "client":{"enable_logging":False, "enforce_auth_on_inference":False},
        "config_store":{"enabled":False}, "logs_store":{"enabled":False}}
    (appdir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    log = (appdir / "gateway.log").open("w")
    process = subprocess.Popen([str(binary), "-host", "127.0.0.1", "-port", str(port), "-app-dir", str(appdir)],
                               env={**os.environ, "FRESHNESSGUARD_TOKEN":token}, stdout=log, stderr=subprocess.STDOUT)
    service_closed = False
    try:
        deadline = time.monotonic() + 90
        while True:
            if process.poll() is not None:
                raise RuntimeError(f"Gateway exited; see {appdir / 'gateway.log'}")
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as health:
                    if health.status == 200:
                        break
            except (URLError, OSError):
                pass
            if time.monotonic() > deadline:
                raise RuntimeError("Gateway readiness timeout")
            time.sleep(0.25)
        request = {"model":"openai/fixture-model", "stream":False, "n":1,
                   "messages":[{"role":"user", "content":"Return the sample answer."}]}
        url = f"http://127.0.0.1:{port}/openai/v1/chat/completions"
        plain = post_json(url, request)
        assert "freshnessguard" not in plain, plain
        before = len(calls)
        started = time.perf_counter()
        checked = post_json(url, request, {"x-freshnessguard":"verify"})
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        assert checked["choices"][0]["message"]["content"] == ANSWER, checked
        report = checked["freshnessguard"]["reports"][0]["report"]
        assert [c["verdict"] for c in report["claims"]] == ["outdated", "supported", "not_checked"], report
        assert report["freshness_score"] == 50 and report["coverage"] == 1, report
        assert calls[before:] == ["generation", "internal", "internal", "internal"], calls
        before = len(calls)
        stream_request = Request(url, data=json.dumps({**request, "stream":True}).encode(),
                                 headers={"Content-Type":"application/json", "x-freshnessguard":"verify"})
        try:
            urlopen(stream_request, timeout=5)
            raise AssertionError("Streaming unexpectedly accepted")
        except HTTPError as exc:
            assert exc.code == 400, exc.code
        assert len(calls) == before, calls
        truncated = post_json(url, {**request,"messages":[{"role":"user","content":"TRUNCATED_FIXTURE"}]}, {"x-freshnessguard":"verify"})
        truncated_report = truncated["freshnessguard"]["reports"][0]["report"]
        assert truncated_report["status"] == "incomplete", truncated_report
        assert truncated_report["metrics"]["search_calls"] == 0 and len(calls) == before + 1, calls
        service.shutdown(); service.server_close(); service_thread.join(); service_closed = True
        failed = post_json(url, request, {"x-freshnessguard":"verify"})
        assert failed["freshnessguard"]["status"] == "unavailable", failed
        assert failed["freshnessguard"]["error"]["stage"] == "native_verifier", failed
        assert failed["freshnessguard"]["error"]["code"] == "verifier_unavailable", failed
        assert failed["choices"][0]["message"]["content"] == ANSWER, failed
        result = {"mode":"synthetic_gateway_fixture", "upstream_commit":"afdce01b50a78199f59e38117cd4d5952d038b07",
            "passed":["normal request bypass", "native plugin loaded", "claim extraction through Bifrost", "judging through Bifrost",
                      "cited report delivered over HTTP", "answer preserved", "internal calls do not recurse",
                      "streaming rejected before provider", "unavailable verifier explicitly unverified"],
            "fixture_end_to_end_ms":elapsed, "quality_accuracy":None, "report":report}
        result["passed"].append("truncated provider answer is never verified")
        result["passed"].append("native failure includes safe structured error metadata")
        Path("benchmarks/gateway-smoke.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if k != "report"}, indent=2))
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait()
        log.close()
        if not service_closed:
            service.shutdown(); service.server_close(); service_thread.join()
        upstream.shutdown(); upstream.server_close(); upstream_thread.join()


if __name__ == "__main__":
    main()
