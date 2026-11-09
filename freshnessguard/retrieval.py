"""One public official HTTPS page, no redirects, credentials, proxies or crawling."""
import hashlib
import http.client
import ipaddress
import queue
import re
import socket
import ssl
import threading
import time
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit

from .clients import ServiceError
from .evidence import is_primary, source_role

MAX_BYTES = 256_000
MAX_TEXT = 16_000
TIMEOUT = 6.0
MAX_HEADERS = 32_768
PREVIEW_RELEASE_PATH = re.compile(
    r"\d(?:a|b|rc)\d+(?=$|[-._/])"
    r"|(?:^|[-._/])(?:alpha|beta|preview|early[-._]access|ea|pre-?release|release[-._]candidate|rc|nightly|dev)\d*(?=$|[-._/])",
    re.I,
)


class HeaderBudget:
    def __init__(self, stream):
        self.stream, self.used = stream, 0

    def readline(self, limit=-1):
        remaining = MAX_HEADERS + 1 - self.used
        if remaining <= 0:
            raise ServiceError("Source headers exceed limit", code="source_headers_too_large")
        line = self.stream.readline(remaining if limit < 0 else min(limit, remaining))
        self.used += len(line)
        if self.used > MAX_HEADERS:
            raise ServiceError("Source headers exceed limit", code="source_headers_too_large")
        return line

    def __getattr__(self, name):
        return getattr(self.stream, name)


class BoundedResponse(http.client.HTTPResponse):
    def begin(self):
        original = self.fp
        self.fp = HeaderBudget(original)
        try:
            super().begin()
        finally:
            self.fp = original


def validate_url(url, policy):
    """Only explicit operator-owned host/path rules; no suffix wildcard trust."""
    try:
        if not isinstance(url, str) or len(url) > 1000 or re.search(r"[\s\\%\x00-\x1f\x7f]", url):
            raise ValueError()
        p = urlsplit(url)
        if (p.scheme != "https" or not p.hostname or p.username or p.password
                or p.port not in (None, 443) or p.query or p.fragment
                or p.hostname.endswith(".") or not p.hostname.isascii()
                or any(part in (".", "..") for part in p.path.split("/"))):
            raise ValueError()
        if not is_primary(url, policy):
            raise ValueError()
        if not any(p.hostname == rule["host"] and re.fullmatch(rule["path"], p.path)
                   for rule in policy.get("retrieval_rules", [])):
            raise ValueError()
        return urlunsplit(("https", p.hostname, p.path or "/", "", ""))
    except (ValueError, TypeError, KeyError):
        raise ServiceError("Source URL blocked", code="blocked_source_url") from None


def target_for(claim):
    """Prefer artifact references in ranked official snippets, then source indexes.

    Links are untrusted URL data, never commands. No inferred version URLs.
    Only the configured apex/www alias may be canonicalized to an index origin.
    """
    policy = claim["source_policy"]
    stable_scope = re.search(r"\b(?:stable|lts|long.term support)\b", claim["text"], re.I)
    targets = []
    for position, source in enumerate(claim["sources"]):
        if not is_primary(source["url"], policy) or source.get("future_dated"):
            continue
        references = [(source["url"], "search_result")]
        references += [(m.group(0).rstrip(".,;)]}"), "snippet_link") for m in re.finditer(
            r"https://[^\s<>\"']+|(?<![\w./])(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}/[^\s<>\"']+", source["content"][:5000])][:16]
        for reference, kind in references:
            url = reference if reference.startswith("https://") else "https://" + reference
            try:
                p = urlsplit(url)
                if p.username or p.password or p.port not in (None, 443):
                    continue
                for index in policy.get("release_indexes", []):
                    origin = urlsplit(index)
                    if p.hostname and p.hostname.removeprefix("www.") == origin.hostname.removeprefix("www."):
                        url = urlunsplit((p.scheme, origin.netloc, p.path, p.query, p.fragment))
                        break
                url = validate_url(url, policy)
            except (ServiceError, ValueError):
                continue
            role = source_role(url)
            if role not in ("version_snapshot", "release_index"):
                continue
            if stable_scope and role == "version_snapshot" and PREVIEW_RELEASE_PATH.search(urlsplit(url).path):
                # Save the single fetch for an eligible candidate. A URL without
                # a preview marker still needs proof from the page itself.
                continue
            targets.append(((0 if role == "version_snapshot" else 1, position),
                            {"url":url, "parent_source_id":source["id"],
                             "discovery":kind, "original_reference":reference}))
    return min(targets, key=lambda item:item[0])[1] if targets else None


