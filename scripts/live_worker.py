"""Windows-side worker for the WSL live integration test; JSON stdin/stdout only.

Credentials stay in Windows memory and never enter subprocess arguments or logs.
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Also supports invocation by absolute Windows path from WSL interop.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from freshnessguard.config import load_env
from freshnessguard.clients import post_json
from freshnessguard.cli import live_verifier
from freshnessguard.engine import annotate_completion


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["provider", "annotate", "health"])
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    try:
        load_env(args.project / ".env")
        if args.operation == "health":
            print(json.dumps({"ok":True, "model":os.environ.get("BIFROST_MODEL")}))
            return
        body = json.loads(sys.stdin.read(256001))
        if args.operation == "provider":
            # Requests addressed to the local native provider reach the existing
            # authenticated Bifrost, which routes to the real Gemini provider.
            body["model"] = os.environ["BIFROST_MODEL"]
            if body["model"] == "gemini/gemini-3-flash-preview":
                body["reasoning_effort"] = "minimal"
                body["max_tokens"] = 1024
            headers = {"x-freshnessguard-internal":"1"}
            if os.environ.get("BIFROST_VIRTUAL_KEY"):
                headers["x-bf-vk"] = os.environ["BIFROST_VIRTUAL_KEY"]
            result = post_json(os.environ["BIFROST_URL"].rstrip("/") + "/chat/completions", body, headers)
        else:
            verifier = live_verifier()
            verifier.max_claims = 1
            result = annotate_completion(body, verifier)
        print(json.dumps(result))
    except Exception:
        # Never expose a traceback, environment or upstream error body.
        print(json.dumps({"error":"Windows live worker unavailable"}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
