import unittest
from unittest.mock import Mock

from benchmarks.final_offline import CHECKED, CURRENT, JAVA_URL, PYTHON, STABLE, cases, evaluate, proposal, row
from freshnessguard.engine import Verifier
from freshnessguard.evidence import is_primary, policy_for


class ReliabilityHardeningTests(unittest.TestCase):
    def test_offline_benchmark(self):
        for case in cases():
            with self.subTest(case=case[0]):
                result = evaluate(case)
                self.assertTrue(result["pass"], result)

    def test_reused_evidence_retains_provenance_and_independent_judgment(self):
        llm, search, retriever = Mock(), Mock(), Mock()
        texts = [CURRENT, PYTHON]
        extraction = {"claims": [
            {"text": text, "subject": "Python", "query": "release", "time_sensitive": True}
            for text in texts
        ]}
        llm.complete.side_effect = [extraction,
            {"verdict": "uncertain", "reason": "Insufficient current evidence"},
            {"verdict": "outdated", "reason": "Select the backend passage", "evidence_conflict": False,
             "use_candidate_release_quote": True, "citation_ids": [], "quotes": [], "correction": None},
        ] * 2
        search.search.return_value = {"results": [row("Python release information.")], "usage": {"credits": 1}}
        retriever.retrieve.side_effect = lambda url, _: {"url": url, "content": STABLE}
        timestamps = [CHECKED, "2026-11-09T10:00:01+00:00", "2026-11-09T10:00:02+00:00",
                      "2026-11-09T10:01:00+00:00", "2026-11-09T10:01:01+00:00", "2026-11-09T10:01:02+00:00"]
        verifier = Verifier(llm, search, retriever=retriever, clock=iter(timestamps).__next__, reuse_evidence=True)
        for offset in (0, 3):
            report = verifier.verify(" ".join(texts))
            first, second = report["claims"]
            self.assertEqual([first["verdict"], second["verdict"]], ["uncertain", "outdated"])
            self.assertEqual((report["coverage"], report["freshness_score"]), (0.5, 0))
            self.assertFalse(first["retrieval"]["search_reused"])
            self.assertFalse(first["source_retrieval"]["reused"])
            self.assertTrue(second["retrieval"]["search_reused"])
            self.assertTrue(second["source_retrieval"]["reused"])
            self.assertEqual(second["retrieval"]["search_obtained_at"], timestamps[offset + 1])
            self.assertEqual(second["source_retrieval"]["obtained_at"], timestamps[offset + 2])
            self.assertEqual([s["retrieved_at"] for s in second["sources"]], timestamps[offset + 1:offset + 3])
            self.assertEqual(second["quotes"], [{"source_id": "s2", "text": STABLE}])
            self.assertEqual(report["metrics"]["search_calls"], 1)
            self.assertEqual(report["metrics"]["source_retrieval_calls"], 1)
            self.assertEqual(report["metrics"]["tavily_credits"], 1)
        self.assertEqual((search.search.call_count, retriever.retrieve.call_count, llm.complete.call_count), (2, 2, 6))

    def test_quote_reference_cannot_override_fabricated_model_quote(self):
        case = ("fabricated-mixed-reference", [PYTHON], [[row(STABLE)]],
                [proposal(STABLE + " It is the latest.", use_candidate_release_quote=True)],
                ["uncertain"], {"llm_calls": 2})
        self.assertTrue(evaluate(case)["pass"])

    def test_java_lts_plan_does_not_prove_lts_status(self):
        claim = "Java 25 is a long-term support release of Java."
        plan = "Oracle will provide long-term support for Java 25 for at least eight years."
        case = ("java-lts-plan", [claim], [[row(plan, JAVA_URL)]],
                [proposal(plan, "supported")], ["uncertain"], {"llm_calls": 2})
        self.assertTrue(evaluate(case)["pass"])
        self.assertFalse(is_primary("https://www.oracle.com/other", policy_for(claim)))
        self.assertIsNone(policy_for("JavaScript runtime")["entity"])
