"""All DNS, HTTP, TLS and LLM responses below are offline test doubles."""
import copy
import hashlib
import json
import socket
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock, patch

from freshnessguard.clients import ServiceError
from freshnessguard.engine import Verifier
from freshnessguard.evidence import policy_for
from freshnessguard.retrieval import (MAX_BYTES, MAX_TEXT, MAX_HEADERS, BoundedResponse, OfficialPageRetriever,
    VisibleText, public_address, target_for, validate_url)

CHECKED = "2026-11-06T12:00:00+00:00"
POLICY = {"entity":"Widget", "domains":["vendor.test"],
    "retrieval_rules":[{"host":"vendor.test", "path":r"/releases/tag/[a-zA-Z0-9.-]+"}]}
URL = "https://vendor.test/releases/tag/v41.3.0"
FACT = "Widget 41.3.0 was released on 2026-09-01 as a stable release."


@contextmanager
def wire(body=b"<p>Page text</p>", status=200, headers=None):
    response = Mock(status=status)
    values = {"Content-Type":"text/html", **(headers or {})}
    response.getheader.side_effect = lambda key, default=None:values.get(key, default)
    response.read1.side_effect = [body, b""]
    conn, sock, secured = Mock(), Mock(), Mock()
    conn.getresponse.return_value = response
    with patch("freshnessguard.retrieval.public_address", return_value=(socket.AF_INET,socket.SOCK_STREAM,6,"",("8.8.8.8",443))), \
         patch("freshnessguard.retrieval.socket.socket", return_value=sock), \
         patch("freshnessguard.retrieval.ssl.create_default_context") as tls, \
         patch("freshnessguard.retrieval.http.client.HTTPSConnection", return_value=conn):
        tls.return_value.wrap_socket.return_value = secured
        yield response, conn, sock, secured, tls