class VisibleText(HTMLParser):
    """Strip executable/hidden containers without executing or loading anything."""
    SKIP = {"script", "style", "noscript", "template", "svg", "iframe", "object", "head", "nav", "footer"}
    BLOCK = {"p", "div", "section", "article", "main", "h1", "h2", "h3", "h4", "li", "tr", "br"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.parts = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = tag in self.SKIP or "hidden" in attrs or attrs.get("aria-hidden") == "true"
        if tag not in {"br", "img", "meta", "link", "hr", "input", "wbr", "source"}:
            self.stack.append((tag, hidden))
            if len(self.stack) > 128:
                raise ServiceError("Source HTML nesting exceeds limit", code="source_html_complex")
        if not any(skip for _, skip in self.stack) and tag in self.BLOCK:
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        for index in range(len(self.stack)-1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break
        if not any(skip for _, skip in self.stack) and tag in self.BLOCK:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if not any(skip for _, skip in self.stack):
            self.parts.append(data)

    def text(self):
        return "\n\n".join(" ".join(p.split()) for p in "".join(self.parts).split("\n\n") if p.strip())


def public_address(host, deadline):
    # OS DNS can block beyond socket timeouts. A single daemon resolver cannot
    # make any HTTP request and cannot hold up this answer past its deadline.
    results = queue.Queue(maxsize=1)
    def resolve():
        try:
            results.put(socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM))
        except OSError:
            results.put(None)
    threading.Thread(target=resolve, daemon=True).start()
    try:
        addresses = results.get(timeout=min(1.0, max(0.001, deadline-time.monotonic())))
    except queue.Empty:
        raise ServiceError("Source DNS timed out", code="source_timeout") from None
    if not addresses or len(addresses) > 64:
        raise ServiceError("Source DNS unavailable", code="source_dns_error")
    for _, _, _, _, address in addresses:
        ip = ipaddress.ip_address(address[0])
        transition = isinstance(ip, ipaddress.IPv6Address) and (
            ip.sixtofour is not None or ip.teredo is not None
            or ip in ipaddress.ip_network("64:ff9b::/96")
            or ip in ipaddress.ip_network("64:ff9b:1::/48"))
        if not ip.is_global or ip.is_multicast or getattr(ip, "ipv4_mapped", None) or transition:
            raise ServiceError("Non-public source address blocked", code="blocked_source_address")
    return addresses[0]


class OfficialPageRetriever:
    def retrieve(self, url, policy):
        url = validate_url(url, policy)
        deadline = time.monotonic() + TIMEOUT
        family, socktype, proto, _, address = public_address(urlsplit(url).hostname, deadline)
        p = urlsplit(url)
        context = ssl.create_default_context()
        connection = http.client.HTTPSConnection(p.hostname, timeout=TIMEOUT, context=context)
        connection.response_class = BoundedResponse
        raw_socket = socket.socket(family, socktype, proto)
        active = [raw_socket]
        def stop():
            try:
                active[0].shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            active[0].close()
        timer = threading.Timer(max(0.001, deadline-time.monotonic()), stop)
        timer.daemon = True
        timer.start()
        response = None
        def remaining():
            value = deadline-time.monotonic()
            if value <= 0:
                raise ServiceError("Source retrieval timed out", code="source_timeout")
            return value
        try:
            raw_socket.settimeout(remaining())
            raw_socket.connect(address)  # pinned validated IP, no second DNS lookup
            secured = context.wrap_socket(raw_socket, server_hostname=p.hostname,
                                          do_handshake_on_connect=False)
            active[0] = secured
            secured.settimeout(remaining())
            secured.do_handshake()
            connection.sock = secured
            connection.request("GET", p.path, headers={"Host":p.hostname, "Accept":"text/html,text/plain",
                "Accept-Encoding":"identity", "User-Agent":"FreshnessGuard/0.1 evidence-check"})
            response = connection.getresponse()
            remaining()
            if 300 <= response.status < 400:
                raise ServiceError("Source redirect blocked", code="source_redirect_blocked")
            if response.status != 200:
                raise ServiceError("Source HTTP failure", code="source_http_error")
            content_type = response.getheader("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in ("text/html", "text/plain") or response.getheader("Content-Encoding", "identity").lower() != "identity":
                raise ServiceError("Source media type blocked", code="source_media_type")
            length = response.getheader("Content-Length")
            if length and (not length.isdecimal() or int(length) > MAX_BYTES):
                raise ServiceError("Source exceeds byte limit", code="source_too_large")
            body = bytearray()
            while True:
                secured.settimeout(remaining())
                chunk = response.read1(min(8192, MAX_BYTES + 1 - len(body)))
                if not chunk:
                    break
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise ServiceError("Source exceeds byte limit", code="source_too_large")
                if time.monotonic() >= deadline:
                    raise ServiceError("Source retrieval timed out", code="source_timeout")
            decoded = body.decode("utf-8", errors="strict")
            if content_type == "text/html":
                parser = VisibleText()
                parser.feed(decoded)
                parser.close()
                text = parser.text()
            else:
                text = decoded
            if not text.strip():
                raise ServiceError("Source has no visible text", code="source_empty")
            remaining()
            return {"url":url, "content":text[:MAX_TEXT], "body_sha256":hashlib.sha256(body).hexdigest(),
                    "text_sha256":hashlib.sha256(text[:MAX_TEXT].encode()).hexdigest(),
                    "bytes":len(body), "text_truncated":len(text) > MAX_TEXT,
                    "content_type":content_type}
        except ServiceError:
            raise
        except TimeoutError:
            raise ServiceError("Source retrieval timed out", code="source_timeout") from None
        except (OSError, http.client.HTTPException, UnicodeError, ValueError):
            code = "source_timeout" if time.monotonic() >= deadline else "source_unavailable"
            raise ServiceError("Source retrieval unavailable", code=code) from None
        finally:
            timer.cancel()
            if response is not None:
                response.close()
            connection.close()
            stop()
