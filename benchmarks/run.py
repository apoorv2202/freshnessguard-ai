"""Protocol benchmark; fixtures do not measure model/search accuracy."""
import argparse
import json
import statistics
import time
from pathlib import Path

from freshnessguard.fixtures import CASES, demo_verifier


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("benchmarks/fixture-results.json"))
    args = parser.parse_args()
    rows = []
    for case in CASES:
        report = demo_verifier().verify(case["answer"])
        actual = report["claims"][0]["verdict"] if report["claims"] else "missing"
        rows.append({"answer":case["answer"], "expected":case["expected"], "actual":actual,
                     "pass":actual == case["expected"], "metrics":report["metrics"]})
    result = {"mode":"synthetic_fixture", "purpose":"Protocol regression only: model and search are scripted",
              "quality_accuracy":None, "cases":len(rows), "passed":sum(r["pass"] for r in rows),
              "median_latency_ms":statistics.median(r["metrics"]["latency_ms"] for r in rows),
              "total_search_calls":sum(r["metrics"]["search_calls"] for r in rows),
              "actual_tavily_credits":0, "rows":rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}, indent=2))
    return 0 if result["passed"] == result["cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
