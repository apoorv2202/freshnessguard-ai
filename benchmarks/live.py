"""Bounded live smoke evaluation; labels are never sent to the model."""
import argparse
import json
import statistics
import time
from pathlib import Path

from freshnessguard.cli import live_verifier
from freshnessguard.config import load_env
from freshnessguard.engine import now
from .outcomes import extraction_failure, report_errors, should_stop


def normalize(text):
    return " ".join(text.casefold().split()).strip(" .")


def evaluate(case, report):
    expected = case.get("expected_claims", [{"text":case["answer"], "verdict":case.get("expected")}])
    actual = report["claims"]
    failure = extraction_failure(report)
    used, matches = set(), []
    for item in expected:
        target = normalize(item["text"])
        found = next((i for i, claim in enumerate(actual) if i not in used and
                      (normalize(claim["text"]) == target or target in normalize(claim["text"]))), None)
        if found is not None:
            used.add(found)
        claim = actual[found] if found is not None else None
        error = failure or (claim.get("error") if claim else None)
        if error is None and claim and claim.get("verification_error"):
            from .outcomes import legacy_error
            error = legacy_error(claim["verification_error"], "verification")
        skipped = bool(claim and claim.get("verification_skipped"))
        outcome = (error["category"] if error else "not_evaluated" if skipped
                   else claim["verdict"] if claim else "missing")
        matches.append({"text":item["text"], "expected":item["verdict"], "actual":outcome,
                        "evaluable":not error and not skipped, "extracted":found is not None and failure is None,
                        "error":error})
    warning_ok = (not case.get("expect_input_citation_warning") or any(
        c["assessment"] == "not_official_for_detected_entity" for c in report.get("input_citations", [])))
    errors = report_errors(report)
    evaluable = failure is None and not errors and all(m["evaluable"] for m in matches)
    return {"claims":matches, "extra_claims":[c for i,c in enumerate(actual) if i not in used],
            "extraction_evaluable":failure is None, "evaluable":evaluable,
            "outcome":failure["category"] if failure else errors[0]["category"] if errors else "evaluated" if evaluable else "not_evaluated",
            "errors":errors,
            "input_citation_check_pass":warning_ok,
            "pass":(all(m["expected"] == m["actual"] for m in matches) and warning_ok and len(used) == len(actual)) if evaluable else None}


