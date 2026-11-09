# Benchmark plan and reproducibility

The [final benchmark report](../docs/BENCHMARK_REPORT.md) covers the current scripted regression suite. The earlier backend-freeze milestone recorded 140 Python tests, 10 race-checked native Go tests, 8 protocol cases, 4 acquisition scenarios and 11 full native gateway fixture checks. Complete-window selection repairs the saved targeted-source quote failure offline. The original live report remains uncertain. Gateway smoke and acquisition timings come from synthetic fixtures. See the [measured live outcomes](../docs/LIVE_RESULTS.md) for separate historical runs.

`python -m benchmarks.acquisition` runs four offline acquisition scenarios, 25 times each, and writes `acquisition-results.json`. It measures local planning, parsing and validation with mocked HTTP, search and models. The live benchmark defaults to one fetch across the run and reports `source_retrieval_calls` and per-report `metrics.timings_ms`. The [acquisition design note](../docs/BOUNDED_ACQUISITION.md) documents the earlier rollout and [integration proof](../docs/INTEGRATION_PROOF.md) shows a captured official-page fetch.

The latest supplied release-index live run **was** a semantic override: Gemini proposed outdated but quoted undated, truncated official snippets. See `../docs/RELEASE_INDEX_EVIDENCE_PATH.md` for the complete retained evidence, the missing four-result trace, and diagnostic-only changes. Five new regressions replay this failure without APIs. The earlier run in `../docs/RETRIEVAL_ABSTENTION.md` was a model-proposed abstention. Neither saved run supplies sufficient dated stable-release proof; controlled positive fixtures are not measured live recall.

## Historical replay inputs

`benchmarks.semantic_replay` re-applies the semantic guard to captured reports. `benchmarks.replay` reclassifies recorded outcomes for failure analysis. Both run offline and require a separately supplied, compatible local benchmark capture. Their default input paths (`work/full-live-check.json` and `benchmark-live.json`, respectively) are ignored and absent from a clean clone. Pass your own capture with `--input`. Use `--output` to save the replay separately from the original.

From a clean clone, `python -B -m benchmarks.final_offline` and the [saved frontend demo fixtures](../frontend/fixtures/manifest.json) are self-contained. They need no historical captures or provider credentials.

The [6 November false-fresh regression](../docs/FALSE_FRESH.md) is an example of semantic replay. The saved supported verdict now abstains. That removes a false-fresh result but still misses the independent stale label.

## Availability versus quality (current metric semantics)

Upstream/API failures are not normal extraction misses. Reports now carry `extraction.status`, safe staged errors and HTTP status where available. Quality metrics include only evaluable observations; unavailable-only runs have null accuracy/recall, with availability and end-to-end success explicitly zero. A valid empty claim list can still be a genuine miss; zero-search timeless cases remain evaluable. Deliberate budget skips don't score detector quality. Search/judge errors do not erase successful extraction measurements. Inspect evaluable counts and failure counts alongside every conditional quality metric.

For an existing local capture at `benchmark-live.json`, run `python -m benchmarks.replay --input benchmark-live.json --output work/extraction-failure-analysis.json`. The [recorded first-case failure](../docs/EXTRACTION_FAILURE.md) was HTTP 429. Published historical scores retain the original metric definitions.

Current measured continuation outcomes and limits are in `../docs/LIVE_RESULTS.md`. Public selected metrics/URLs are in `live-results.json`; native transport's failed semantic review is in `native-live.json`. Raw payloads remain in ignored `work/`. No complete final-revision accuracy study was possible because Gemini returned HTTP 429.

## Offline protocol regression

`python -m benchmarks.run` checks 8 synthetic cases: changed version, supported price, missing evidence, historical claim, timeless claim, conflicting evidence, old-only evidence and no results. `fixture-results.json` records results, call counts and processing latency.

Both model and search are scripted. Passing these cases demonstrates wiring and regression behavior only. The reported sub-millisecond latency is local fixture processing, not Tavily/model performance. No model accuracy or credit-saving claim can be derived from this run. Separate tests exercise malformed output, fabricated citations, failure handling and the actual HTTP service.

