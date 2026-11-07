"""Loopback-only MVP service; intentionally no public deployment surface."""
import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .engine import annotate_completion


def make_server(verifier_factory, token, port=8765):
    slots = threading.BoundedSemaphore(2)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def reply(self, status, body):
            raw = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path == "/health":
                self.reply(200, {"status": "ok"})
            else:
                self.reply(404, {"error": "Not found"})

        def do_POST(self):
            if self.path not in ("/verify", "/annotate"):
                return self.reply(404, {"error": "Not found"})
            if token and not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + token):
                return self.reply(401, {"error": "Unauthorized"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self.reply(400, {"error": "Invalid content length"})
            if not 0 < length <= 256000:
                return self.reply(413, {"error": "Body must contain 1–256000 bytes"})
            if not slots.acquire(blocking=False):
                return self.reply(429, {"error": "Verification busy"})
            try:
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Expected JSON object")
                verifier = verifier_factory()
                result = (verifier.verify(body.get("answer")) if self.path == "/verify"
                          else annotate_completion(body, verifier))
                self.reply(200, result)
            except (ValueError, TypeError, AttributeError):
                self.reply(400, {"error": "Invalid answer or completion"})
            except Exception:
                # No upstream body or credentials leak into errors.
                self.reply(503, {"error": "Verification unavailable"})
            finally:
                slots.release()

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server
