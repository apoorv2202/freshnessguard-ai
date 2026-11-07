"""Reclassify a saved benchmark offline. Never loads credentials or calls APIs."""
import argparse
import json
from pathlib import Path

from .live import evaluate, summarize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("benchmark-live.json"))
    parser.add_argument("--output", type=Path, default=Path("work/reclassified-live.json"))
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Preserve the original run: choose a different output path")
    original = json.loads(args.input.read_text(encoding="utf-8"))
    rows = [{**row, "evaluation":evaluate(row, row["report"])} for row in original["rows"]]
    corpus = {"as_of":original.get("reference_as_of"), "purpose":"Offline reclassification of saved observations; no new model or search calls"}
    result = summarize(rows, corpus, args.input)
    result.update(mode="offline_reclassification", source_run_at=original.get("run_at"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
