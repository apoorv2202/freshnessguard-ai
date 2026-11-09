"""Deterministic synthetic verification cases. No network clients are constructed."""
import json
from unittest.mock import Mock

from freshnessguard.clients import ServiceError
from freshnessguard.engine import Verifier


CHECKED = "2026-11-09T10:00:00+00:00"
PYTHON = "The latest stable Python release series is 3.11."
CURRENT = "The latest stable Python release series is 3.14."
JAVA = "Java 17 is the newest Java LTS release."
NODE = "Node.js 20.0 is the latest stable Node.js release series."
HISTORY = "Python 3.14.0 was released on October 7, 2025."
STABLE = "Python 3.14.0 was released on October 7, 2025 as a stable release."
DATED_CURRENT = "As of 2026-11-09, the latest stable Python release series is 3.14."
PY_URL = "https://www.python.org/downloads/release/python-3140/"
JAVA_URL = "https://www.oracle.com/java/technologies/java-se-support-roadmap.html"
JAVA_LTS = "Java 25 was released on September 16, 2025 as a stable LTS release."


def row(content, url=PY_URL):
    return {"url":url, "content":content}


def proposal(text, verdict="outdated", source="s1", **overrides):
    return {"verdict":verdict, "reason":"Synthetic judge", "citation_ids":[source],
            "quotes":[{"source_id":source, "text":text}], "evidence_conflict":False,
            "correction":text if verdict=="outdated" else None, **overrides}


def cases():
    for name, answer, sources, judge, expected in (
        ("dated-newer", PYTHON, [row(STABLE)], proposal(STABLE), "outdated"),
        ("exact-current", CURRENT, [row(DATED_CURRENT, "https://www.python.org/downloads/")], proposal(DATED_CURRENT,"supported"), "supported"),
        ("old-page-is-not-current", CURRENT, [row(STABLE)], proposal(STABLE,"supported"), "uncertain"),
        ("third-party-proof-rejected", PYTHON, [row(STABLE,"https://vendor.test/python")], proposal(STABLE), "uncertain"),
        ("fabricated-quote", PYTHON, [row(STABLE)], proposal(STABLE+" Today."), "uncertain"),
        ("unknown-source", PYTHON, [row(STABLE)], proposal(STABLE,source="s9"), "uncertain"),
        ("nonmatching-correction", PYTHON, [row(STABLE)], proposal(STABLE,correction="Python 3.16 is stable."), "uncertain"),
        ("conflicting-evidence", PYTHON, [row(STABLE)], proposal(STABLE,evidence_conflict=True), "uncertain"),
        ("missing-source", PYTHON, [], None, "uncertain"),
        ("no-date", PYTHON, [row("Python 3.14.0 is a stable release.")], proposal("Python 3.14.0 is a stable release."), "uncertain"),
        ("preview-is-not-stable", PYTHON, [row(STABLE.replace("stable", "preview"))], proposal(STABLE.replace("stable","preview")), "uncertain"),
        ("future-release", PYTHON, [row(STABLE.replace("2025", "2028"))], proposal(STABLE.replace("2025","2028")), "uncertain"),
        ("java-feature-lts", JAVA, [row(JAVA_LTS,JAVA_URL)], proposal(JAVA_LTS), "outdated"),
        ("java-irrelevant", JAVA, [row("Trade release schedule.", "https://www.census.gov/foreign-trade/")], None, "uncertain"),
        ("node-dated-release", NODE, [row("Node.js 22.0 was released on May 1, 2025 as a stable release.","https://nodejs.org/en/download/")],
         proposal("Node.js 22.0 was released on May 1, 2025 as a stable release."), "outdated"),
        ("http-429-at-judgment", PYTHON, [row(STABLE)], ServiceError("Upstream HTTP 429",http_status=429), "uncertain"),
        ("timeout-at-judgment", PYTHON, [row(STABLE)], ServiceError("Upstream unavailable",code="timeout"), "uncertain"),
        ("source-reference", PYTHON, [row(STABLE)], {"verdict":"outdated","reason":"Synthetic candidate selection",
          "evidence_conflict":False,"use_candidate_release_quote":True,"citation_ids":[],"quotes":[],"correction":None}, "outdated"),
    ):
        checks = {}
        if name == "java-irrelevant":
            checks["llm_calls"] = 1
        if isinstance(judge, ServiceError):
            checks["status"] = "upstream_error" if judge.http_status else "unavailable"
        yield name, [answer], [sources], [judge], [expected], checks
    yield "historical", [HISTORY], [], [], ["not_checked"], {"search_calls":0}
    yield "mixed-historical", [PYTHON,HISTORY], [[row(STABLE)]], [proposal(STABLE)], ["outdated","not_checked"], {"search_calls":1}
    yield "mixed-independent", [PYTHON,CURRENT], [[row(STABLE)],[row(DATED_CURRENT,"https://www.python.org/downloads/")]], [
        proposal(STABLE),proposal(DATED_CURRENT,"supported")], ["outdated","supported"], {}
    yield "mixed-uncertain", [PYTHON,CURRENT], [[row(STABLE)],[]], [proposal(STABLE)], ["outdated","uncertain"], {}
    yield "mixed-429-stops", [PYTHON,CURRENT], [[row(STABLE)]], [ServiceError("Upstream HTTP 429",http_status=429)], [
        "uncertain","uncertain"], {"status":"upstream_error","search_calls":1}
    yield "http-429-at-extraction", [PYTHON], [], ServiceError("Upstream HTTP 429",http_status=429), [], {
        "status":"upstream_error","search_calls":0}
    yield ("two-official-fetches", [PYTHON,NODE], [[row("Python release information.")],
           [row("Node.js release information.","https://nodejs.org/en/blog/release/v22.0")]], [
           proposal(STABLE,source="s2"),
           proposal("Node.js 22.0 was released on May 1, 2025 as a stable release.",source="s2")],
           ["outdated","outdated"], {"source_retrieval_calls":2})


