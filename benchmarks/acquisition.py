"""Offline acquisition/planning overhead only; no network or real model timing."""
import hashlib
import json
import statistics
from pathlib import Path
from unittest.mock import Mock, patch

from freshnessguard.engine import Verifier
from freshnessguard.retrieval import VisibleText

FACT = "Widget 41.3.0 was released on 2026-09-01 as a stable release."
URL = "https://vendor.test/releases/tag/v41.3.0"
POLICY = {"entity":"Widget", "domains":["vendor.test"],
          "retrieval_rules":[{"host":"vendor.test", "path":r"/releases/tag/[a-zA-Z0-9.-]+"}]}


def run():
    results = []
    for name, initial, fetched, expected, retrievals in (
        ("sufficient_snippet", FACT, FACT, "outdated", 0),
        ("dated_release_retrieved", "Official release: " + URL, FACT, "outdated", 1),
        ("missing_release_date", "Official release: " + URL, "Widget 41.3.0 is a stable release.", "uncertain", 1),
        ("preview_retrieved", "Official release: " + URL, "Widget 41.3.0rc1 was released on 2026-09-01; not a stable release.", "uncertain", 1)):
        timings = []
        for _ in range(25):
            llm, search, retriever = Mock(), Mock(), Mock()
            answer = "The latest stable Widget release series is 41.2."
            def complete(system, payload):
                if "answer" in payload:
                    return {"claims":[{"text":answer,"subject":"Widget","time_sensitive":True,"query":"lookup"}]}
                source = payload["sources"][-1]
                return {"verdict":"outdated","reason":"A proposed dated newer release", "evidence_conflict":False,
                        "citation_ids":[source["id"]], "quotes":[{"source_id":source["id"],"text":source["content"]}],
                        "correction":source["content"]}
            def retrieve(url, policy):
                body = ("<html><body><p>" + fetched + "</p></body></html>").encode()
                parser = VisibleText(); parser.feed(body.decode()); parser.close()
                return {"url":url,"content":parser.text(),"body_sha256":hashlib.sha256(body).hexdigest()}
            llm.complete.side_effect = complete
            retriever.retrieve.side_effect = retrieve
            search.search.return_value = {"results":[{"url":URL,"content":initial}],"usage":{"credits":0}}
            with patch("freshnessguard.engine.policy_for", return_value=POLICY):
                report = Verifier(llm,search,retriever=retriever,mode="synthetic_acquisition",
                                  clock=lambda:"2026-11-06T12:00:00+00:00").verify(answer)
            assert report["claims"][0]["verdict"] == expected
            assert report["metrics"]["source_retrieval_calls"] == retrievals
            assert report["metrics"]["llm_calls"] == 2
            timings.append(report["metrics"]["timings_ms"])
        results.append({"case":name,"passed":True,"iterations":len(timings),"verdict":expected,
                        "source_retrieval_calls_per_case":retrievals,"llm_calls_per_case":2,
                        "median_timings_ms":{key:round(statistics.median(t[key] for t in timings),4) for key in timings[0]}})
    return {"mode":"synthetic_acquisition", "actual_paid_calls":0, "quality_accuracy":None,
            "timing_scope":"Local planning, HTML text extraction and semantic checks; search/HTTP/TLS/model are mocked. Not live latency.",
            "results":results}


def main():
    result = run()
    Path("benchmarks/acquisition-results.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
