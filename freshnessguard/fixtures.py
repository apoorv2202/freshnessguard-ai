"""Synthetic protocol fixtures, deliberately not presented as live research."""
from .engine import Verifier

ANSWER = "The latest stable version of ExampleSDK is 3.0. ExampleCloud currently costs $10 per month. Water is made of hydrogen and oxygen."
CASES = [
    {"answer": "The latest stable version of ExampleSDK is 3.0.", "expected": "outdated",
     "evidence": "As of 2026-11-05, the latest stable version of ExampleSDK is 4.0.",
     "correction": "The latest stable version of ExampleSDK is 4.0 as of 2026-11-05."},
    {"answer": "ExampleCloud currently costs $10 per month.", "expected": "supported",
     "evidence": "As of 2026-11-05, ExampleCloud currently costs $10 per month."},
    {"answer": "The current CEO of ExampleCorp is Ada Chen.", "expected": "uncertain",
     "evidence": "ExampleCorp does not publish a current leadership list."},
    {"answer": "ExampleSDK 3.0 was released in 2024.", "expected": "not_checked",
     "evidence": ""},
    {"answer": "Water is made of hydrogen and oxygen.", "expected": "not_checked", "evidence": ""},
    {"answer": "ExampleApp is currently available in India.", "expected": "uncertain",
     "evidence": "One page says available; another says withdrawn. No effective dates are given."},
    {"answer": "ExampleDB currently supports unlimited storage.", "expected": "uncertain",
     "evidence": "In 2020 ExampleDB supported unlimited storage."},
    {"answer": "ExampleTool is the latest release.", "expected": "uncertain", "evidence": ""},
]


class FixtureLLM:
    def complete(self, system, payload):
        if "answer" in payload:
            answer = payload["answer"]
            return {"claims": [{"text": case["answer"],
                "subject":next((word.strip(".") for word in case["answer"].split() if word.startswith("Example")), case["answer"].split()[0]),
                "time_sensitive": case["expected"] != "not_checked",
                "query": case["answer"], "reason": "Synthetic fixture"}
                for case in CASES if case["answer"] in answer]}
        case = next(c for c in CASES if c["answer"] == payload["claim"])
        decisive = case["expected"] in ("outdated", "supported")
        return {"verdict": case["expected"], "reason": "Synthetic fixture assessment",
                "citation_ids": ["s1"] if decisive else [],
                "quotes": [{"source_id": "s1", "text": case["evidence"]}] if decisive else [],
                "correction": case["evidence"] if case["expected"] == "outdated" else None,
                "evidence_conflict": False}


class FixtureSearch:
    def search(self, query, **_options):
        # Neutral latest queries deliberately omit the alleged version.
        case = next((c for c in CASES if c["answer"] == query), None)
        if case is None:
            case = next(c for c in CASES if any(word.startswith("Example") and word.strip(".,") in query for word in c["answer"].split()))
        return {"usage": {"credits": 0}, "results": [{
            "title": "Synthetic example — not a real source",
            "url": "https://example.com/synthetic-evidence",
            "content": case["evidence"], "published_date": "2026-11-05"}
        ] if case["evidence"] else []}


def demo_verifier():
    return Verifier(FixtureLLM(), FixtureSearch(), mode="synthetic_fixture",
                    clock=lambda: "2026-11-05T12:00:00+00:00")