## Native cost

`go test -run '^$' -bench BenchmarkDisabledHook -benchmem ./...` in `integrations/bifrost` measures opt-out overhead. Record compiler, CPU and exact source commit with results. It does not measure the whole gateway or enabled verification. The loader smoke test executes Bifrost's real loader, native hooks and Python service, with synthetic evidence; it is not a full provider-to-gateway network test.

`python3 -m scripts.gateway_smoke`, after `bash scripts/build-gateway.sh`, additionally tests the real upstream HTTP server with a local scripted provider. It exercises generation, extraction and judging through Bifrost and checks report delivery, opt-out, streaming rejection, recursion prevention and explicit unavailable results. Its local fixture timing is not live API performance. See `gateway-smoke.json` and `docs/VALIDATION.md` for the observed run.

## Live smoke set

`python -m benchmarks.live --env-file .env` uses real Bifrost model calls and Tavily. It writes ignored `benchmark-live.json`, including full cited reports, case agreement, stale precision/recall, false-fresh count, median latency and actual Tavily credit usage when available. Missing usage is flagged rather than represented as known zero cost. No dollar amount is guessed; LLM costs remain in Bifrost's own usage accounting.

The original four-case set remains in `live-cases.json` for reproducing the baseline. The default is now the eight-case `reliability-cases.json`: stale/current release series, timeless and historical controls, private/ambiguous claims, misleading input citation and mixed claims. Labels were set against official Python pages before this smoke run. This developer-selected, predominantly Python set is neither independent nor representative enough to establish general quality. Missing and extra extracted claims count in scoring; extra supported claims count as false-fresh. A nonofficial input-link warning is a domain assessment, not proof that a page is fabricated.

Default limits: eight cases, eight search attempts, twenty-second pacing between cases, no retries, stop after 429/503, and partial output saved after each case. Use `--max-cases`, `--max-searches` and `--interval-seconds` to reduce work. Reported model tokens may omit failed calls and are not a complete billing estimate. Publication metadata is not an effective-date guarantee. Provenance rate measures exact quote/source membership only; manual entailment review remains necessary.

`llm_calls` counts logical client requests to Bifrost. FreshnessGuard does not retry; any retries performed by the existing gateway's own policy are not reflected in this counter. Provider credentials and gateway policies were not changed during the continuation.

Conflict, future-dated source, malformed JSON, hallucinated citation and truncated-answer categories are covered by controlled regression tests. Live contradictory evidence was not established; don't silently count these fixture checks as live search evaluations.

## Submission quality benchmark (remaining)

Before recording accuracy claims, build an independent 30-answer set: 10 stale claims, 10 supported current claims, 5 historical/timeless controls and 5 conflicting/no-evidence cases. Use multiple domains, entity collisions, pricing tiers, prerelease-versus-stable versions, date ambiguity, negation and source prompt injection. Freeze expected labels and dated primary sources before running. Keep this set separate from prompt-tuning examples.

Report claim-extraction precision/recall separately from verdict quality. Score missed sensitive claims as misses, rather than dropping them from the denominator. Report stale precision/recall, false-fresh rate, abstention coverage, citation validity, p50/p95 total latency, model calls/tokens and actual Tavily credits. Compare the same answers against an always-trust-model baseline and a search-every-claim policy; count real calls, not hypothetical savings. Have a human inspect whether quoted evidence entails the correction. Run twice to expose retrieval variability. Do not call a fixture score “accuracy.”

## Final reliability regression suite

Run `python -B -m benchmarks.final_offline` from the repository root. It emits JSON with each case's expected and actual verdicts and exits with a failure code on any mismatch. The same 25 synthetic cases passed 20/25 before the hardening and 25/25 after it. The cases cover release proof, independent claims and budgets, irrelevant results, fabricated quotes, historical claims, missing evidence, HTTP 429 and timeouts. Some version and date inputs are deliberately scripted. This suite measures behavior on fixed inputs with mocked services. Live accuracy, current provider compatibility and latency are outside its scope.
