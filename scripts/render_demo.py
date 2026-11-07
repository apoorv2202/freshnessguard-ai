"""Render a clearly labelled synthetic or live report."""
import argparse
import json
from pathlib import Path
from freshnessguard.fixtures import ANSWER, demo_verifier
from freshnessguard.reporting import render_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    parser.add_argument("--case", help="Case id in a benchmark file")
    parser.add_argument("--output", type=Path, default=Path("demo/report.html"))
    parser.add_argument("--note", help="Visible provenance/revision note")
    args = parser.parse_args()
    if args.report:
        data = json.loads(args.report.read_text(encoding="utf-8"))
        report = (next(row["report"] for row in data["rows"] if row.get("id") == args.case)
                  if "rows" in data else data.get("report", data))
    else:
        report = demo_verifier().verify(ANSWER)
    if args.note:
        report["run_note"] = args.note
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(report), encoding="utf-8")
    args.output.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {args.output}; evidence mode: {report['mode']}")


if __name__ == "__main__":
    main()