def evaluate(case):
    name, texts, searches, decisions, expected, checks = case
    llm, search, retriever = Mock(), Mock(), Mock()
    extraction = {"claims":[{"text":t,"subject":t.split()[0] if t[0]!="T" else "Python",
                             "time_sensitive":t!=HISTORY,"query":"release evidence"} for t in texts]}
    llm.complete.side_effect = [decisions] if isinstance(decisions, ServiceError) else [extraction,*decisions]
    search.search.side_effect = [{"results":r,"usage":{"credits":0}} for r in searches]
    retriever.retrieve.side_effect = lambda url, _: {"url":url,"content": STABLE if "python" in url else
        "Node.js 22.0 was released on May 1, 2025 as a stable release."}
    report = Verifier(llm,search,retriever=retriever if name=="two-official-fetches" else None,
                      clock=lambda:CHECKED).verify(" ".join(texts))
    actual = [c["verdict"] for c in report["claims"]]
    decisive = [v for v in expected if v in ("outdated","supported")]
    sensitive = [v for v in expected if v!="not_checked"]
    observations = {**report["metrics"],"status":report["status"]}
    ok = (actual==expected and all(observations.get(k)==v for k,v in checks.items())
          and report["coverage"]==(round(len(decisive)/len(sensitive),3) if sensitive else 0)
          and report["freshness_score"]==(round(100*decisive.count("supported")/len(decisive)) if decisive else None))
    return {"case":name,"pass":ok,"expected":expected,"actual":actual,
            "observed":{k:observations.get(k) for k in checks}}


def main():
    results = [evaluate(c) for c in cases()]
    passed = sum(r["pass"] for r in results)
    print(json.dumps({"provenance":"synthetic evidence and scripted provider responses",
                      "passed":passed,"failed":len(results)-passed,"cases":results},indent=2))
    return int(passed!=len(results))


if __name__ == "__main__":
    raise SystemExit(main())
