import io
import json
import unittest
import contextlib
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from benchmarks.live import evaluate, summarize
from benchmarks.outcomes import should_stop
from freshnessguard.clients import BifrostLLM, ServiceError, TavilySearch
from freshnessguard.engine import Verifier
from freshnessguard.fixtures import CASES, demo_verifier


ANSWER = "The latest stable Python release series is 3.11."
CASE = {"answer":ANSWER, "expected":"outdated"}
COMPOUND_ANSWER = (
    "The latest stable release of Python is version 3.15.2, which was released on October 25, 2026. "
    "The major 3.15 branch was initially released on October 9, 2026"
)


def completion(content, finish_reason="stop"):
    return {"choices":[{"message":{"content":content}, "finish_reason":finish_reason}]}


class FailureTests(unittest.TestCase):
    def client(self):
        with patch.dict("os.environ", {"BIFROST_MODEL":"gemini/gemini-3-flash-preview"}, clear=True):
            return BifrostLLM()

    def assert_extraction_failure(self, report, code, category="unavailable"):
        self.assertEqual(report["status"], category)
        self.assertEqual(report["extraction"]["status"], "failed")
        self.assertEqual(report["extraction"]["error"]["code"], code)
        self.assertEqual(report["metrics"]["search_calls"], 0)
        self.assertEqual(report["metrics"]["tavily_credits"], 0)
        evaluation = evaluate(CASE, report)
        self.assertFalse(evaluation["evaluable"])
        self.assertIsNone(evaluation["pass"])
        self.assertEqual(evaluation["claims"][0]["actual"], category)
        summary = summarize([{"report":report, "evaluation":evaluation}], {"as_of":"2026-11-05"}, "test")
        self.assertEqual(summary["extraction_failure_count"], 1)
        self.assertEqual(summary["genuine_missing_claim_count"], 0)
        self.assertEqual(summary["evaluable_claim_count"], 0)
        self.assertIsNone(summary["case_agreement"])
        self.assertIsNone(summary["claim_agreement"])
        self.assertIsNone(summary["extraction_recall"])
        self.assertIsNone(summary["stale_recall"])
        self.assertIsNone(summary["coverage"])
        self.assertEqual(summary["extraction_availability"], 0)
        self.assertEqual(summary["end_to_end_success_rate"], 0)

    def test_http_429_is_structured_and_never_parsed_as_model_output(self):
        secret = "private-upstream-body-must-not-leak"
        error = HTTPError("https://example.invalid", 429, secret, {}, io.BytesIO(secret.encode()))
        search = Mock()
        with patch("freshnessguard.clients.urlopen", side_effect=error) as call:
            report = Verifier(self.client(), search).verify(ANSWER)
        self.assert_extraction_failure(report, "http_error", "upstream_error")
        self.assertEqual(report["extraction"]["error"]["http_status"], 429)
        self.assertNotIn(secret, json.dumps(report))
        self.assertFalse(report["metrics"]["model_token_usage_available"])
        call.assert_called_once()
        search.search.assert_not_called()
        self.assertTrue(should_stop(report))

    def test_empty_model_content_is_unavailable(self):
        for content in [None, "", "  \n"]:
            with self.subTest(content=content), patch("freshnessguard.clients.post_json", return_value=completion(content)):
                report = Verifier(self.client(), Mock()).verify(ANSWER)
                self.assert_extraction_failure(report, "empty_model_response")

    def test_empty_choices_are_unavailable(self):
        with patch("freshnessguard.clients.post_json", return_value={"choices":[]}):
            self.assert_extraction_failure(Verifier(self.client(), Mock()).verify(ANSWER), "empty_model_response")

    def test_invalid_model_json_is_not_missing(self):
        for content in ["not JSON", '{"claims":', '{"claims":[],"claims":[]}']:
            with self.subTest(content=content), patch("freshnessguard.clients.post_json", return_value=completion(content)):
                self.assert_extraction_failure(Verifier(self.client(), Mock()).verify(ANSWER), "invalid_model_json")

    def test_invalid_extraction_schema_is_unavailable(self):
        with patch("freshnessguard.clients.post_json", return_value=completion('{"claims":{}}')):
            self.assert_extraction_failure(Verifier(self.client(), Mock()).verify(ANSWER), "invalid_extraction")

    def test_truncated_json_is_distinct_from_invalid_json(self):
        with patch("freshnessguard.clients.post_json", return_value=completion('{"claims":', "length")):
            self.assert_extraction_failure(Verifier(self.client(), Mock()).verify(ANSWER), "truncated_model_output")

    def test_empty_http_body_is_unavailable(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b""
        with patch("freshnessguard.clients.urlopen", return_value=response):
            self.assert_extraction_failure(Verifier(self.client(), Mock()).verify(ANSWER), "empty_http_response")

    def test_valid_empty_extraction_is_a_genuine_miss(self):
        with patch("freshnessguard.clients.post_json", return_value=completion('{"claims":[]}')):
            report = Verifier(self.client(), Mock()).verify(ANSWER)
        self.assertEqual(report["extraction"]["status"], "ok")
        self.assertEqual(report["status"], "no_claims_extracted")
        evaluation = evaluate(CASE, report)
        self.assertTrue(evaluation["evaluable"])
        self.assertEqual(evaluation["claims"][0]["actual"], "missing")
        summary = summarize([{"report":report,"evaluation":evaluation}], {"as_of":"2026-11-05"}, "test")
        self.assertEqual(summary["extraction_recall"], 0)
        self.assertEqual(summary["genuine_missing_claim_count"], 1)

    def test_valid_zero_search_timeless_case_still_scores(self):
        report = demo_verifier().verify(CASES[4]["answer"])
        case = {"answer":CASES[4]["answer"], "expected":"not_checked"}
        evaluation = evaluate(case, report)
        self.assertTrue(evaluation["pass"])
        self.assertEqual(report["metrics"]["search_calls"], 0)

    def test_budget_skipped_verification_does_not_score_detector(self):
        verifier = demo_verifier(); verifier.max_claims = 0
        report = verifier.verify(CASES[0]["answer"])
        evaluation = evaluate({"answer":CASES[0]["answer"], "expected":"outdated"}, report)
        summary = summarize([{"report":report, "evaluation":evaluation}], {"as_of":"2026-11-05"}, "test")
        self.assertEqual(summary["extraction_recall"], 1)
        self.assertIsNone(summary["case_agreement"])
        self.assertEqual(evaluation["claims"][0]["actual"], "not_evaluated")

    def test_saved_legacy_429_report_reclassifies_without_api_calls(self):
        report = {"status":"incomplete","warnings":["Upstream HTTP 429"],"claims":[],
            "metrics":{"latency_ms":2405.22,"search_calls":0,"llm_calls":1,"tavily_credits":0,"credit_usage_complete":True}}
        self.assertTrue(should_stop(report))
        evaluation = evaluate(CASE, report)
        self.assertEqual(evaluation["claims"][0]["actual"], "upstream_error")
        summary = summarize([{"report":report,"evaluation":evaluation}], {"as_of":"2026-11-05"}, "test")
        self.assertIsNone(summary["extraction_recall"])
        self.assertEqual(summary["median_latency_ms"], 2405.22)

    def test_partial_invalid_extraction_never_triggers_search(self):
        llm = Mock()
        good = {"text":ANSWER,"subject":"Python","time_sensitive":True,"query":"Python releases"}
        llm.complete.return_value = {"claims":[good, {"text":"invented","time_sensitive":True}]}
        search = Mock()
        report = Verifier(llm, search).verify(ANSWER)
        self.assert_extraction_failure(report, "invalid_extraction")
        search.search.assert_not_called()

    def test_recorded_compound_extraction_rejects_rewritten_text_and_subject(self):
        latest = {"text":"The latest stable release of Python is version 3.15.2",
                  "subject":"Python", "time_sensitive":True, "query":"Python stable releases"}
        rewritten = {"text":"Python version 3.15.2 was released on October 25, 2026",
                     "subject":"Python version 3.15.2", "time_sensitive":False}
        expanded_subject = {"text":"The major 3.15 branch was initially released on October 9, 2026",
                            "subject":"Python 3.15 branch", "time_sensitive":False}
        for invalid_claims, message in (
            ([rewritten, expanded_subject], "Invalid claim extraction: claim text must be a verbatim span of the answer. Include the original subject and connecting words"),
            ([expanded_subject], "Claim extraction lacks a concrete grounded subject. Copy the subject from within the claim span"),
        ):
            with self.subTest(message=message):
                search = Mock()
                body = completion(json.dumps({"claims":[latest, *invalid_claims]}))
                with patch("freshnessguard.clients.post_json", return_value=body) as post:
                    report = Verifier(self.client(), search).verify(COMPOUND_ANSWER)
                self.assertEqual(report["status"], "unavailable")
                self.assertEqual(report["extraction"]["error"]["code"], "invalid_extraction")
                self.assertEqual(report["warnings"], [message])
                self.assertEqual(report["claims"], [])
                self.assertEqual(report["metrics"]["search_calls"], 0)
                search.search.assert_not_called()
                post.assert_called_once()

    def test_compound_extraction_accepts_overlapping_verbatim_spans(self):
        release_sentence, branch_sentence = COMPOUND_ANSWER.split(". ", 1)
        latest = release_sentence.split(", ", 1)[0]
        claims = [
            {"text":latest, "subject":"Python", "time_sensitive":True, "query":"Python stable releases"},
            {"text":release_sentence, "subject":"Python", "time_sensitive":False},
            {"text":branch_sentence, "subject":"3.15 branch", "time_sensitive":False},
        ]
        search = Mock()
        search.search.return_value = {"results":[], "usage":{"credits":0}}
        with patch("freshnessguard.clients.post_json", return_value=completion(json.dumps({"claims":claims}))) as post:
            report = Verifier(self.client(), search).verify(COMPOUND_ANSWER)
        self.assertEqual(report["extraction"]["status"], "ok")
        self.assertEqual([claim["text"] for claim in report["claims"]], [latest, release_sentence, branch_sentence])
        self.assertEqual([claim["verdict"] for claim in report["claims"]], ["uncertain", "not_checked", "not_checked"])
        search.search.assert_called_once()
        post.assert_called_once()

    def test_recorded_two_sentence_python_subject_requires_antecedent_in_span(self):
        first = "Python 3.11 is the latest stable Python release series"
        second = "It is the newest version recommended for production use"
        answer = f"{first}. {second}."
        for grounded in (False, True):
            with self.subTest(grounded=grounded):
                claims = [{"text":text, "subject":"Python 3.11", "time_sensitive":True,
                           "query":"Python stable releases"} for text in (first, answer if grounded else second)]
                search = Mock()
                search.search.return_value = {"results":[], "usage":{"credits":0}}
                with patch("freshnessguard.clients.post_json", return_value=completion(json.dumps({"claims":claims}))) as post:
                    report = Verifier(self.client(), search).verify(answer)
                post.assert_called_once()
                self.assertEqual(report["original_answer"], answer)
                if grounded:
                    self.assertEqual(report["extraction"]["status"], "ok")
                    self.assertEqual([c["text"] for c in report["claims"]], [first, answer])
                    self.assertEqual(search.search.call_count, 2)
                else:
                    self.assertEqual(report["status"], "unavailable")
                    self.assertEqual(report["extraction"]["error"]["code"], "invalid_extraction")
                    self.assertIn("Copy the subject from within the claim span", report["warnings"][0])
                    self.assertEqual(report["claims"], [])
                    search.search.assert_not_called()

    def test_recorded_pronoun_paraphrase_fails_despite_valid_json_and_flags(self):
        first = "Python 3.11 is the latest stable Python release series."
        answer = first + " It is the newest version recommended for production use."
        claims = [{"text":text, "subject":"Python 3.11", "time_sensitive":True, "query":"Python releases"}
                  for text in (first, "Python 3.11 is the newest version recommended for production use.")]
        search = Mock()
        with patch("freshnessguard.clients.post_json", return_value=completion(json.dumps({"claims":claims}))) as post:
            report = Verifier(self.client(), search).verify(answer)
        self.assertEqual(report["status"], "unavailable")
        self.assertEqual(report["claims"], [])
        self.assertEqual(report["extraction"]["error"]["code"], "invalid_extraction")
        self.assertIn("claim text must be a verbatim span", report["warnings"][0])
        post.assert_called_once()
        search.search.assert_not_called()

    def test_time_sensitive_flag_must_be_present_and_boolean(self):
        for flag, message in (
            ({}, "missing time_sensitive flag"),
            ({"time_sensitive":"true"}, "time_sensitive must be a JSON boolean"),
            ({"time_sensitive":1}, "time_sensitive must be a JSON boolean"),
        ):
            with self.subTest(flag=flag):
                search = Mock()
                claims = [{"text":ANSWER, "subject":"Python", "query":"Python releases", **flag}]
                with patch("freshnessguard.clients.post_json", return_value=completion(json.dumps({"claims":claims}))) as post:
                    report = Verifier(self.client(), search).verify(ANSWER)
                self.assert_extraction_failure(report, "invalid_extraction")
                self.assertIn(message, report["warnings"][0])
                body = post.call_args.args[1]
                schema = body["response_format"]["json_schema"]["schema"]
                items = schema["properties"]["claims"]["items"]
                self.assertEqual(body["response_format"]["type"], "json_schema")
                self.assertIn("time_sensitive", items["required"])
                self.assertEqual(items["properties"]["time_sensitive"], {"type":"boolean"})
                self.assertEqual(post.call_args.kwargs["timeout"], 20)
                post.assert_called_once()
                search.search.assert_not_called()

    def test_grounded_historical_iphone_claim_does_not_trigger_search(self):
        answer = "The first iPhone was introduced by Apple on January 9, 2007."
        claims = [{"text":answer, "subject":"iPhone", "time_sensitive":False}]
        search = Mock()
        with patch("freshnessguard.clients.post_json", return_value=completion(json.dumps({"claims":claims}))) as post:
            report = Verifier(self.client(), search).verify(answer)
        self.assertEqual(report["status"], "no_time_sensitive_claims")
        self.assertEqual(report["claims"][0]["text"], answer)
        self.assertEqual(report["claims"][0]["subject"], "iPhone")
        self.assertEqual(report["claims"][0]["verdict"], "not_checked")
        self.assertIsNone(report["freshness_score"])
        post.assert_called_once()
        search.search.assert_not_called()

    def test_judge_429_preserves_extraction_quality_but_excludes_detector_score(self):
        verifier = demo_verifier()
        original = verifier.llm.complete
        def complete(system, payload):
            if "claim" in payload:
                raise ServiceError("Upstream HTTP 429", http_status=429)
            return original(system, payload)
        verifier.llm.complete = complete
        report = verifier.verify(CASES[0]["answer"])
        evaluation = evaluate({"answer":CASES[0]["answer"], "expected":"outdated"}, report)
        summary = summarize([{"report":report,"evaluation":evaluation}], {"as_of":"2026-11-05"}, "test")
        self.assertEqual(report["errors"][0]["stage"], "judgement")
        self.assertEqual(summary["extraction_recall"], 1)
        self.assertIsNone(summary["stale_recall"])

    def verify_with_simulated_judgment(self, delay, model="gemini/gemini-3-flash-preview"):
        evidence = "Python 3.14.0 was released on 2025-10-07 as a stable release."
        extraction = {"claims":[{"text":ANSWER, "subject":"Python", "time_sensitive":True,
                                 "query":"Python stable releases"}]}
        judgment = {"verdict":"outdated", "reason":"A newer stable release exists",
                    "citation_ids":["s1"], "quotes":[{"source_id":"s1", "text":evidence}],
                    "correction":evidence, "evidence_conflict":False}
        search = {"results":[{"url":"https://www.python.org/downloads/release/python-3140/",
                              "content":evidence}], "usage":{"credits":1}}
        requests = []

        def open_response(request, *, timeout):
            if request.host == "api.tavily.com":
                stage, response = "search", search
            else:
                messages = json.loads(request.data)["messages"]
                payload = json.loads(messages[1]["content"])
                if "answer" in payload:
                    stage, response = "extraction", completion(json.dumps(extraction))
                else:
                    stage, response = "judgment", completion(json.dumps(judgment))
            requests.append((stage, timeout))
            if stage == "judgment" and delay > timeout:
                raise TimeoutError()
            return io.BytesIO(json.dumps(response).encode())

        with patch.dict("os.environ", {"BIFROST_MODEL":model, "TAVILY_API_KEY":"test-only"}, clear=True), \
             patch("freshnessguard.clients.urlopen", side_effect=open_response):
            report = Verifier(BifrostLLM(), TavilySearch(), clock=lambda: "2026-11-07T00:00:00+00:00").verify(ANSWER)
        return report, requests

    def test_gemini_judgment_within_extended_timeout_reaches_validator(self):
        report, requests = self.verify_with_simulated_judgment(34.18)
        self.assertEqual(requests, [("extraction", 20), ("search", 20), ("judgment", 45)])
        claim = report["claims"][0]
        self.assertEqual(claim["verdict"], "outdated")
        self.assertEqual(claim["citation_ids"], ["s1"])
        self.assertEqual(claim["semantic_validation"]["status"], "passed")

    def test_gemini_judgment_beyond_extended_timeout_is_unavailable_without_retry(self):
        report, requests = self.verify_with_simulated_judgment(86.50)
        self.assertEqual(requests, [("extraction", 20), ("search", 20), ("judgment", 45)])
        self.assertEqual(report["status"], "unavailable")
        self.assertEqual(report["extraction"]["status"], "ok")
        self.assertEqual(report["errors"][0]["stage"], "judgement")
        self.assertEqual(report["errors"][0]["code"], "timeout")
        self.assertEqual(report["claims"][0]["verdict"], "uncertain")
        self.assertEqual(report["claims"][0]["citation_ids"], [])
        self.assertEqual(report["claims"][0]["reason"], "Upstream unavailable")
        self.assertEqual(report["coverage"], 0)
        self.assertIsNone(report["freshness_score"])

    def test_other_bifrost_models_keep_default_judgment_timeout(self):
        _, requests = self.verify_with_simulated_judgment(0, model="provider/model")
        self.assertEqual(requests, [("extraction", 20), ("search", 20), ("judgment", 20)])

    def test_numbers_in_valid_reason_do_not_trigger_overload_stop(self):
        report = demo_verifier().verify(CASES[0]["answer"])
        report["claims"][0]["reason"] = "Version 429 is older than 503"
        self.assertFalse(should_stop(report))

    def test_gemini_json_and_thinking_request_contract(self):
        with patch("freshnessguard.clients.post_json", return_value=completion('{"claims":[]}')) as call:
            self.client().complete("extract", {"answer":ANSWER})
        body = call.call_args.args[1]
        headers = call.call_args.args[2]
        self.assertEqual(body["response_format"], {"type":"json_object"})
        self.assertEqual(body["max_tokens"], 2800)
        self.assertEqual(body["reasoning_effort"], "minimal")
        self.assertEqual(headers["x-freshnessguard-internal"], "1")
        self.assertNotIn("x-freshnessguard", headers)

    def test_absent_usage_does_not_invalidate_valid_model_json(self):
        client = self.client()
        response = {**completion('{"claims":[]}'), "usage":None}
        with patch("freshnessguard.clients.post_json", return_value=response):
            self.assertEqual(client.complete("extract", {}), {"claims":[]})
        self.assertEqual(client.usage_responses, 0)

    def test_benchmark_saves_failure_and_stops_after_one_request(self):
        from benchmarks.live import main
        report = {"status":"incomplete","warnings":["Upstream HTTP 429"],"claims":[],
            "metrics":{"latency_ms":2405.22,"search_calls":0,"llm_calls":1,"tavily_credits":0,"credit_usage_complete":True}}
        verifier = Mock(); verifier.verify.return_value = report
        with tempfile.TemporaryDirectory() as folder:
            cases, output = Path(folder) / "cases.json", Path(folder) / "result.json"
            cases.write_text(json.dumps({"as_of":"2026-11-05","cases":[CASE, CASE]}))
            with patch("benchmarks.live.live_verifier", return_value=verifier), patch("sys.argv", [
                "benchmark", "--cases",str(cases),"--output",str(output),"--interval-seconds","0"
            ]), contextlib.redirect_stdout(io.StringIO()):
                main()
            saved = json.loads(output.read_text())
        verifier.verify.assert_called_once()
        self.assertEqual(saved["run_status"], "stopped_upstream_error")
        self.assertEqual(saved["requested_case_count"], 2)
        self.assertEqual(saved["case_count"], 1)
        self.assertIsNone(saved["case_agreement"])
