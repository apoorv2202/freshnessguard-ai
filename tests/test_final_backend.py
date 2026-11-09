import copy
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock
from urllib.request import Request

from freshnessguard.clients import RejectAPIRedirects, ServiceError, post_json
from freshnessguard.engine import Verifier
from freshnessguard.evidence import policy_for
from freshnessguard.semantics import release_evidence_window


class FinalBackendTests(unittest.TestCase):
    def fixture(self):
        return json.loads((Path(__file__).parent/'fixtures/targeted_source_quote_failure.json').read_text(encoding='utf-8'))

    def nov09_fixture(self):
        return json.loads((Path(__file__).parent / "fixtures/nov09_live_citation_mismatch.json").read_text(encoding="utf-8"))

    def test_nov09_recorded_feed_quote_is_rejected_and_blog_alone_is_insufficient(self):
        saved = self.nov09_fixture()
        original = {**saved["claim"], "checked_at":saved["checked_at"], "source_policy":policy_for("Python")}
        decision = saved["decision"]
        blog, feed = decision["quotes"]
        self.assertIn(blog["text"], original["sources"][0]["content"])
        self.assertNotIn(feed["text"], original["sources"][1]["content"])
        self.assertIn(feed["text"].removeprefix("Python "), original["sources"][1]["content"])
        self.assertTrue(all(release_evidence_window(original, s, saved["checked_at"]) is None
                            for s in original["sources"]))
        for proposal, reason in (
            (decision, "Evidence quote does not match cited source"),
            ({**decision, "citation_ids":["s1"], "quotes":[blog]}, "No eligible cited"),
        ):
            with self.subTest(reason=reason):
                claim = copy.deepcopy(original)
                Verifier._apply_decision(claim, proposal)
                self.assertEqual(claim["verdict"], "uncertain")
                self.assertIn(reason, claim["validation_error"])
                self.assertEqual(claim["citation_ids"], [])
                self.assertIsNone(claim["correction"])

    def test_nov09_search_replay_fetches_stable_link_and_still_checks_model_quote(self):
        saved = self.nov09_fixture()
        answer = saved["claim"]["text"]
        stable = self.fixture()["claim"]["sources"][-1]
        for use_exact_quote in (True, False):
            with self.subTest(use_exact_quote=use_exact_quote):
                llm, search, retriever = Mock(), Mock(), Mock()
                search.search.return_value = {"usage":{"credits":0}, "results":saved["claim"]["sources"][:-1]}
                retriever.retrieve.return_value = stable
                extraction = {"claims":[{"text":answer, "subject":"Python", "time_sensitive":True,
                                         "query":"Python releases"}]}

                def judge(system, payload):
                    if "answer" in payload:
                        return extraction
                    quote = payload["candidate_release_quote"]
                    self.assertEqual(quote["source_id"], "s5")
                    self.assertEqual(quote["text"], "Release date: Oct. 7, 2025\n\nThis is the stable release of Python 3.14.0")
                    self.assertIn(quote["text"], stable["content"])
                    if not use_exact_quote:
                        return saved["decision"]
                    return {**saved["decision"], "citation_ids":["s5"], "quotes":[quote], "correction":quote["text"]}

                llm.complete.side_effect = judge
                report = Verifier(llm, search, retriever=retriever, clock=lambda:saved["checked_at"]).verify(answer)
                claim = report["claims"][0]
                self.assertEqual(claim["source_retrieval"]["original_reference"], "python.org/downloads/release/python-3140/")
                retriever.retrieve.assert_called_once_with(stable["url"], policy_for("Python"))
                search.search.assert_called_once()
                self.assertEqual(llm.complete.call_count, 2)
                if use_exact_quote:
                    self.assertEqual(claim["verdict"], "outdated")
                    self.assertEqual(claim["citation_ids"], ["s5"])
                    self.assertEqual(claim["semantic_validation"]["status"], "passed")
                else:
                    self.assertEqual(claim["verdict"], "uncertain")
                    self.assertEqual(claim["citation_ids"], [])
                    self.assertEqual(claim["validation_error"], "Evidence quote does not match cited source")

    def replay_retrieved_page(self, judge, answer=None):
        saved = self.fixture()
        claim = saved["claim"]
        answer = answer or claim["text"]
        llm, search, retriever = Mock(), Mock(), Mock()
        extraction = {"claims":[{"text":answer, "subject":"Python", "time_sensitive":True,
                                 "query":"Python releases"}]}

        def complete(system, payload):
            return extraction if "answer" in payload else judge(payload)

        llm.complete.side_effect = complete
        search.search.return_value = {"usage":{"credits":0}, "results":claim["sources"][:-1]}
        retriever.retrieve.return_value = claim["sources"][-1]
        report = Verifier(llm, search, retriever=retriever, clock=lambda:saved["checked_at"]).verify(answer)
        search.search.assert_called_once()
        retriever.retrieve.assert_called_once()
        self.assertEqual(llm.complete.call_count, 2)
        self.assertEqual(report["original_answer"], answer)
        self.assertNotIn("candidate_release_quote", report["claims"][0])
        prompt, payload = llm.complete.call_args.args
        self.assertEqual("candidate_release_quote" in prompt, "candidate_release_quote" in payload)
        return report["claims"][0], payload

    def test_recorded_page_exposes_exact_complete_quote_to_judgment(self):
        decision = self.fixture()["decision"]
        def judge(payload):
            return {**decision, "quotes":[payload["candidate_release_quote"]]}
        claim, payload = self.replay_retrieved_page(judge)
        window = payload["candidate_release_quote"]
        self.assertEqual(window, {
            "source_id":"s5",
            "text":"Release date: Oct. 7, 2025\n\nThis is the stable release of Python 3.14.0",
        })
        source = payload["sources"][-1]
        original_source = claim["sources"][-1]
        self.assertEqual(source, {k:v for k,v in original_source.items() if k not in ("acquisition", "retrieved_at")})
        self.assertEqual(original_source["acquisition"]["method"], "direct_https_visible_text_v1")
        self.assertEqual(original_source["retrieved_at"], payload["checked_at"])
        self.assertLess(len(json.dumps(payload, ensure_ascii=False, separators=(",", ":"))),
                        len(json.dumps({**payload, "sources":claim["sources"]})))
        self.assertEqual(source["content"], self.fixture()["claim"]["sources"][-1]["content"])
        self.assertIn(window["text"], source["content"])
        self.assertEqual(claim["verdict"], "outdated")
        self.assertEqual(claim["quotes"], [window])
        self.assertEqual(claim["semantic_validation"]["status"], "passed")

    def test_outdated_explanation_drops_unquoted_supersession_and_rankings(self):
        decision = self.fixture()["decision"]
        supported = "Python 3.14.0 was released as stable on October 7, 2025."
        for reason in (supported,
                       supported + " It was superseded by 3.14.10 as of late 2026.",
                       supported + " It is the newest and highest-ranked release."):
            with self.subTest(reason=reason):
                claim, payload = self.replay_retrieved_page(
                    lambda p: {**decision, "reason":reason, "quotes":[p["candidate_release_quote"]]})
                self.assertEqual(claim["verdict"], "outdated")
                self.assertEqual(claim["reason"], "The cited evidence establishes a newer release in the claimed scope.")
                self.assertEqual(claim["proposed_assessment"]["reason"], "Model proposal before final evidence validation.")
                self.assertEqual(claim["quotes"], [payload["candidate_release_quote"]])
                self.assertEqual(claim["correction"], decision["correction"])

    def test_uncertain_explanation_drops_uncited_factual_prose(self):
        claim, _ = self.replay_retrieved_page(lambda _: {
            "verdict":"uncertain", "reason":"Python 3.14.10 is the newest release.",
            "citation_ids":[], "quotes":[], "correction":None,
        })
        self.assertEqual(claim["verdict"], "uncertain")
        self.assertEqual(claim["reason"], "The available evidence did not justify a decisive verdict.")
        self.assertEqual(claim["citation_ids"], [])
        self.assertIsNone(claim["correction"])

    def test_recorded_incomplete_and_stitched_quotes_still_fail(self):
        decision = self.fixture()["decision"]
        comparison = ("Python 3.14.0 is the newest major release of the Python programming language, "
                      "and it contains many new features and optimisations compared to Python 3.13.")
        incomplete = "This is the stable release of Python 3.14.0\n\n" + comparison
        for quote, exact in ((incomplete, True), ("Release date: Oct. 7, 2025\n\n" + comparison, False)):
            with self.subTest(exact=exact):
                claim, payload = self.replay_retrieved_page(
                    lambda _: {**decision, "quotes":[{"source_id":"s5", "text":quote}]})
                self.assertEqual(quote in payload["sources"][-1]["content"], exact)
                self.assertIn("candidate_release_quote", payload)
                self.assertEqual(claim["verdict"], "uncertain")
                self.assertEqual(claim["citation_ids"], [])
                if exact:
                    self.assertEqual(claim["semantic_validation"]["status"], "rejected")
                else:
                    self.assertEqual(claim["validation_error"], "Evidence quote does not match cited source")

    def test_feed_timestamp_and_older_official_page_do_not_support_newer_claim(self):
        answer = "The latest stable release of Python is version 3.15.2"
        for source_id, quote in (
            ("s2", "3.15.2 date: 2026-10-25 04:15:38+00:00Sun, 25 Oct 2026 04:15:38 +0000"),
            ("s5", "Release date: Oct. 7, 2025\n\nThis is the stable release of Python 3.14.0"),
        ):
            with self.subTest(source_id=source_id):
                decision = {"verdict":"supported", "reason":"Proposed support", "evidence_conflict":False,
                            "citation_ids":[source_id], "quotes":[{"source_id":source_id, "text":quote}]}
                claim, payload = self.replay_retrieved_page(lambda _:decision, answer=answer)
                self.assertNotIn("candidate_release_quote", payload)
                self.assertEqual(claim["verdict"], "uncertain")
                self.assertEqual(claim["citation_ids"], [])
                self.assertEqual(claim["semantic_validation"]["status"], "rejected")

    def test_actual_saved_incomplete_quote_selects_exact_adjacent_complete_window(self):
        saved=self.fixture(); claim=copy.deepcopy(saved['claim'])
        original_sources=copy.deepcopy(claim['sources'])
        original_decision=copy.deepcopy(saved['decision'])
        Verifier._apply_decision(claim,saved['decision'])
        self.assertEqual(claim['verdict'],'outdated')
        self.assertEqual(claim['sources'],original_sources)
        self.assertEqual(saved['decision'],original_decision)
        self.assertEqual(claim['proposed_assessment']['quotes'],original_decision['quotes'])
        quote=claim['quotes'][0]; audit=claim['quote_windows'][0]
        source=next(s for s in claim['sources'] if s['id']==quote['source_id'])
        self.assertEqual(quote['source_id'],'s5')
        self.assertEqual(quote['text'],'Release date: Oct. 7, 2025\n\nThis is the stable release of Python 3.14.0')
        self.assertEqual(source['content'][audit['start']:audit['end']],quote['text'])
        self.assertEqual(claim['semantic_validation']['release_witnesses'][0]['date'],'2025-10-07')
        self.assertEqual(claim['correction'],original_decision['correction'])

    def modified(self,content,verdict='outdated',quote='This is the stable release of Python 3.14.0'):
        saved=self.fixture(); claim=saved['claim']; source=claim['sources'][-1]
        source['content']=content; claim['sources']=[source]
        decision={'verdict':verdict,'reason':'Synthetic boundary regression','evidence_conflict':False,
                  'citation_ids':['s5'],'quotes':[{'source_id':'s5','text':quote}],
                  'correction':'Python 3.14.0' if verdict=='outdated' else None}
        Verifier._apply_decision(claim,decision)
        return claim

    def test_missing_date_is_never_invented(self):
        claim=self.modified('This is the stable release of Python 3.14.0')
        self.assertEqual(claim['verdict'],'uncertain')
        self.assertNotIn('quote_windows',claim)

    def test_unrelated_intervening_paragraph_is_not_spliced_out(self):
        claim=self.modified('Release date: 2025-10-07\n\nOtherSDK announcement\n\nThis is the stable release of Python 3.14.0')
        self.assertEqual(claim['verdict'],'uncertain')
        self.assertNotIn('quote_windows',claim)

    def test_another_products_date_is_not_borrowed(self):
        claim=self.modified('OtherSDK release date: 2025-10-07\n\nThis is the stable release of Python 3.14.0')
        self.assertEqual(claim['verdict'],'uncertain')

    def test_duplicate_anchor_is_not_expanded(self):
        claim=self.modified('Release date: 2025-10-07\n\nThis is the stable release of Python 3.14.0\n\nRelease date: 2025-11-07\n\nThis is the stable release of Python 3.14.0')
        self.assertEqual(claim['verdict'],'uncertain')
        self.assertNotIn('quote_windows',claim)

    def test_future_and_preview_windows_cannot_establish_stable_release(self):
        for text in ('Release date: 2027-10-07\n\nThis is the stable release of Python 3.14.0',
                     'Release date: 2025-10-07\n\nThis is the stable release of Python 3.14.0 preview'):
            with self.subTest(text=text):
                self.assertEqual(self.modified(text)['verdict'],'uncertain')

    def test_invented_anchor_rejected_before_window_selection(self):
        claim=self.modified('Release date: 2025-10-07\n\nThis is the stable release of Python 3.14.0',quote='Invented Python 3.14.0 stable announcement')
        self.assertEqual(claim['verdict'],'uncertain')
        self.assertEqual(claim['validation_error'],'Evidence quote does not match cited source')
        self.assertNotIn('quote_windows',claim)

    def test_supported_quote_never_promoted_by_historical_window(self):
        claim=self.modified('Release date: 2025-10-07\n\nThis is the stable release of Python 3.14.0',verdict='supported')
        self.assertEqual(claim['verdict'],'uncertain')
        self.assertNotIn('quote_windows',claim)

    def test_redirect_handler_never_constructs_secret_bearing_cross_origin_request(self):
        req=Request('https://api.tavily.com/search',data=b'{}',headers={'Authorization':'Bearer synthetic','x-bf-vk':'synthetic'})
        for status in (301,302,303,307,308):
            with self.subTest(status=status),self.assertRaises(ServiceError) as caught:
                RejectAPIRedirects().redirect_request(req,None,status,'redirect',{},'https://untrusted.test/')
            self.assertEqual(caught.exception.code,'api_redirect_blocked')
            self.assertNotIn('synthetic',str(caught.exception))

    def test_real_opener_refuses_all_redirects_before_any_destination_request(self):
        calls=[]
        class Destination(BaseHTTPRequestHandler):
            def log_message(self,*_): pass
            def do_GET(self): calls.append('GET'); self.send_response(200); self.end_headers()
            def do_POST(self): calls.append('POST'); self.send_response(200); self.end_headers()
        destination=ThreadingHTTPServer(('127.0.0.1',0),Destination)
        class Redirect(BaseHTTPRequestHandler):
            def log_message(self,*_): pass
            def do_POST(self):
                self.rfile.read(int(self.headers.get('Content-Length','0')))
                self.send_response(int(self.path[1:])); self.send_header('Location',f'http://127.0.0.1:{destination.server_port}/'); self.end_headers()
        redirect=ThreadingHTTPServer(('127.0.0.1',0),Redirect)
        threads=[threading.Thread(target=s.serve_forever,daemon=True) for s in (destination,redirect)]
        for thread in threads: thread.start()
        try:
            for status in (301,302,303,307,308):
                with self.subTest(status=status),self.assertRaises(ServiceError) as caught:
                    post_json(f'http://127.0.0.1:{redirect.server_port}/{status}',{'private':'synthetic'},
                              {'Authorization':'Bearer synthetic','x-bf-vk':'synthetic'})
                self.assertEqual(caught.exception.code,'api_redirect_blocked')
            self.assertEqual(calls,[])
        finally:
            for server in (destination,redirect): server.shutdown(); server.server_close()
            for thread in threads: thread.join()
