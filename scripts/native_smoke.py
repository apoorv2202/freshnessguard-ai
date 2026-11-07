"""Run in Linux/WSL: real Bifrost loader and native plugin, synthetic evidence."""
import argparse
import os
import secrets
import subprocess
import threading
from pathlib import Path

from freshnessguard.fixtures import demo_verifier
from freshnessguard.server import make_server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    args = parser.parse_args()
    token = secrets.token_urlsafe(32)
    server = make_server(demo_verifier, token)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(["bash", "scripts/loader-smoke.sh", str(args.upstream.resolve())],
                                env={**os.environ, "FRESHNESSGUARD_TOKEN":token}, check=False)
        return result.returncode
    finally:
        server.shutdown(); server.server_close(); thread.join()


if __name__ == "__main__":
    raise SystemExit(main())
