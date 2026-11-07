import copy
import unittest
from unittest.mock import Mock, patch

from freshnessguard.clients import structured_json, ServiceError
from freshnessguard.engine import Verifier
from freshnessguard.evidence import policy_for, is_primary, publication_date
from freshnessguard.fixtures import demo_verifier, CASES


class ReliabilityTests(unittest.TestCase):
    def decision(self, **changes):
        quote = "As of 2026-11-05, the latest stable Python release series is 3.15."
        claim = {"text":"The latest stable Python release series is 3.11.", "verdict":"uncertain",
                 "checked_at":"2026-11-06T12:00:00+00:00",
                 "source_policy":policy_for("Python"), "sources":[{"id":"s1", "content":quote,
                 "url":"https://www.python.org/downloads/", "primary_source":True, "future_dated":False}]}
        decision = {"verdict":"outdated", "reason":"Newer stable release", "citation_ids":["s1"],
                    "quotes":[{"source_id":"s1", "text":quote}], "correction":quote, "evidence_conflict":False}
        decision.update(changes)
        return claim, decision

    def test_extractively_grounded_correction(self):
        claim, decision = self.decision()
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "outdated")

    def test_unsupported_correction_rejected(self):
        claim, decision = self.decision(correction="Python 3.16 is stable now.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")
        self.assertIn("Correction", claim["validation_error"])

    def test_unresolved_conflict_abstains(self):
        for value in [True, None, "false", 0]:
            claim, decision = self.decision(evidence_conflict=value)
            Verifier._apply_decision(claim, decision)
            self.assertEqual(claim["verdict"], "uncertain")

    def test_secondary_only_cannot_decide_known_entity(self):
        claim, decision = self.decision()
        claim["sources"][0]["primary_source"] = False
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_future_evidence_cannot_decide(self):
        claim, decision = self.decision()
        claim["sources"][0]["future_dated"] = True
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_domain_boundary_and_github_owner(self):
        policy = policy_for("Python")
        self.assertTrue(is_primary("https://docs.python.org/3/", policy))
        for url in ["https://python.org.evil.test", "https://evilpython.org", "https://user@python.org", "http://python.org"]:
            self.assertFalse(is_primary(url, policy))
        self.assertFalse(is_primary("https://github.com/random/bifrost", policy_for("Bifrost")))
        self.assertTrue(is_primary("https://github.com/maximhq/bifrost/blob/dev/core/go.mod", policy_for("Bifrost")))

    def test_dates_are_not_retrieval_dates(self):
        self.assertIsNone(publication_date(None))
        self.assertIsNone(publication_date("not-a-date"))
        self.assertEqual(publication_date("2026-11-05").year, 2026)
        self.assertEqual(publication_date("Thu, 05 Nov 2026 10:00:00 GMT").day, 5)

    def test_structured_output_accepts_one_fence(self):
        self.assertEqual(structured_json('```json\n{"claims": []}\n```'), {"claims":[]})

    def test_structured_output_rejects_duplicate_keys_and_prose(self):
        for raw in ['{"verdict":"uncertain","verdict":"supported"}', '[]', '{"x":NaN}', '{"x":1e309}', 'Here is JSON: {}', '```json\n{}\n``` trailing']:
            with self.assertRaises(ServiceError):
                structured_json(raw)

    def test_hallucinated_citation_rejected(self):
        claim, decision = self.decision(citation_ids=["invented-source"])
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_whitespace_quote_resolves_to_original_span(self):
        claim, decision = self.decision()
        claim["sources"][0]["content"] = claim["sources"][0]["content"].replace("latest stable", "latest\n  stable")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "outdated")
        self.assertIn(claim["quotes"][0]["text"], claim["sources"][0]["content"])
        self.assertIn(claim["correction"], claim["quotes"][0]["text"])

    def test_multi_claim_benchmark_counts_missing_claims(self):
        from benchmarks.live import evaluate
        case = {"answer":"one. two.", "expected_claims":[{"text":"one", "verdict":"outdated"}, {"text":"two", "verdict":"supported"}]}
        result = evaluate(case, {"claims":[{"text":"one", "verdict":"outdated"}]})
        self.assertFalse(result["pass"])
        self.assertEqual(result["claims"][1]["actual"], "missing")
        from benchmarks.live import summarize
        report = demo_verifier().verify(CASES[0]["answer"])
        extra = copy.deepcopy(report["claims"][0])
        extra.update(text="An unmatched factual assertion.", verdict="supported")
        report["claims"].append(extra)
        case = {"answer":CASES[0]["answer"], "expected":"outdated"}
        row = {"report":report, "evaluation":evaluate(case, report)}
        summary = summarize([row], {"as_of":"2026-11-05"}, "test")
        self.assertEqual(summary["false_fresh_count"], 1)
        self.assertEqual(summary["extraction_precision"], 0.5)

    def test_fragment_cannot_become_grounded_claim(self):
        llm = Mock()
        llm.complete.return_value = {"claims":[{"text":"The latest stable", "subject":"The", "time_sensitive":True, "query":"latest stable"}]}
        search = Mock()
        report = Verifier(llm, search).verify("The latest stable")
        self.assertEqual(report["status"], "unavailable")
        self.assertIsNone(report["freshness_score"])
        search.search.assert_not_called()

    def test_truncated_provider_answer_skips_all_verification(self):
        from freshnessguard.engine import annotate_completion
        verifier = Mock(); verifier.mode = "live"
        result = annotate_completion({"choices":[{"index":0,"finish_reason":"length","message":{"content":"The latest stable"}}]}, verifier)
        self.assertEqual(result["freshnessguard"]["reports"][0]["report"]["status"], "incomplete")
        verifier.verify.assert_not_called()

    def test_report_escapes_original_answer(self):
        from freshnessguard.reporting import render_report
        report = demo_verifier().verify(CASES[0]["answer"])
        report["original_answer"] = '<script>alert("secret")</script>'
        page = render_report(report)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_unsafe_report_source_is_not_clickable(self):
        from freshnessguard.reporting import render_report
        report = demo_verifier().verify(CASES[0]["answer"])
        report["claims"][0]["sources"][0]["url"] = "javascript:alert(1)"
        self.assertNotIn('href="javascript:', render_report(report))

    def test_input_url_does_not_become_verification_source(self):
        report = demo_verifier().verify(CASES[0]["answer"] + " Python source: https://example.com/release")
        self.assertEqual(report["input_citations"][0]["assessment"], "not_official_for_detected_entity")
        self.assertEqual(report["claims"][0]["sources"][0]["url"], "https://example.com/synthetic-evidence")

    def test_model_failure_does_not_erase_known_tavily_usage(self):
        verifier = demo_verifier()
        original = verifier.llm.complete
        def complete(system, payload):
            if "claim" in payload:
                raise ServiceError("Upstream HTTP 503")
            return original(system, payload)
        verifier.llm.complete = complete
        report = verifier.verify(CASES[0]["answer"])
        self.assertTrue(report["metrics"]["credit_usage_complete"])
        self.assertEqual(report["claims"][0]["reason"], "Upstream HTTP 503")
