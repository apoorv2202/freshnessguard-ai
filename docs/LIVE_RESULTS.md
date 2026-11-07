# Measured live outcomes

## Final browser smoke run — 8 November 2026 (IST)

One submission through the Vite adapter checked “The latest stable Python release series is 3.11.” The schema-v1 report returned HTTP 200, status `review_required`, one `outdated` claim, 100% coverage, and freshness 0/100. Gemini cited the full candidate quote containing the release date and stable-release statement from the [official Python 3.14.0 release page](https://www.python.org/downloads/release/python-3140/). The verifier accepted that exact source span.

Browser-facing latency was 9.66 seconds. Bifrost recorded two Gemini calls totaling 6,669 tokens and zero retries. Tavily reported one search and one credit, and the verifier fetched one official page. This run exercises the paste-answer path through the gateway. The native post-hook has separate test results below.

## Earlier live runs — 5 November 2026

These are small smoke runs, using `gemini/gemini-3-flash-preview`, the existing authenticated Windows Bifrost gateway and real Tavily searches. They use overlapping developer-selected examples and different code revisions. They are **not an A/B study or a general accuracy benchmark**. Expected Python release-series labels were independently checked against [Python's downloads page](https://www.python.org/downloads/) and [version status](https://devguide.python.org/versions/). Historical release control references [Python 3.11.0](https://www.python.org/downloads/release/python-3110/).

| Run | Completed cases | Case agreement | Reported Tavily credits | Outcome |
|---|---:|---:|---:|---|
| Original four-case Bifrost smoke set | 4/4 | 2/4 | 3 | Stale and current module claims abstained; timeless and nonexistent-entity controls matched |
| Official-source reliability run | 5/8 | 1/5 | 2 | Current Python series supported with official sources; stale claim quote rejected; timeless JSON truncated; private claim omitted; stopped on HTTP 429 |
| Paced run after quote/JSON changes | 2/8 | 0/2 | 1 | Stale claim abstained; next extraction hit HTTP 429, so run stopped |
| Native live gateway roundtrip | 1 | Failed semantic review | 1 | Real Gemini generation was truncated to “The latest stable”; a secondary .NET source incorrectly produced supported |

Total observed search attempts: **7**, with **7 reported Tavily credits** across these runs. The original benchmark conflated model failure with incomplete search billing, so the reported total is not a billing guarantee. Logical model requests to Bifrost: **20**, including one native generation. Bifrost's own upstream retry policies are outside this counter; the number is not a count of actual Gemini backend attempts. Failed/timed-out requests may lack token usage. User-run calls before this continuation are not counted.

The baseline median was about 14.28 seconds; the interrupted reliability run about 12.01 seconds; the paced two-case run about 15.15 seconds. The native roundtrip was 13.94 seconds including WSL interop and existing gateway routing. Different inputs and failures make these timings unsuitable for speedup claims. Raw per-case latency, confusion, missing claims, coverage and reported tokens are in `benchmarks/live-results.json`; reviewed native evidence is in `benchmarks/native-live.json`.

## Reliability findings and fixes

1. **Fragment false positive:** Native generation's short token cap produced an incomplete fragment. Added grounded concrete subjects to extraction; gateway responses marked `length` or `content_filter` now skip verification with `incomplete`, zero score and zero search calls. The real gateway regression verifies that behavior. The Windows test bridge now requests minimal reasoning and a larger bounded generation budget.
2. **Official-source preference:** Python/Node.js/Bifrost policies restrict search domains and require an official decisive source. GitHub sources must belong to `maximhq/bifrost`. This is a small explicit registry, not an authority classifier for all entities.
3. **Quote drift and unsupported correction:** Exact source quotes remain mandatory. Whitespace-only differences can resolve back to exact source spans. Corrections must themselves be exact cited excerpts. Mismatched citations, fabricated wording or corrections abstain with a visible validation reason.
4. **Conflicts and dates:** Unresolved conflicts and future-dated decisive sources abstain. Publication metadata is retained separately from retrieval time. Search caches and old page-creation timestamps can still be misleading; semantic temporal interpretation remains model-dependent.
5. **JSON and provider failures:** Duplicate keys, non-finite values, non-object output, truncation and extra prose fail clearly. No retries. Known Tavily usage survives a later model failure. The configured Gemini Flash request uses minimal reasoning; this setting does not grant quota or guarantee valid JSON.
6. **Benchmark misses:** Missing and extra claims are now counted; a multi-claim answer cannot silently become a one-claim success. Unmatched supported claims count as false-fresh predictions. Provenance rate checks source membership, not semantic entailment.

Conflict, future-date, fabricated-citation and fragment guards were tested with controlled fixtures. Actual contradictory live retrieval was not established. The last grounded-subject/truncation changes were added after the interrupted live runs and remain **offline/gateway-fixture tested only**.

## Native status

Actual OSS plugin loader: passed. Complete native HTTP gateway with scripted provider: 10 checks passed. Real Gemini + Tavily transport through native post-hook: observed, but **failed semantic review**. The corrected native live end-to-end test is prepared and not rerun after repeated quota responses. Do not present native live accuracy as working until that test passes with a complete meaningful answer and human-reviewed evidence.

The corrected native live roundtrip and a broader independent evaluation remain open.
