"""Publish selected public metrics and source URLs, never local credentials."""
import json
import os
from pathlib import Path

from freshnessguard.config import load_env


def claim_view(claim):
    return {"text":claim["text"], "verdict":claim["verdict"], "reason":claim["reason"],
            "validation_error":claim.get("validation_error"),
            "citations":[{"id":s["id"],"url":s["url"],"primary":s.get("primary_source", False)}
                         for s in claim["sources"] if s["id"] in claim["citation_ids"]]}


def write_public(path, data):
    text = json.dumps(data, indent=2)
    secrets = [os.environ.get(k) for k in ("TAVILY_API_KEY", "BIFROST_VIRTUAL_KEY", "FRESHNESSGUARD_TOKEN")]
    if any(value and value in text for value in secrets):
        raise RuntimeError("Refusing to publish data containing a configured credential")
    path.write_text(text, encoding="utf-8")


def main():
    load_env(".env")
    runs = []
    for name in ("baseline-live", "reliability-live", "final-live"):
        path = Path("work") / (name + ".json")
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        summary = {k:v for k,v in data.items() if k != "rows"}
        rows = [{"id":row.get("id"), "answer":row["answer"], "evaluation":row.get("evaluation"),
                 "legacy_expected":row.get("expected"), "legacy_actual":row.get("actual"),
                 "warnings":row["report"]["warnings"], "metrics":row["report"]["metrics"],
                 "claims":[claim_view(c) for c in row["report"]["claims"]]} for row in data["rows"]]
        runs.append({"name":name, "summary":summary, "rows":rows})
    write_public(Path("benchmarks/live-results.json"), {
        "warning":"Runs use different revisions and overlapping cases. Do not aggregate them into an accuracy score. Last two runs stopped at HTTP 429; the latest grounded-subject guard was added afterwards and is offline-tested only.",
        "runs":runs})
    native = json.loads(Path("work/native-live-result.json").read_text(encoding="utf-8"))
    record = {k:v for k,v in native.items() if k != "report"}
    record["live_pipeline_complete"] = False
    record["transport_roundtrip_demonstrated"] = True
    record["review"] = "FAILED semantic review: generation truncated to a fragment, incorrectly judged using unrelated .NET evidence. Fixed by rejecting truncated provider answers and requiring concrete grounded subjects. Corrected native live run remains blocked on Gemini quota."
    record["original_answer"] = native["report"]["original_answer"]
    record["observed_claims"] = [claim_view(c) for c in native["report"]["claims"]]
    record["metrics"] = native["report"]["metrics"]
    write_public(Path("benchmarks/native-live.json"), record)
    print("Published credential-screened live metrics and reviewed native outcome")


if __name__ == "__main__":
    main()
