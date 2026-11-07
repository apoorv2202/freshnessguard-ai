import argparse
import json
import os
import sys
from pathlib import Path

from .clients import BifrostLLM, TavilySearch, ServiceError
from .engine import Verifier
from .fixtures import ANSWER, demo_verifier
from .server import make_server
from .config import load_env
from .retrieval import OfficialPageRetriever


def live_verifier():
    return Verifier(BifrostLLM(), TavilySearch(), retriever=OfficialPageRetriever())


def main():
    parser = argparse.ArgumentParser(description="FreshnessGuard AI")
    parser.add_argument("command", choices=["demo", "verify", "serve"])
    parser.add_argument("--answer-file", type=Path)
    parser.add_argument("--fixture", action="store_true", help="Synthetic offline mode; never live evidence")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args()
    try:
        load_env(args.env_file)
        if args.command == "demo":
            print(json.dumps(demo_verifier().verify(ANSWER), indent=2))
        elif args.command == "verify":
            answer = args.answer_file.read_text(encoding="utf-8") if args.answer_file else sys.stdin.read()
            print(json.dumps((demo_verifier() if args.fixture else live_verifier()).verify(answer), indent=2))
        else:
            token = os.environ.get("FRESHNESSGUARD_TOKEN", "")
            if not args.fixture and len(token) < 24:
                raise ServiceError("Set FRESHNESSGUARD_TOKEN to a random token of at least 24 characters")
            factory = demo_verifier if args.fixture else live_verifier
            factory()  # Fail startup clearly if live configuration is missing.
            server = make_server(factory, token, args.port)
            print(f"FreshnessGuard {'SYNTHETIC FIXTURE' if args.fixture else 'LIVE'} on http://127.0.0.1:{args.port}", flush=True)
            try:
                server.serve_forever()
            finally:
                server.server_close()
    except (ServiceError, ValueError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
