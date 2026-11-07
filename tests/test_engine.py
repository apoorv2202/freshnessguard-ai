import copy
import unittest
from unittest.mock import Mock

from freshnessguard.clients import ServiceError
from freshnessguard.engine import Verifier, annotate_completion
from freshnessguard.fixtures import ANSWER, CASES, demo_verifier


class EngineTests(unittest.TestCase):
    def test_mixed_report_and_score_denominator(self):
        report = demo_verifier().verify(ANSWER)
        self.assertEqual([c["verdict"] for c in report["claims"]], ["outdated", "supported", "not_checked"])
        self.assertEqual(report["freshness_score"], 50)
        self.assertEqual(report["coverage"], 1)
        self.assertEqual(report["metrics"]["search_calls"], 2)
        self.assertEqual(report["mode"], "synthetic_fixture")

    def test_uncertain_is_not_scored_as_fresh(self):
        report = demo_verifier().verify(CASES[2]["answer"])
        self.assertIsNone(report["freshness_score"])
        self.assertEqual(report["coverage"], 0)
        self.assertEqual(report["status"], "review_required")

    def test_budget_preserves_unchecked_claim(self):
        verifier = demo_verifier(); verifier.max_claims = 1
        report = verifier.verify(ANSWER)
        self.assertEqual(report["metrics"]["search_calls"], 1)
        self.assertEqual(report["claims"][1]["verdict"], "uncertain")
        self.assertEqual(report["coverage"], 0.5)

    def test_search_failure_abstains(self):
        verifier = demo_verifier()
        verifier.search.search = Mock(side_effect=ServiceError("Upstream HTTP 429"))
        report = verifier.verify(CASES[0]["answer"])
        self.assertEqual(report["claims"][0]["verdict"], "uncertain")
        self.assertFalse(report["metrics"]["credit_usage_complete"])

    def test_malformed_extraction_is_incomplete(self):
        for output in [None, {"claims": []}, {"claims": [{"text": "invented", "time_sensitive": True}]}]:
            llm = Mock(); llm.complete.return_value = output
            report = Verifier(llm, Mock()).verify("The latest version is 3.0.")
            if output != {"claims": []}:
                self.assertEqual(report["status"], "unavailable")
            self.assertIsNone(report["freshness_score"])

    def test_bad_citations_and_quotes_are_rejected(self):
        report = demo_verifier().verify(CASES[0]["answer"])
        template = report["claims"][0]
        for ids, quotes in [(["invented"], []), (["s1"], [{"source_id":"s1", "text":"fabricated quotation"}]),
                            (["s1"], []), (None, []), ([{}], [])]:
            claim = copy.deepcopy(template); claim["verdict"] = "uncertain"
            Verifier._apply_decision(claim, {"verdict":"outdated", "reason":"Changed", "citation_ids":ids,
                                           "quotes":quotes, "correction":"New version"})
            self.assertEqual(claim["verdict"], "uncertain")

    def test_no_search_for_timeless(self):
        verifier = demo_verifier(); verifier.search = Mock()
        verifier.verify(CASES[4]["answer"])
        verifier.search.search.assert_not_called()

    def test_completion_preserves_fields_and_input(self):
        completion = {"id":"abc", "choices":[{"index":0,"message":{"role":"assistant","content":ANSWER,
                       "tool_calls":[{"id":"tool1"}]}}], "usage":{"total_tokens":100}}
        original = copy.deepcopy(completion)
        result = annotate_completion(completion, demo_verifier())
        self.assertEqual(completion, original)
        self.assertEqual(result["choices"], original["choices"])
        self.assertEqual(result["usage"], original["usage"])
        self.assertEqual(len(result["freshnessguard"]["reports"]), 1)

    def test_tool_only_completion_is_explicit(self):
        result = annotate_completion({"choices":[{"message":{"content":None,"tool_calls":[]}}]}, demo_verifier())
        self.assertEqual(result["freshnessguard"]["status"], "no_text_to_check")

    def test_input_limits(self):
        for answer in [None, "", " " * 5, "a" * 16001, []]:
            with self.assertRaises(ValueError):
                demo_verifier().verify(answer)

    def test_unsafe_source_url_removed(self):
        verifier = demo_verifier()
        verifier.search.search = Mock(return_value={"results":[{"url":"javascript:alert(1)", "content":"irrelevant"}]})
        report = verifier.verify(CASES[0]["answer"])
        self.assertEqual(report["claims"][0]["sources"], [])
        self.assertEqual(report["claims"][0]["verdict"], "uncertain")


if __name__ == "__main__":
    unittest.main()
