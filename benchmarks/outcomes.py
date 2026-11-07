"""Distinguish pipeline availability from model-quality outcomes, including old runs."""
import re


def legacy_error(message, stage):
    match = re.fullmatch(r"Upstream HTTP ([1-5][0-9]{2})", message.strip()) if isinstance(message, str) else None
    if match:
        status = int(match[1])
        return {"stage":stage, "category":"upstream_error", "code":"http_error",
                "http_status":status, "retryable":status in (429, 500, 502, 503, 504)}
    return {"stage":stage, "category":"unavailable", "code":"legacy_failure",
            "http_status":None, "retryable":False}


def extraction_failure(report):
    extraction = report.get("extraction")
    if isinstance(extraction, dict):
        if extraction.get("status") == "ok":
            return None
        return extraction.get("error") or {"stage":"extraction", "category":"unavailable",
            "code":"extraction_not_completed", "http_status":None, "retryable":False}
    # Saved pre-fix reports carried only warnings + empty claims. Do not turn
    # those operational failures into normal extraction false negatives.
    if not report.get("claims") and report.get("warnings"):
        errors = [legacy_error(w, "extraction") for w in report["warnings"]]
        return next((e for e in errors if e["category"] == "upstream_error"), errors[0])
    if report.get("status") in ("unavailable", "upstream_error", "incomplete"):
        return {"stage":"extraction", "category":"unavailable", "code":"legacy_failure",
                "http_status":None, "retryable":False}
    return None


def report_errors(report):
    errors = list(report.get("errors", []))
    failure = extraction_failure(report)
    if failure and failure not in errors:
        errors.append(failure)
    for claim in report.get("claims", []):
        error = claim.get("error")
        if error is None and claim.get("verification_error"):
            error = legacy_error(claim["verification_error"], "verification")
        if error and error not in errors:
            errors.append(error)
    return errors


def should_stop(report):
    return any(e.get("http_status") in (429, 503) for e in report_errors(report))
