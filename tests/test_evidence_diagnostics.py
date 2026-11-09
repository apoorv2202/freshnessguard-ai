"""Offline replay of the actual release-index live failure; no API calls."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

from freshnessguard.engine import Verifier


class EvidenceDiagnosticsTests(unittest.TestCase):
    def saved(self):
        return json.loads((Path(__file__).parent / "fixtures/release_index_live_evidence.json").read_text(encoding="utf-8"))

    def replay(self):
        saved = self.saved()
        claim = copy.deepcopy(saved["claim"])
        claim["checked_at"] = saved["checked_at"]
        Verifier._apply_decision(claim, saved["decision"])
        return claim

    def test_saved_model_outdated_is_safely_rejected_with_quote_reasons(self):
        claim = self.replay()
        self.assertEqual(claim["proposed_verdict"], "outdated")
        self.assertEqual(claim["verdict"], "uncertain")
        self.assertEqual(claim["citation_ids"], [])
        self.assertIsNone(claim["correction"])
        audit = claim["semantic_validation"]
        self.assertEqual(audit["release_witnesses"], [])
        self.assertEqual(audit["observed_release_witnesses"], [])
        quotes = {r["source_id"]:r for r in audit["release_evidence_checks"] if r["scope"] == "quote"}
        self.assertEqual(quotes["s1"]["rejected_passage_counts"], {"explicit_release_or_effective_date_missing":1})
        self.assertEqual(quotes["s4"]["rejected_passage_counts"], {"explicit_stable_or_final_channel_missing":1})
        sources = {r["source_id"]:r for r in audit["release_evidence_checks"] if r["scope"] == "source"}
        self.assertEqual(sources["s2"]["examined_passages"], 0)
        self.assertEqual(sources["s2"]["rejected_passage_counts"], {"no_passage_within_800_character_bound":1})
        self.assertTrue(all(r["parsed_facts"] == 0 for r in sources.values()))

    def test_publication_metadata_cannot_repair_saved_missing_release_date(self):
        saved = self.saved()
        claim = copy.deepcopy(saved["claim"])
        claim["checked_at"] = saved["checked_at"]
        for source in claim["sources"]:
            source["published_date"] = "2026-11-06"
        Verifier._apply_decision(claim, saved["decision"])
        self.assertEqual(claim["verdict"], "uncertain")

    def test_saved_source_text_reaches_judge_exactly_and_retains_report_provenance(self):
        saved = self.saved()
        original = saved["claim"]
        llm = Mock()
        llm.complete.side_effect = [{"claims":[{"text":original["text"], "subject":original["subject"],
            "time_sensitive":True, "query":"lookup"}]}, saved["decision"]]
        search = Mock()
        search.search.return_value = {"results":original["sources"], "usage":{"credits":0}}
        report = Verifier(llm, search, mode="offline", clock=lambda:saved["checked_at"]).verify(original["text"])
        result = report["claims"][0]
        self.assertEqual(result["verdict"], "uncertain")
        payload = llm.complete.call_args_list[1].args[1]
        self.assertEqual(payload["sources"], [{k:v for k,v in source.items() if k != "retrieved_at"}
                                              for source in result["sources"]])
        self.assertTrue(all(source["retrieved_at"] == payload["checked_at"] for source in result["sources"]))
        self.assertEqual([s["content"] for s in payload["sources"]], [s["content"] for s in original["sources"]])
        self.assertEqual(report["metrics"]["search_calls"], 1)
        self.assertEqual(report["metrics"]["llm_calls"], 2)

    def test_candidate_trace_records_cap_dedup_invalid_and_truncation_without_secrets(self):
        answer = "The latest stable Python release series is 3.11."
        llm = Mock()
        llm.complete.side_effect = [{"claims":[{"text":answer,"subject":"Python","time_sensitive":True,"query":"lookup"}]},
            {"verdict":"uncertain","reason":"No sufficient evidence","citation_ids":[],"quotes":[]}]
        secret = "sensitive-test-marker"
        rows = [{"url":f"https://www.python.org/downloads/release/python-{i}?token={secret}",
                 "title":secret,"content":secret * 300,"published_date":None} for i in range(5)]
        rows.extend([copy.deepcopy(rows[0]), {"url":f"https://user:{secret}@vendor.test/", "content":secret}, None])
        search = Mock()
        search.search.return_value = {"results":rows,"usage":{"credits":0},"private_upstream_field":secret}
        report = Verifier(llm, search, clock=lambda:"2026-11-06T12:00:00+00:00").verify(answer)
        claim = report["claims"][0]
        trace = claim["retrieval"]["candidates"]
        self.assertEqual([r["selection"] for r in trace], ["selected"]*4 + ["selection_cap","duplicate_url","invalid_url_or_content","invalid_result"])
        self.assertEqual(trace[0]["url_sha256"], hashlib.sha256(rows[0]["url"].encode()).hexdigest())
        self.assertTrue(trace[0]["verifier_truncated"])
        self.assertEqual(trace[0]["source_id"], "s1")
        self.assertNotIn(secret, json.dumps(claim["retrieval"]))
        self.assertEqual(len(claim["sources"]), 4)
        self.assertEqual(len(claim["sources"][0]["content"]), 5000)
        self.assertEqual(llm.complete.call_count, 2)

    def test_source_diagnostic_counts_are_bounded_and_do_not_copy_text(self):
        claim = self.replay()
        checks = claim["semantic_validation"]["release_evidence_checks"]
        for check in checks:
            self.assertLessEqual(check["examined_passages"], 100)
            self.assertNotIn("text", check)
            self.assertNotIn("content", check)
            # Each rejected passage reports the first failing predicate, not
            # independent evidence votes or an exhaustive semantic analysis.
            self.assertEqual(sum(check.get("rejected_passage_counts", {}).values()) + check["accepted_passages"],
                             check["examined_passages"] or 1)
