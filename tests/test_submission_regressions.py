"""Offline reproductions of the ten submission smoke outcomes."""
import io
import json
import unittest
from datetime import datetime, timedelta
from email.utils import format_datetime
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from freshnessguard.clients import BifrostLLM, ServiceError, retry_after_seconds
from freshnessguard.engine import Verifier
from freshnessguard.evidence import is_primary, policy_for


CHECKED = "2026-11-08T16:00:00+00:00"


def extracted(text, subject, sensitive=True):
    return {"text":text, "subject":subject, "time_sensitive":sensitive, "query":"official release evidence"}


class SubmissionRegressions(unittest.TestCase):
    def replay(self, answer, claims, *, search=None):
        llm = Mock()
        llm.complete.return_value = {"claims":claims}
        search = search if search is not None else Mock()
        report = Verifier(llm, search, clock=lambda:CHECKED).verify(answer)
        self.assertEqual(report["original_answer"], answer)
        return report, llm, search

    def test_judgment_timeout_still_fails_closed(self):
        answer = "The latest stable Python release series is 3.11."
        llm, search = Mock(), Mock()
        llm.complete.side_effect = [{"claims":[extracted(answer, "Python")]},
                                    ServiceError("Upstream unavailable", code="timeout")]
        search.search.return_value = {"results":[{"url":"https://www.python.org/downloads/", "content":"Python releases"}]}
        report = Verifier(llm, search, clock=lambda:CHECKED).verify(answer)
        self.assertEqual((report["status"], report["claims"][0]["verdict"]), ("unavailable", "uncertain"))
        self.assertEqual(report["errors"][0]["code"], "timeout")
        self.assertEqual(report["claims"][0]["citation_ids"], [])
        self.assertIsNone(report["freshness_score"])
        self.assertEqual(llm.complete.call_count, 2)

    def test_recorded_joined_predicate_and_pronoun_paraphrases_fail_closed(self):
        for first, rest, subject, rewrite in (
            ("Python 2.7 is the latest stable Python release",
             " and is recommended for all new Python projects.", "Python 2.7",
             "Python 2.7 is recommended for all new Python projects"),
            ("Python 3.11 is the latest stable Python release series.",
             " It is the newest version recommended for production use.", "Python 3.11",
             "Python 3.11 is the newest version recommended for production use."),
        ):
            with self.subTest(subject=subject):
                answer = first + rest
                report, llm, search = self.replay(answer, [extracted(first, subject), extracted(rewrite, subject)])
                self.assertEqual(report["status"], "unavailable")
                self.assertEqual(report["extraction"]["error"]["code"], "invalid_extraction")
                self.assertEqual(report["claims"], [])
                llm.complete.assert_called_once()
                search.search.assert_not_called()

    def test_dated_release_overlaps_merge_but_current_assertion_stays(self):
        stem = "Python 3.14.0 was released on October 7, 2025"
        full = stem + ", as a stable version of Python."
        current = "Python 3.14.0 is the latest stable Python release."
        answer = full + " " + current
        for event_spans in ([extracted(stem, "Python 3.14.0", False), extracted(full, "Python 3.14.0")],
                            [extracted(full, "Python 3.14.0"), extracted(stem, "Python 3.14.0", False)]):
            search = Mock()
            search.search.return_value = {"results":[], "usage":{"credits":0}}
            report, _, _ = self.replay(answer, [*event_spans, extracted(current, "Python 3.14.0")], search=search)
            self.assertEqual([(c["text"],c["verdict"]) for c in report["claims"]],
                             [(full, "not_checked"), (current, "uncertain")])
            search.search.assert_called_once()

    def test_lossless_outer_padding_repair_and_period_dedup(self):
        answer = "Python is maintained."
        search = Mock()
        search.search.return_value = {"results":[], "usage":{"credits":0}}
        report, _, _ = self.replay(answer, [extracted(" " + answer + " ", "Python", False),
                                           extracted(answer.removesuffix("."), "Python")], search=search)
        self.assertEqual(len(report["claims"]), 1)
        self.assertIn(report["claims"][0]["text"], answer)
        search.search.assert_called_once()

    def test_recorded_gpt_and_iphone_retail_citations_do_not_prove_release_claims(self):
        cases = (
            ("GPT-3.5 is the newest AI model available from OpenAI.", "GPT-3.5",
             "https://www.clone-systems.com/", "https://openai.com/",
             "GPT-6.1 Terra is OpenAI's new flagship in the GPT-6 family, released on October 26, 2026"),
            ("The iPhone 15 is Apple's newest iPhone model.", "iPhone 15",
             "https://www.laptopoutlet.co.uk/", "https://www.apple.com/",
             "Apple officially announced the iPhone 18 Pro Max on 9th September 2026, alongside the iPhone 18 Pro."),
        )
        for answer, subject, third_party, official, quote in cases:
            policy = policy_for(answer)
            self.assertTrue(is_primary(official, policy))
            self.assertFalse(is_primary(third_party, policy))
            for url, error in ((third_party, "recognized official source"), (official, "outside the deterministic")):
                with self.subTest(url=url):
                    claim = {"text":answer, "subject":subject, "source_policy":policy,
                             "sources":[{"id":"s1", "url":url, "content":quote, "primary_source":True}]}
                    decision = {"verdict":"outdated", "reason":"Proposed newer release", "evidence_conflict":False,
                                "citation_ids":["s1"], "quotes":[{"source_id":"s1", "text":quote}], "correction":quote}
                    Verifier._apply_decision(claim, decision)
                    self.assertEqual(claim["verdict"], "uncertain")
                    self.assertIn(error, claim["validation_error"])
                    self.assertIsNone(claim["correction"])

    def test_historical_iphone_stays_not_checked(self):
        answer = "Apple introduced the first iPhone on January 9, 2007."
        report, _, search = self.replay(answer, [extracted(answer, "Apple", False)])
        self.assertEqual(report["claims"][0]["verdict"], "not_checked")
        self.assertIsNone(report["freshness_score"])
        search.search.assert_not_called()

    def test_recorded_extraction_429_cases_preserve_status_and_retry_after(self):
        for answer in (
            "Python was created by Guido van Rossum. Python 3.11 is the latest stable Python release series.",
            "React 16 is the latest stable major version of React.",
            "By December 2027, Python 4.0 will replace Python 3 as the recommended version for production systems.",
        ):
            with self.subTest(answer=answer):
                upstream = HTTPError("https://example.invalid", 429, "test-only", {"Retry-After":"60"}, io.BytesIO(b"private"))
                search = Mock()
                with patch.dict("os.environ", {"BIFROST_MODEL":"gemini/fixture"}, clear=True), \
                     patch("freshnessguard.clients.urlopen", side_effect=upstream) as call:
                    report = Verifier(BifrostLLM(), search, clock=lambda:CHECKED).verify(answer)
                self.assertEqual(report["original_answer"], answer)
                self.assertEqual(report["status"], "upstream_error")
                self.assertEqual(report["errors"][0]["http_status"], 429)
                self.assertEqual(report["errors"][0]["retry_after_seconds"], 60)
                self.assertNotIn("private", json.dumps(report))
                call.assert_called_once()
                search.search.assert_not_called()

    def test_retry_after_http_date_and_unsafe_headers(self):
        now = datetime.fromisoformat(CHECKED)
        header = format_datetime(now + timedelta(minutes=2), usegmt=True)
        with patch("freshnessguard.clients.datetime") as clock:
            clock.now.return_value = now
            self.assertEqual(retry_after_seconds(header), 120)
        for invalid in ("-1", "never", "99999999", "60\r\nsecret", None):
            self.assertIsNone(retry_after_seconds(invalid))

    def test_rate_limit_stops_remaining_paid_checks(self):
        first, second = "Python is currently maintained.", "React is currently maintained."
        search = Mock()
        search.search.side_effect = ServiceError("Upstream HTTP 429", http_status=429)
        report, llm, _ = self.replay(first + " " + second, [extracted(first, "Python"), extracted(second, "React")],
                                     search=search)
        self.assertEqual(report["claims"][1]["verification_skipped"], "upstream_rate_limit")
        self.assertEqual(report["coverage"], 0)
        search.search.assert_called_once()
        llm.complete.assert_called_once()

    def test_terminal_judgment_errors_preserve_later_claims_without_paid_calls(self):
        first = "The latest stable Python release series is 3.11."
        second = "React is currently maintained."
        historical = "Apple introduced the first iPhone on January 9, 2007."
        answer = " ".join((first, second, historical))
        for error, status, skipped in (
            (ServiceError("Upstream unavailable", code="timeout"), "unavailable", "judgment_timeout"),
            (ServiceError("Upstream HTTP 429", http_status=429, retry_after=60), "upstream_error", "upstream_rate_limit"),
        ):
            with self.subTest(status=status):
                llm, search = Mock(), Mock()
                llm.complete.side_effect = [
                    {"claims":[extracted(first, "Python"), extracted(second, "React"),
                               extracted(historical, "Apple", False)]}, error,
                ]
                search.search.return_value = {"results":[{"url":"https://www.python.org/downloads/", "content":"Python releases"}]}
                report = Verifier(llm, search, clock=lambda:CHECKED).verify(answer)
                self.assertEqual(report["status"], status)
                self.assertEqual(report["original_answer"], answer)
                self.assertEqual(report["errors"], [error.diagnostic("judgement")])
                self.assertEqual(report["claims"][1]["verification_skipped"], skipped)
                self.assertEqual(report["claims"][2]["verdict"], "not_checked")
                self.assertEqual(report["claims"][0]["citation_ids"], [])
                self.assertIsNone(report["freshness_score"])
                self.assertEqual(llm.complete.call_count, 2)
                search.search.assert_called_once()

    def test_only_outer_padding_is_recovered_without_rewriting_antecedent(self):
        answer = "Python 3.11 is the latest stable Python release series. It is the newest version recommended for production use."
        search = Mock()
        search.search.return_value = {"results":[]}
        report, _, _ = self.replay(answer, [extracted("  " + answer + "\t", "Python 3.11")], search=search)
        self.assertEqual(report["claims"][0]["text"], answer)
        self.assertEqual(report["claims"][0]["subject"], "Python 3.11")
        for text, subject in ((answer.replace("It is", "It  is"), "Python 3.11"),
                              (answer.split(". ", 1)[1], "Python 3.11")):
            with self.subTest(text=text):
                report, llm, search = self.replay(answer, [extracted(text, subject)])
                self.assertEqual(report["extraction"]["error"]["code"], "invalid_extraction")
                self.assertEqual(report["claims"], [])
                llm.complete.assert_called_once()
                search.search.assert_not_called()

    def test_duplicate_source_text_is_elided_only_from_judge_context(self):
        answer = "The latest stable Python release series is 3.11."
        content = "Python release evidence."
        rows = [{"url":f"https://www.python.org/article/{n}", "title":"Releases", "content":text}
                for n, text in enumerate((content, content, "Different possible evidence."))]
        llm, search = Mock(), Mock()
        llm.complete.side_effect = [{"claims":[extracted(answer, "Python")]},
                                    {"verdict":"uncertain", "reason":"Insufficient evidence"}]
        search.search.return_value = {"results":rows}
        report = Verifier(llm, search, clock=lambda:CHECKED).verify(answer)
        self.assertEqual([s["content"] for s in report["claims"][0]["sources"]],
                         [r["content"] for r in rows])
        self.assertEqual([s["id"] for s in llm.complete.call_args.args[1]["sources"]], ["s1", "s3"])
        self.assertNotIn("candidate_release_quote", llm.complete.call_args.args[0])