def summarize(rows, corpus, dataset):
    all_matches = [m for row in rows for m in row["evaluation"]["claims"]]
    matches = [m for m in all_matches if m.get("evaluable", True)]
    extraction_rows = [r for r in rows if r["evaluation"].get("extraction_evaluable", True)]
    extraction_matches = [m for r in extraction_rows for m in r["evaluation"]["claims"]]
    evaluable_rows = [r for r in rows if r["evaluation"].get("evaluable", True)]
    reports = [row["report"] for row in rows]
    extracted = [c for r in extraction_rows for c in r["report"]["claims"]]
    predicted = [c for c in extracted if not c.get("error") and not c.get("verification_error") and not c.get("verification_skipped")]
    true_stale = sum(m["expected"] == "outdated" and m["actual"] == "outdated" for m in matches)
    stale_actual = sum(c["verdict"] == "outdated" for c in predicted)
    stale_expected = sum(m["expected"] == "outdated" for m in matches)
    sensitive = [c for c in predicted if c["time_sensitive"]]
    decisive = [c for c in sensitive if c["verdict"] in ("supported", "outdated")]
    grounded = 0
    for c in decisive:
        sources = {s["id"]:s for s in c["sources"]}
        if c["citation_ids"] and c["quotes"] and all(
            q["source_id"] in c["citation_ids"] and q["source_id"] in sources
            and q["text"] in sources[q["source_id"]]["content"] for q in c["quotes"]):
            grounded += 1
    latencies = sorted(r["metrics"]["latency_ms"] for r in reports)
    confusion = {}
    for m in matches:
        key = m["expected"] + " -> " + m["actual"]
        confusion[key] = confusion.get(key, 0) + 1
    errors = [e for row in rows for e in row["evaluation"].get("errors", [])]
    error_counts = {}
    for error in errors:
        key = error["stage"] + ":" + error["code"]
        error_counts[key] = error_counts.get(key, 0) + 1
    return {"mode":"live", "run_at":now(), "dataset":str(dataset), "reference_as_of":corpus["as_of"],
        "methodology":corpus.get("purpose"), "case_count":len(rows), "expected_claim_count":len(all_matches),
        "evaluable_case_count":len(evaluable_rows), "evaluable_claim_count":len(matches),
        "extraction_evaluable_case_count":len(extraction_rows),
        "extraction_failure_count":len(rows) - len(extraction_rows), "error_counts":error_counts,
        "unavailable_case_count":sum(bool(r["evaluation"].get("errors")) for r in rows),
        "not_evaluated_case_count":sum(r["evaluation"].get("outcome") == "not_evaluated" for r in rows),
        "extraction_availability":len(extraction_rows) / len(rows) if rows else None,
        "pipeline_availability":len(evaluable_rows) / len(rows) if rows else None,
        "end_to_end_success_rate":sum(r["evaluation"]["pass"] is True for r in rows) / len(rows) if rows else None,
        "case_agreement":sum(r["evaluation"]["pass"] is True for r in evaluable_rows) / len(evaluable_rows) if evaluable_rows else None,
        "claim_agreement":sum(m["actual"] == m["expected"] for m in matches) / len(matches) if matches else None,
        "extraction_recall":sum(m.get("extracted", m["actual"] != "missing") for m in extraction_matches) / len(extraction_matches) if extraction_matches else None,
        "extraction_precision":sum(m.get("extracted", m["actual"] != "missing") for m in extraction_matches) / len(extracted) if extracted else None,
        "genuine_missing_claim_count":sum(m["actual"] == "missing" for m in matches),
        "extra_claim_count":sum(len(r["evaluation"]["extra_claims"]) for r in extraction_rows),
        "confusion":confusion, "stale_precision":true_stale / stale_actual if stale_actual else None,
        "stale_recall":true_stale / stale_expected if stale_expected else None,
        "false_positive_stale":stale_actual - true_stale, "false_negative_stale":stale_expected - true_stale,
        "false_fresh_count":sum(m["actual"] == "supported" and m["expected"] != "supported" for m in matches)
            + sum(c["verdict"] == "supported" and not c.get("error") and not c.get("verification_error")
                  for row in extraction_rows for c in row["evaluation"]["extra_claims"]),
        "coverage":len(decisive) / len(sensitive) if sensitive else 0 if matches else None,
        "abstention_count":sum(c["verdict"] == "uncertain" for c in predicted),
        "citation_provenance_rate":grounded / len(decisive) if decisive else None,
        "decisive_primary_source_count":sum(any(s.get("primary_source") and s["id"] in c["citation_ids"] for s in c["sources"]) for c in decisive),
        "median_latency_ms":statistics.median(latencies) if latencies else None,
        "p95_latency_ms":latencies[min(len(latencies)-1, int(0.95 * len(latencies)))] if latencies else None,
        "search_calls":sum(r["metrics"]["search_calls"] for r in reports),
        "source_retrieval_calls":sum(r["metrics"].get("source_retrieval_calls", 0) for r in reports),
        "llm_calls":sum(r["metrics"]["llm_calls"] for r in reports),
        "tavily_credits":sum(r["metrics"]["tavily_credits"] for r in reports),
        "usage_complete":all(r["metrics"]["credit_usage_complete"] for r in reports),
        "model_total_tokens":sum(r["metrics"].get("model_tokens", {}).get("total_tokens", 0) for r in reports),
        "model_token_usage_complete":all(r["metrics"].get("model_token_usage_available", False)
                                         for r in reports if r["metrics"]["llm_calls"]),
        "semantic_citation_entailment":"Requires human review; provenance does not prove entailment", "rows":rows}


def main():
    parser = argparse.ArgumentParser(description="Live smoke benchmark (paid API calls, no retries)")
    parser.add_argument("--cases", type=Path, default=Path("benchmarks/reliability-cases.json"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-live.json"))
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--max-searches", type=int, default=8)
    parser.add_argument("--max-cases", type=int, default=8)
    parser.add_argument("--max-retrievals", type=int, choices=(0, 1), default=1,
                        help="Maximum official-page GETs across the whole run; no retries")
    parser.add_argument("--interval-seconds", type=float, default=20,
                        help="Pacing between cases; no automatic retries")
    args = parser.parse_args()
    if not 0 <= args.max_searches <= 16 or not 1 <= args.max_cases <= 20:
        parser.error("Use 0-16 searches and 1-20 cases per run")
    load_env(args.env_file)
    corpus = json.loads(args.cases.read_text(encoding="utf-8"))
    verifier, rows, searches = live_verifier(), [], 0
    retrievals = 0
    for case in corpus["cases"][:args.max_cases]:
        if rows:
            time.sleep(max(0, min(args.interval_seconds, 60)))
        verifier.max_claims = min(5, args.max_searches - searches)
        verifier.max_retrievals = min(1, args.max_retrievals - retrievals)
        report = verifier.verify(case["answer"])
        searches += report["metrics"]["search_calls"]
        retrievals += report["metrics"].get("source_retrieval_calls", 0)
        rows.append({**case, "report":report, "evaluation":evaluate(case, report)})
        result = summarize(rows, corpus, args.cases)
        stopped = should_stop(report)
        result["run_status"] = "stopped_upstream_error" if stopped else "completed" if len(rows) == min(len(corpus["cases"]), args.max_cases) else "in_progress"
        result["requested_case_count"] = min(len(corpus["cases"]), args.max_cases)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"{case.get('id', len(rows))}: {rows[-1]['evaluation']['claims']}", flush=True)
        if stopped:
            print("Stopping after upstream overload; no retries", flush=True)
            break
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
