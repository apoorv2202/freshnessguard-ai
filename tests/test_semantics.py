import copy
import json
import unittest
from pathlib import Path
from unittest.mock import Mock

from benchmarks.live import evaluate, summarize
from freshnessguard.engine import Verifier
from freshnessguard.evidence import canonical_source, is_primary, policy_for, source_role
from freshnessguard.semantics import latest_query

CHECKED = "2026-11-06T12:00:00+00:00"


class SemanticTests(unittest.TestCase):
    def make_case(self, content, target="41.2", verdict="supported", url="https://vendor.test/downloads"):
        claim = {"text":f"The latest stable release series of Widget is {target}.",
                 "subject":"Widget", "time_sensitive":True, "checked_at":CHECKED,
                 "source_policy":{"entity":"Widget", "domains":["vendor.test"]},
                 "verdict":"uncertain", "correction":None,"citation_ids":[],"quotes":[],
                 "sources":[{"id":"s1","url":url,"title":"Widget release information", "content":content,
                             "published_date":"2026-11-06", "retrieved_at":CHECKED,"primary_source":True}]}
        decision = {"verdict":verdict,"reason":"A proposed model assessment", "citation_ids":["s1"],
                    "quotes":[{"source_id":"s1","text":content}],"evidence_conflict":False,
                    "correction":content if verdict == "outdated" else None}
        return claim, decision

    def test_exact_saved_false_fresh_becomes_uncertain(self):
        fixture = json.loads((Path(__file__).parent / "fixtures/stale_latest_python.json").read_text(encoding="utf-8"))
        claim = copy.deepcopy(fixture["claim"])
        claim["checked_at"] = fixture["checked_at"]
        Verifier._apply_decision(claim, fixture["reconstructed_decision"])
        self.assertEqual(claim["proposed_verdict"], "supported")
        self.assertEqual(claim["proposed_assessment"]["reason"], "Model proposal before final evidence validation.")
        self.assertEqual(claim["verdict"], "uncertain")
        self.assertEqual(claim["semantic_validation"]["status"], "rejected")
        self.assertIsNone(claim["correction"])

    def test_full_pipeline_saved_evidence_needs_no_paid_calls(self):
        fixture = json.loads((Path(__file__).parent / "fixtures/stale_latest_python.json").read_text(encoding="utf-8"))
        source = fixture["claim"]
        llm = Mock()
        llm.complete.side_effect = [{"claims":[{"text":source["text"],"subject":source["subject"],
            "time_sensitive":True,"query":"Python 3.11 latest stable"}]}, fixture["reconstructed_decision"]]
        search = Mock()
        search.search.return_value = {"usage":{"credits":0},"results":source["sources"]}
        report = Verifier(llm, search, mode="saved_evidence_replay", clock=lambda:fixture["checked_at"]).verify(source["text"])
        self.assertEqual(report["claims"][0]["verdict"], "uncertain")
        self.assertIsNone(report["freshness_score"])
        self.assertEqual(report["coverage"], 0)
        self.assertEqual(report["metrics"]["llm_calls"], 2)
        self.assertEqual(report["metrics"]["search_calls"], 1)
        self.assertEqual(len(report["claims"][0]["sources"]), 2)
        self.assertTrue(any(not s["primary_source"] and s["source_role"] == "community" for s in report["claims"][0]["sources"]))
        self.assertNotIn("3.11", search.search.call_args.args[0])
        case = {"answer":source["text"],"expected":"outdated"}
        summary = summarize([{"report":report,"evaluation":evaluate(case,report)}], {"as_of":"2026-11-06"}, "saved evidence")
        self.assertEqual(summary["false_fresh_count"], 0)
        # Abstention is safer, but remains a missed stale detection, not a win.
        self.assertEqual(summary["false_negative_stale"], 1)

    def test_still_supported_does_not_entail_latest(self):
        claim, decision = self.make_case("As of 2026-11-06, Widget 41.2 is stable and supported until 2029.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_old_latest_statement_not_current_even_with_fresh_metadata(self):
        claim, decision = self.make_case("As of 2023-03-07, the latest stable Widget release series is 41.2.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_undated_latest_quote_not_rescued_by_publication_or_retrieval(self):
        claim, decision = self.make_case("The latest stable release series of Widget is 41.2.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_current_same_entity_scope_and_channel_can_be_supported(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable release series of Widget is 41.2.")
        decision["reason"] = decision["quotes"][0]["text"]
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "supported")
        self.assertEqual(claim["reason"], "The verifier accepted the cited evidence for this claim.")
        self.assertEqual(claim["quotes"], decision["quotes"])

    def test_current_newer_version_can_ground_outdated(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable release series of Widget is 41.3.", verdict="outdated")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "outdated")
        self.assertIn(claim["correction"], claim["sources"][0]["content"])

    def test_uncited_newer_current_evidence_blocks_supported(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable release series of Widget is 41.2.")
        newer = copy.deepcopy(claim["sources"][0])
        newer.update(id="s2",url="https://vendor.test/versions",content="As of 2026-11-06, the latest stable release series of Widget is 41.3.")
        claim["sources"].append(newer)
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")
        self.assertIn("41.3", claim["semantic_validation"]["observed_versions"])

    def test_historical_snapshot_cannot_establish_current_latest(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable release series of Widget is 41.2.", url="https://vendor.test/releases/tag/v1.0")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_latest_patch_within_old_branch_not_latest_global_series(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable maintenance release of Widget is 41.2.9.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_latest_lts_not_latest_stable_overall(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable LTS release series of Widget is 41.2.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_prerelease_does_not_establish_latest_stable(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable release of Widget is 41.2rc1.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_future_effective_date_rejected_without_metadata_flag(self):
        claim, decision = self.make_case("As of 2027-01-01, the latest stable release series of Widget is 41.2.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_unrelated_entity_quote_does_not_entail_claim(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable release series of OtherSDK is 41.2.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_negated_latest_statement_is_not_support(self):
        claim, decision = self.make_case("As of 2026-11-06, Widget 41.2 is not the latest stable release series.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_version_comparison_is_numeric_not_lexical(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable release series of Widget is 9.10.", target="9.9", verdict="outdated")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "outdated")

    def test_forum_hosting_is_not_primary_authorship(self):
        self.assertFalse(is_primary("https://discuss.python.org/t/release/123", policy_for("Python")))
        self.assertEqual(source_role("https://python.org/downloads/release/python-390"), "version_snapshot")

    def test_www_alias_does_not_count_as_independent_evidence(self):
        self.assertEqual(canonical_source("https://www.python.org/downloads/release/python-390/"), canonical_source("https://python.org/downloads/release/python-390"))

    def test_query_does_not_anchor_on_alleged_version(self):
        query = latest_query("Widget 41.2 is the latest stable version.","Widget","confirm Widget 41.2",CHECKED)
        self.assertNotIn("41.2", query)
        self.assertNotIn("2026-11-06", query)

    def test_question_about_latest_is_not_an_assertion(self):
        claim, decision = self.make_case("As of 2026-11-06, is Widget 41.2 the latest stable release series?")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_speculative_latest_is_not_support(self):
        claim, decision = self.make_case("As of 2026-11-06, Widget 41.2 might be the latest stable release series.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_patch_version_wording_cannot_prove_global_latest(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable patch version of Widget is 41.2.9.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_newer_prerelease_does_not_contradict_stable_claim(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable release series of Widget is 41.2.")
        newer = copy.deepcopy(claim["sources"][0])
        newer.update(id="s2",url="https://vendor.test/preview",content="As of 2026-11-06, the latest preview release of Widget is 42.0.")
        claim["sources"].append(newer)
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "supported")

    def test_subject_containing_claimed_version_does_not_hide_newer_evidence(self):
        claim, decision = self.make_case("As of 2026-11-06, the latest stable release series of Widget is 41.3.", verdict="outdated")
        claim.update(text="Widget 41.2 is the latest stable release series.", subject="Widget 41.2")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "outdated")