class SourceRetrievalTests(unittest.TestCase):
    def pipeline(self, content=FACT, initial="Release index. " + URL, failure=None, answer=None, max_retrievals=1, source_url=URL, real_transport=False):
        answer = answer or "The latest stable Widget release series is 41.2."
        llm, search, retriever = Mock(), Mock(), Mock()
        def complete(system, payload):
            if "answer" in payload:
                return {"claims":[{"text":answer,"subject":"Widget","time_sensitive":True,"query":"lookup"}]}
            source = payload["sources"][-1]
            return {"verdict":"outdated","reason":"A dated newer stable release exists", "evidence_conflict":False,
                "citation_ids":[source["id"]], "quotes":[{"source_id":source["id"],"text":source["content"]}],
                "correction":source["content"]}
        llm.complete.side_effect = complete
        search.search.return_value = {"results":[{"url":source_url,"content":initial}],"usage":{"credits":0}}
        retriever.retrieve.return_value = {"url":URL,"content":content}
        if failure:
            retriever.retrieve.side_effect = failure
        if real_transport:
            retriever = OfficialPageRetriever()
        with patch("freshnessguard.engine.policy_for", return_value=POLICY):
            report = Verifier(llm, search, clock=lambda:CHECKED, retriever=retriever,
                              max_retrievals=max_retrievals).verify(answer)
        return report, llm, search, retriever

    def test_newer_release_fetched_before_single_judge_with_exact_provenance(self):
        report, llm, search, retriever = self.pipeline()
        claim = report["claims"][0]
        self.assertEqual(claim["verdict"], "outdated")
        self.assertEqual(report["metrics"]["llm_calls"], 2)
        self.assertEqual(report["metrics"]["source_retrieval_calls"], 1)
        self.assertEqual(search.search.call_count, 1)
        self.assertEqual(retriever.retrieve.call_count, 1)
        payload = llm.complete.call_args_list[1].args[1]
        self.assertEqual(payload["sources"][-1]["content"], FACT)
        self.assertEqual(claim["correction"], FACT)
        self.assertEqual(claim["citation_ids"], ["s2"])
        self.assertEqual(claim["semantic_validation"]["release_witnesses"][0]["date"], "2026-09-01")

    def test_missing_date_does_not_become_proof(self):
        report, llm, *_ = self.pipeline(content="Widget 41.3.0 is a stable release.")
        self.assertNotIn("candidate_release_quote", llm.complete.call_args.args[1])
        self.assertEqual(report["claims"][0]["verdict"], "uncertain")

    def test_full_fetch_parse_judge_semantic_path_is_grounded(self):
        with wire(body=("<h1>Widget 41.3.0</h1><p>Release date: 2026-09-01</p><p>This is the stable release of Widget 41.3.0.</p>").encode()):
            report, llm, _, _ = self.pipeline(real_transport=True)
        claim = report["claims"][0]
        self.assertEqual(claim["verdict"], "outdated")
        source = claim["sources"][-1]
        self.assertEqual(claim["quotes"][0]["text"],source["content"])
        self.assertIn("\n\nRelease date: 2026-09-01\n\n", source["content"])
        self.assertEqual(source["acquisition"]["text_sha256"],hashlib.sha256(source["content"].encode()).hexdigest())
        self.assertEqual(llm.complete.call_count,2)

    def test_prerelease_does_not_become_stable_proof(self):
        report, llm, *_ = self.pipeline(content="Widget 41.3.0rc1 was released on 2026-09-01; this is not a stable release.")
        self.assertNotIn("candidate_release_quote", llm.complete.call_args.args[1])
        self.assertEqual(report["claims"][0]["verdict"], "uncertain")

    def test_sufficient_snippet_avoids_retrieval(self):
        report, _, _, retriever = self.pipeline(initial=FACT)
        retriever.retrieve.assert_not_called()
        self.assertEqual(report["claims"][0]["verdict"], "outdated")
        self.assertEqual(report["claims"][0]["source_retrieval"]["reason"], "snippets_already_sufficient")

    def test_current_supported_snippet_avoids_retrieval(self):
        report, _, _, retriever = self.pipeline(initial="As of 2026-11-06, the latest stable Widget release series is 41.2.",
                                              source_url="https://vendor.test/downloads/")
        retriever.retrieve.assert_not_called()
        self.assertEqual(report["metrics"]["source_retrieval_calls"], 0)

    def test_timeout_degrades_to_original_evidence_once_without_retry(self):
        report, llm, _, retriever = self.pipeline(failure=ServiceError("Source retrieval timed out",code="source_timeout"))
        claim = report["claims"][0]
        self.assertEqual(claim["verdict"], "uncertain")
        self.assertEqual(claim["source_retrieval"]["error"]["code"], "source_timeout")
        self.assertEqual(retriever.retrieve.call_count, 1)
        self.assertEqual(llm.complete.call_count, 2)

    def test_zero_budget_disables_retrieval(self):
        report, _, _, retriever = self.pipeline(max_retrievals=0)
        retriever.retrieve.assert_not_called()
        self.assertEqual(report["metrics"]["source_retrieval_calls"], 0)

    def test_budget_is_one_across_multiple_claims(self):
        llm, search, retriever = Mock(), Mock(), Mock()
        texts = [f"The latest stable Widget release series is {v}." for v in ("41.2", "41.1")]
        llm.complete.side_effect = [{"claims":[{"text":t,"subject":"Widget","time_sensitive":True,"query":"lookup"} for t in texts]},
            {"verdict":"uncertain","reason":"Insufficient","citation_ids":[],"quotes":[]},
            {"verdict":"uncertain","reason":"Insufficient","citation_ids":[],"quotes":[]}]
        search.search.return_value = {"results":[{"url":URL,"content":"Release index"}],"usage":{"credits":0}}
        retriever.retrieve.side_effect = ServiceError("Source failed",code="source_timeout")
        with patch("freshnessguard.engine.policy_for", return_value=POLICY):
            report = Verifier(llm, search, retriever=retriever, clock=lambda:CHECKED,
                              max_retrievals=1).verify(" ".join(texts))
        self.assertEqual(retriever.retrieve.call_count, 1)
        self.assertEqual(report["metrics"]["source_retrieval_calls"], 1)

    def test_structured_timings_include_all_stages(self):
        report, *_ = self.pipeline()
        timings = report["metrics"]["timings_ms"]
        self.assertEqual(set(timings), {"extraction","search","source_retrieval","judgment","semantic_validation","total"})
        self.assertTrue(all(isinstance(v, (int,float)) and v >= 0 for v in timings.values()))
        self.assertEqual(timings["total"], report["metrics"]["latency_ms"])

    def test_observed_python_snippet_exposes_target_without_fabricated_version(self):
        saved = json.loads((Path(__file__).parent / "fixtures/release_index_live_evidence.json").read_text(encoding="utf-8"))
        claim = saved["claim"]
        claim["source_policy"] = policy_for(claim["text"])
        target = target_for(claim)
        self.assertEqual(target["url"], "https://www.python.org/downloads/release/python-3140/")
        self.assertEqual(target["original_reference"], "python.org/downloads/release/python-3140/")
        self.assertEqual(target["parent_source_id"], "s1")

    def test_stable_scope_uses_index_when_only_preview_snapshots_are_linked(self):
        index = "https://vendor.test/downloads/"
        policy = {**POLICY, "retrieval_rules":[*POLICY["retrieval_rules"],
                  {"host":"vendor.test", "path":r"/downloads/"}]}
        for version in ("v42.0.0a3", "v42.0.0b2", "v42.0.0rc1", "v42.0.0-beta.2", "v42.0.0-preview", "v42-ea"):
            with self.subTest(version=version):
                preview = f"https://vendor.test/releases/tag/{version}"
                claim = {"text":"The latest stable Widget release is 41.2.", "source_policy":policy,
                         "sources":[{"id":"s1", "url":preview, "content":index}]}
                self.assertEqual(target_for(claim)["url"], index)
                claim["text"] = "The latest preview Widget release is 41.2."
                self.assertEqual(target_for(claim)["url"], preview)

    def test_blocked_urls_do_not_resolve_or_connect(self):
        urls = ["http://vendor.test/releases/tag/v1", "https://127.0.0.1/releases/tag/v1", "https://vendor.test.evil/releases/tag/v1",
            "https://user:pass@vendor.test/releases/tag/v1", "https://vendor.test:8443/releases/tag/v1",
            URL+"?token=secret", URL+"#fragment", "https://vendor.test/%2e%2e/releases/tag/v1",
            "https://vendor.test/../releases/tag/v1", "https://vendor.test./releases/tag/v1",
            "https://vendor.test/admin", "https://[::1]/", "https://vendor.test\\@127.0.0.1/releases/tag/v1"]
        with patch("freshnessguard.retrieval.public_address") as dns:
            for url in urls:
                with self.subTest(url=url), self.assertRaises(ServiceError):
                    OfficialPageRetriever().retrieve(url, POLICY)
            dns.assert_not_called()

    def test_mixed_private_dns_answers_are_blocked(self):
        for ip in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "fc00::1", "::ffff:8.8.8.8", "224.0.0.1", "64:ff9b::a00:1", "2002:0808:0808::1"):
            addresses = [(socket.AF_INET,socket.SOCK_STREAM,6,"",("8.8.8.8",443)),
                         (socket.AF_INET,socket.SOCK_STREAM,6,"",(ip,443))]
            with self.subTest(ip=ip), patch("freshnessguard.retrieval.socket.getaddrinfo", return_value=addresses), \
                 self.assertRaises(ServiceError) as caught:
                public_address("vendor.test", __import__('time').monotonic()+6)
            self.assertEqual(caught.exception.code, "blocked_source_address")

    def test_redirects_are_not_followed(self):
        for status in (301,302,303,307,308):
            with self.subTest(status=status), wire(status=status, headers={"Location":"http://127.0.0.1/"}) as (_,conn,sock,_,_):
                with self.assertRaises(ServiceError) as caught:
                    OfficialPageRetriever().retrieve(URL,POLICY)
                self.assertEqual(caught.exception.code,"source_redirect_blocked")
                self.assertEqual(conn.request.call_count,1)
                self.assertEqual(sock.connect.call_count,1)

    def test_pinned_ip_tls_hostname_and_no_authorization(self):
        with wire(body=b"<h1>Widget 41.3.0</h1><p>Release date: 2026-09-01</p><p>This is the stable release.</p>") as (_,conn,sock,_,tls):
            result = OfficialPageRetriever().retrieve(URL,POLICY)
            sock.connect.assert_called_once_with(("8.8.8.8",443))
            tls.return_value.wrap_socket.assert_called_once_with(sock,server_hostname="vendor.test",do_handshake_on_connect=False)
            headers = conn.request.call_args.kwargs["headers"]
            self.assertNotIn("Authorization",headers)
            self.assertNotIn("Cookie",headers)
            self.assertEqual(result["url"],URL)
            self.assertEqual(result["text_sha256"],hashlib.sha256(result["content"].encode()).hexdigest())

    def test_timeout_has_safe_code(self):
        with wire() as (_,_,sock,_,_):
            sock.connect.side_effect = TimeoutError("sensitive-error-detail")
            with self.assertRaises(ServiceError) as caught:
                OfficialPageRetriever().retrieve(URL,POLICY)
            self.assertEqual(caught.exception.code,"source_timeout")
            self.assertNotIn("sensitive",str(caught.exception))

    def test_tls_and_body_timeouts_do_not_retry(self):
        for stage in ("tls", "body"):
            with self.subTest(stage=stage), wire() as (response,conn,_,secured,_):
                if stage == "tls":
                    secured.do_handshake.side_effect = TimeoutError()
                else:
                    response.read1.side_effect = TimeoutError()
                with self.assertRaises(ServiceError) as caught:
                    OfficialPageRetriever().retrieve(URL,POLICY)
                self.assertEqual(caught.exception.code,"source_timeout")
                self.assertLessEqual(conn.request.call_count,1)

    def test_dns_deadline_fails_without_connecting(self):
        import queue
        with patch("freshnessguard.retrieval.queue.Queue") as result_queue, \
             patch("freshnessguard.retrieval.threading.Thread"), \
             patch("freshnessguard.retrieval.socket.socket") as connect:
            result_queue.return_value.get.side_effect = queue.Empty()
            with self.assertRaises(ServiceError) as caught:
                OfficialPageRetriever().retrieve(URL,POLICY)
            self.assertEqual(caught.exception.code,"source_timeout")
            connect.assert_not_called()

    def test_streamed_body_limit(self):
        with wire() as (response,_,_,_,_):
            response.read1.side_effect = [b"x"*MAX_BYTES,b"x"]
            with self.assertRaises(ServiceError) as caught:
                OfficialPageRetriever().retrieve(URL,POLICY)
            self.assertEqual(caught.exception.code,"source_too_large")

    def test_declared_size_media_and_compression_rejected(self):
        for headers in ({"Content-Length":str(MAX_BYTES+1)}, {"Content-Type":"application/octet-stream"},
                        {"Content-Encoding":"gzip"}):
            with self.subTest(headers=headers), wire(headers=headers) as (response,_,_,_,_):
                with self.assertRaises(ServiceError):
                    OfficialPageRetriever().retrieve(URL,POLICY)
                response.read1.assert_not_called()

    def test_http_header_budget_without_network(self):
        import io
        for raw, valid in ((b"HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nbody", True),
                           (b"HTTP/1.1 200 OK\r\nX-Huge: "+b"x"*MAX_HEADERS+b"\r\n\r\n", False)):
            sock = Mock()
            sock.makefile.return_value = io.BytesIO(raw)
            response = BoundedResponse(sock)
            if valid:
                response.begin()
                self.assertEqual(response.read(), b"body")
            else:
                with self.assertRaises(ServiceError) as caught:
                    response.begin()
                self.assertEqual(caught.exception.code,"source_headers_too_large")
            response.close()

    def test_safe_text_extraction_and_hidden_content(self):
        parser = VisibleText()
        parser.feed('<head>ignored</head><script>bad()</script><p>Widget &amp; facts</p><div hidden>hidden</div><p>Release date: 2026-09-01</p>')
        self.assertEqual(parser.text(), "Widget & facts\n\nRelease date: 2026-09-01")

    def test_html_nesting_is_bounded(self):
        parser = VisibleText()
        with self.assertRaises(ServiceError):
            parser.feed("<div>"*129)

    def test_text_budget_is_explicit(self):
        with wire(body=b"x"*(MAX_TEXT+1),headers={"Content-Type":"text/plain"}):
            result=OfficialPageRetriever().retrieve(URL,POLICY)
            self.assertEqual(len(result["content"]),MAX_TEXT)
            self.assertTrue(result["text_truncated"])

    def test_invented_judge_quote_is_rejected_even_after_fetch(self):
        report,llm,_,_=self.pipeline()
        claim = copy.deepcopy(report["claims"][0])
        decision = {"verdict":"outdated","reason":"Invented detail","evidence_conflict":False,
                    "citation_ids":["s2"],"quotes":[{"source_id":"s2","text":FACT+" invented"}],"correction":FACT}
        Verifier._apply_decision(claim,decision)
        self.assertEqual(claim["verdict"],"uncertain")
        self.assertEqual(claim["validation_error"],"Evidence quote does not match cited source")
