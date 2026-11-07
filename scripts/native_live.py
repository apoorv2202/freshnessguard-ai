"""WSL live native-plugin test using Windows credential custody.

Local bridge is test infrastructure for WSL NAT, not a production deployment.
One real Gemini generation, one extraction, at most one search and one judge.
"""
import argparse
import json
import os
import secrets
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PureWindowsPath
from urllib.error import URLError
from urllib.request import urlopen

from freshnessguard.clients import post_json
from scripts.gateway_smoke import free_port


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows-python", required=True)
    parser.add_argument("--windows-project", required=True)
    args = parser.parse_args()
    root = Path.cwd()
    worker = str(PureWindowsPath(args.windows_project) / "scripts" / "live_worker.py")
    token = secrets.token_urlsafe(32)
    counts = {"provider":0, "annotate":0}

    class Bridge(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            operation = "annotate" if self.path == "/annotate" else "provider"
            if operation == "annotate" and self.headers.get("Authorization") != "Bearer " + token:
                self.send_error(401); return
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 256000:
                self.send_error(413); return
            counts[operation] += 1
            try:
                result = subprocess.run([args.windows_python, worker, operation, "--project", args.windows_project],
                    input=self.rfile.read(length), capture_output=True, timeout=120)
                raw = result.stdout
                value = json.loads(raw)
                if result.returncode or "error" in value:
                    self.send_error(503); return
                self.send_response(200); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
            except Exception:
                self.send_error(503)

    bridge = ThreadingHTTPServer(("127.0.0.1", 0), Bridge)
    thread = threading.Thread(target=bridge.serve_forever, daemon=True); thread.start()
    port = free_port()
    appdir = root / "work/native-live" / secrets.token_hex(4)
    appdir.mkdir(parents=True)
    config = {"setup_token":secrets.token_urlsafe(32),
        "providers":{"livebridge":{"custom_provider_config":{"base_provider_type":"openai"},
            "keys":[{"name":"local-bridge", "value":"local-bridge-not-a-secret", "weight":1,"models":["*"]}],
            "network_config":{"base_url":f"http://127.0.0.1:{bridge.server_port}/v1"}}},
        "plugins":[{"name":"freshnessguard","enabled":True,"path":str(root / "work/build/freshnessguard.so"),
            "config":{"service_url":f"http://127.0.0.1:{bridge.server_port}"}}],
        "client":{"enable_logging":False,"enforce_auth_on_inference":False},
        "config_store":{"enabled":False},"logs_store":{"enabled":False}}
    (appdir / "config.json").write_text(json.dumps(config))
    log = (appdir / "gateway.log").open("w")
    process = subprocess.Popen([str(root / "work/build/bifrost-http"), "-host","127.0.0.1","-port",str(port),"-app-dir",str(appdir)],
        env={**os.environ,"FRESHNESSGUARD_TOKEN":token}, stdout=log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 60
        while True:
            if process.poll() is not None:
                raise RuntimeError("Native gateway failed; private work/native-live log contains diagnostics")
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as health:
                    if health.status == 200: break
            except (URLError, OSError):
                pass
            if time.monotonic() > deadline: raise RuntimeError("Gateway readiness timeout")
            time.sleep(0.25)
        start = time.perf_counter()
        result = post_json(f"http://127.0.0.1:{port}/openai/v1/chat/completions", {
            "model":"livebridge/gemini", "stream":False,"n":1,"max_tokens":100,"reasoning_effort":"minimal",
            "messages":[{"role":"user","content":"For a software test, output exactly this sentence, without explanation: The latest stable Python release series is 3.11."}]},
            {"x-freshnessguard":"verify"}, timeout=145)
        envelope = result.get("freshnessguard", {})
        reports = envelope.get("reports", [])
        if not reports:
            raise RuntimeError("Native gateway did not return a live report")
        report = reports[0]["report"]
        text = result["choices"][0]["message"]["content"]
        generation_complete = result["choices"][0].get("finish_reason") == "stop"
        generation_matches_control = text.strip().rstrip(".") == "The latest stable Python release series is 3.11"
        assert text == report["original_answer"], "Original answer changed"
        assert report["mode"] == "live", "Expected live report"
        assert report["metrics"]["search_calls"] <= 1, "Live test exceeded search budget"
        live_complete = (generation_complete and generation_matches_control and bool(report["claims"]) and report["metrics"]["search_calls"] == 1
                         and any(c["sources"] for c in report["claims"]) and not report["warnings"]
                         and not any(c.get("verification_error") for c in report["claims"]))
        record = {"run_at":report["checked_at"],"mode":"native_live", "model":report.get("model"),
            "topology":"WSL native Bifrost -> local stdio bridge -> existing authenticated Windows Bifrost -> Gemini; native post-hook -> Windows verifier -> Tavily/Gemini",
            "live_pipeline_complete":live_complete,"generation_complete":generation_complete,
            "generation_matches_control":generation_matches_control,
            "original_preserved":True,"bridge_calls":counts,
            "end_to_end_ms":round((time.perf_counter()-start)*1000,2),"report":report}
        (root / "work/native-live-result.json").write_text(json.dumps(record,indent=2))
        print(json.dumps({k:v for k,v in record.items() if k != "report"},indent=2))
        if not live_complete:
            raise SystemExit("Native interception worked but live verification was incomplete; see private result")
    finally:
        process.terminate()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill(); process.wait()
        log.close(); bridge.shutdown(); bridge.server_close(); thread.join()


if __name__ == "__main__":
    main()
