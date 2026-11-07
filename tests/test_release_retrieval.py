import copy
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from freshnessguard.clients import TavilySearch
from freshnessguard.engine import Verifier
from freshnessguard.evidence import is_primary, policy_for, source_role, release_source_rank
from freshnessguard.semantics import latest_query, dated_release_facts, version_retrieval_claim

CHECKED = "2026-11-06T12:00:00+00:00"


class ReleaseRetrievalTests(unittest.TestCase):
    def setup_case(self, content, target="41.2", verdict="outdated", url="https://vendor.test/releases/tag/v41.3.0"):
        claim = {"text":f"The latest stable Widget release series is {target}.", "subject":"Widget",
            "time_sensitive":True,"checked_at":CHECKED,"verdict":"uncertain","sources":[{
            "id":"s1","url":url,"title":"Widget release", "content":content,"primary_source":True,
            "published_date":None,"retrieved_at":CHECKED}],"source_policy":{"entity":"Widget","domains":["vendor.test"]}}
        decision = {"verdict":verdict,"reason":"A dated stable release is newer than the alleged maximum",
            "evidence_conflict":False,"citation_ids":["s1"],"quotes":[{"source_id":"s1","text":content}],
            "correction":content if verdict == "outdated" else None}
        return claim, decision

    def test_saved_retrieval_missing_evidence_still_abstains(self):
        saved = json.loads((Path(__file__).parent / "fixtures/retrieval_abstention.json").read_text(encoding="utf-8"))
        claim = saved["claim"]
        llm = Mock(); llm.complete.side_effect = [{"claims":[{"text":claim["text"],"subject":claim["subject"],"time_sensitive":True,"query":"old query"}]},
            {"verdict":"uncertain","reason":claim["reason"],"citation_ids":[],"quotes":[],"correction":None,"evidence_conflict":False}]
        search = Mock(); search.search.return_value = {"usage":{"credits":0},"results":claim["sources"]}
        report = Verifier(llm, search, mode="saved_retrieval_replay", clock=lambda:saved["checked_at"]).verify(claim["text"])
        result = report["claims"][0]
        self.assertEqual(result["verdict"], "uncertain")
        self.assertEqual(result["proposed_verdict"], "uncertain")
        self.assertNotIn("semantic_validation", result)
        self.assertTrue(any(s["source_role"] == "aggregator" and not s["primary_source"] for s in result["sources"]))
        self.assertIn("https://www.python.org/downloads/", search.search.call_args.args[0])
        self.assertNotIn("3.11", search.search.call_args.args[0])
        self.assertEqual(search.search.call_args.kwargs["max_results"], 8)
        self.assertIn("planet.python.org", search.search.call_args.kwargs["exclude_domains"])

    def test_newer_final_release_over_30_days_old_can_refute_latest(self):
        text = "Widget 41.3.0\n\nRelease date: September 1, 2026\n\nThis is the stable release of Widget 41.3.0."
        claim, decision = self.setup_case(text)
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "outdated")
        self.assertEqual(claim["semantic_validation"]["proof_kind"], "newer_dated_stable_release")
        self.assertEqual(claim["semantic_validation"]["release_witnesses"][0]["date"], "2026-09-01")
        self.assertEqual(claim["correction"], text)

    def test_old_announcement_cannot_establish_supported_latest(self):
        text = "Widget 41.3.0\n\nRelease date: September 1, 2026\n\nThis is the stable release of Widget 41.3.0."
        claim, decision = self.setup_case(text, target="41.3", verdict="supported")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_supported_latest_blocked_by_uncited_dated_newer_release(self):
        text = "As of 2026-11-06, the latest stable Widget release series is 41.2."
        claim, decision = self.setup_case(text, verdict="supported", url="https://vendor.test/downloads")
        newer = copy.deepcopy(claim["sources"][0]); newer.update(id="s2",url="https://vendor.test/releases/tag/v41.3.0",
            content="Widget 41.3.0 was released on 2026-08-01 as a stable release.")
        claim["sources"].append(newer)
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_future_release_does_not_refute(self):
        claim, decision = self.setup_case("Widget 41.3.0 was released on 2027-01-01 as a stable release.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_preview_release_does_not_refute_stable(self):
        for suffix in ("a1", "b2", "rc1"):
            text = f"Widget 41.3.0{suffix}\n\nRelease date: 2026-09-01\n\nThis is not a stable release of Widget 41.3.0{suffix}."
            claim, decision = self.setup_case(text)
            Verifier._apply_decision(claim, decision)
            self.assertEqual(claim["verdict"], "uncertain")

    def test_same_series_patch_cannot_refute_latest_series(self):
        claim, decision = self.setup_case("Widget 41.2.9 was released on 2026-09-01 as a stable release.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_newer_patch_can_refute_exact_version(self):
        claim, decision = self.setup_case("Widget 41.2.9 was released on 2026-09-01 as a stable release.")
        claim["text"] = "The latest stable Widget version is 41.2.0."
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "outdated")

    def test_lts_scope_is_not_silently_changed(self):
        claim, decision = self.setup_case("Widget 41.3.0 was released on 2026-09-01 as a stable release.")
        claim["text"] = "The latest stable LTS Widget release series is 41.2."
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_publication_date_is_not_a_release_date(self):
        claim, decision = self.setup_case("This is the stable release of Widget 41.3.0.")
        claim["sources"][0]["published_date"] = "2026-09-01"
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_unrelated_entity_still_rejected(self):
        claim, decision = self.setup_case("OtherSDK 41.3.0 was released on 2026-09-01 as a stable release.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_unofficial_release_cannot_create_new_counterexample(self):
        claim, decision = self.setup_case("Widget 41.3.0 was released on 2026-09-01 as a stable release.", url="https://unrelated.test/releases/41")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_current_and_other_latest_wording_get_release_queries(self):
        for word in ("latest", "current", "newest", "most recent"):
            text = f"The {word} stable Python release series is 3.11."
            self.assertTrue(version_retrieval_claim(text))
            query = latest_query(text,"Python release series","bad query",CHECKED)
            self.assertIn("https://devguide.python.org/versions/", query)
            self.assertNotIn("3.11", query)
            self.assertNotIn("2026-11-06", query)

    def test_version_comparison_gets_neutral_history_not_confirmation(self):
        text = "Python 3.11 is newer than Python 3.15."
        query = latest_query(text,"Python","confirm it",CHECKED)
        self.assertIn("release history", query)
        self.assertIn("3.11 3.15", query)
        self.assertNotIn("newer than", query)

    def test_release_indexes_rank_above_snapshots_and_feeds(self):
        policy = policy_for("Python")
        urls = ["https://planet.python.org", "https://www.python.org/downloads/release/python-397", "https://www.python.org/downloads/"]
        self.assertEqual(sorted(urls, key=lambda u:release_source_rank(u, policy))[0], urls[-1])
        self.assertFalse(is_primary(urls[0], policy))
        self.assertEqual(source_role(urls[-1]), "release_index")

    def test_current_index_later_in_search_results_survives_selection_cap(self):
        llm = Mock(); llm.complete.side_effect = [{"claims":[{"text":"The latest stable Python release series is 3.11.","subject":"Python","time_sensitive":True,"query":"old"}]},
            {"verdict":"uncertain","reason":"Only testing retrieval","citation_ids":[],"quotes":[],"correction":None}]
        rows = [{"url":f"https://www.python.org/downloads/release/python-{i}","content":"Historical artifact"} for i in range(7)]
        rows.append({"url":"https://www.python.org/downloads/","content":"Current release index"})
        search = Mock(); search.search.return_value = {"results":rows,"usage":{"credits":0}}
        report = Verifier(llm, search, clock=lambda:CHECKED).verify("The latest stable Python release series is 3.11.")
        self.assertEqual(report["claims"][0]["sources"][0]["url"], "https://www.python.org/downloads/")
        self.assertEqual(len(report["claims"][0]["sources"]), 4)
        self.assertEqual(report["metrics"]["search_calls"], 1)

    def test_search_wire_bounds_and_exclusions(self):
        with patch.dict("os.environ", {"TAVILY_API_KEY":"test-only"}), patch("freshnessguard.clients.post_json") as post:
            TavilySearch().search("query", include_domains=["python.org"],exclude_domains=["planet.python.org"], max_results=100)
        body = post.call_args.args[1]
        self.assertEqual(body["max_results"], 8)
        self.assertEqual(body["exclude_domains"], ["planet.python.org"])

    def test_entity_cooccurrence_is_not_a_release_relation(self):
        claim, decision = self.setup_case("Widget interoperates with OtherSDK 41.3.0. Release date: 2026-09-01. This is a stable release.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_official_withdrawal_blocks_release_counterexample(self):
        claim, decision = self.setup_case("Widget 41.3.0 was released on 2026-09-01 as a stable release.")
        withdrawal = copy.deepcopy(claim["sources"][0])
        withdrawal.update(id="s2",url="https://vendor.test/status",content="As of 2026-11-01, Widget 41.3.0 is withdrawn.")
        claim["sources"].append(withdrawal)
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")

    def test_as_of_fact_is_not_labelled_a_release_date(self):
        claim, decision = self.setup_case("As of 2026-09-01, the latest stable Widget release series is 41.3.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "outdated")
        self.assertEqual(claim["semantic_validation"]["release_witnesses"][0]["date_kind"], "as_of")

    def test_full_pipeline_with_dated_official_release_detects_stale(self):
        text = "Widget 41.3.0\n\nRelease date: September 1, 2026\n\nThis is the stable release of Widget 41.3.0."
        claim, decision = self.setup_case(text)
        llm = Mock(); llm.complete.side_effect = [{"claims":[{"text":claim["text"],"subject":"Widget","time_sensitive":True,"query":"lookup"}]},decision]
        search = Mock(); search.search.return_value = {"usage":{"credits":0},"results":claim["sources"]}
        # Synthetic operator policy for a fictional product; no real release or
        # official endpoint is invented or requested by this regression.
        with patch("freshnessguard.engine.policy_for", return_value=claim["source_policy"]):
            report = Verifier(llm, search, mode="synthetic_release_proof", clock=lambda:CHECKED).verify(claim["text"])
        self.assertEqual(report["claims"][0]["verdict"], "outdated")
        self.assertEqual(report["freshness_score"], 0)
        self.assertEqual(report["coverage"], 1)
        self.assertEqual(report["metrics"]["search_calls"], 1)
        self.assertEqual(report["metrics"]["llm_calls"], 2)
        self.assertEqual(report["claims"][0]["correction"], text)

    def test_negated_release_date_is_not_a_release_witness(self):
        claim, decision = self.setup_case("Widget 41.3.0 has not been released on 2026-09-01 as a stable release.")
        Verifier._apply_decision(claim, decision)
        self.assertEqual(claim["verdict"], "uncertain")
