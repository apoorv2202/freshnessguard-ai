"""Replay the accepted judgement against saved evidence, with zero API calls."""
import argparse
import copy
import json
import time
from pathlib import Path

from freshnessguard.engine import Verifier
from freshnessguard.evidence import is_primary, source_role
from .live import evaluate, summarize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("work/full-live-check.json"))
    parser.add_argument("--output", type=Path, default=Path("work/false-fresh-replay.json"))
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Preserve the original measured run")
    original = json.loads(args.input.read_text(encoding="utf-8"))
    rows = []
    for row in original["rows"]:
        started = time.perf_counter()
        report = copy.deepcopy(row["report"])
        report["mode"] = "offline_evidence_replay"
        report["original_live_metrics"] = report["metrics"]
        report["metrics"] = {"search_calls":0,"llm_calls":0,"tavily_credits":0,
                             "credit_usage_complete":True,"latency_ms":0}
        for claim in report["claims"]:
            decision = {key:copy.deepcopy(claim[key]) for key in ("verdict","reason","citation_ids","quotes","correction")}
            # Old acceptance implies this was false under the old validator.
            # This is a reconstruction, not a saved raw model completion.
            decision["evidence_conflict"] = False
            claim["checked_at"] = report["checked_at"]
            for source in claim["sources"]:
                source["primary_source"] = is_primary(source["url"], claim["source_policy"])
                source["source_role"] = source_role(source["url"])
            Verifier._apply_decision(claim, decision)
        sensitive = [c for c in report["claims"] if c["time_sensitive"]]
        decisive = [c for c in sensitive if c["verdict"] in ("supported","outdated")]
        report["coverage"] = len(decisive) / len(sensitive) if sensitive else 0
        report["freshness_score"] = round(100 * sum(c["verdict"] == "supported" for c in decisive) / len(decisive)) if decisive else None
        report["status"] = "review_required" if any(c["verdict"] != "supported" for c in sensitive) else "supported"
        report["metrics"]["latency_ms"] = round((time.perf_counter() - started)*1000, 2)
        rows.append({**row,"report":report,"evaluation":evaluate(row, report)})
    result = summarize(rows, {"as_of":original["reference_as_of"],
        "purpose":"Offline replay of reconstructed accepted judgements; no new extraction, model, or Tavily calls"}, args.input)
    result["mode"] = "offline_evidence_replay"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
