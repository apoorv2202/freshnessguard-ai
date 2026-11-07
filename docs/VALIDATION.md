# Validation record

## Final fixes and backend freeze — 7 November 2026

140 Python tests, 10 top-level native Go race-checked tests (including redirect/envelope subcases), 8 synthetic protocol cases, 4 acquisition scenarios and 11 complete Bifrost HTTP gateway fixture checks pass. The loader Go module compile-checks with race instrumentation and has no test files. The final gateway fixture took 114.71 ms on local scripted services; this is not live performance. Complete-window selection repairs the saved short-quote failure offline without relaxing semantic validation. Authenticated API/native redirects are refused and malformed native report envelopes fail open with safe structured errors. No paid calls, credential changes or pushes. See `BACKEND_FREEZE.md` and `FRONTEND_CONTRACT.md`; no final live success is claimed.

## Bounded source acquisition — 6 November 2026

130 Python tests, 8 synthetic protocol cases, and 4 acquisition scenarios (25 iterations each) pass. A mocked end-to-end official-page fetch/parser/judge/semantic check accepts a dated newer stable release; missing dates, previews and fabricated quotes still abstain. Security tests cover destination allowlists, DNS/IP pinning, redirects, deadlines, size/type limits and safe text extraction. Structured timings include extraction/search/retrieval/judgment/semantic/total stages. See `BOUNDED_ACQUISITION.md` and `benchmarks/acquisition-results.json`. No paid calls; no Go source changed or native checks repeated. Live retrieval effectiveness remains unmeasured.

## Release-index evidence diagnosis — 6 November 2026

105 Python tests and all 8 synthetic cases pass. The supplied release-index live run proposed outdated, then failed semantic validation: neither cited quote provided a dated stable-release witness. All four retained judge sources and exact quotes are documented in `RELEASE_INDEX_EVIDENCE_PATH.md`; four other returned candidates were not saved. Added bounded selection metadata and parser rejection diagnostics, with five observed-evidence regressions. No paid calls or acceptance-rule changes; Go code is unchanged and native checks were not repeated in this diagnostic-only investigation.

## Latest retrieval/dated-release fix — 6 November 2026

100 Python tests and all 8 synthetic cases pass. The saved model itself proposed uncertain after receiving Planet Python's Django/PyCharm feed and a Python 3.9.7 artifact snippet; the semantic guard did not reject a proposed outdated verdict. A bounded release-index retrieval plan and a separate authoritative dated newer-stable-release proof path are implemented and regression-tested. Missing original evidence remains uncertain; no new paid live checks were run. Details and next single-case command are in `RETRIEVAL_ABSTENTION.md`.

## Latest false-fresh semantic fix — 6 November 2026

78 Python tests, all 8 synthetic protocol cases, 6 native Go race-checked tests and 10 complete synthetic gateway checks pass. Saved live evidence is replayed offline as uncertain rather than supported. This removes a false-fresh verdict but remains a missed stale detection against the benchmark's independent outdated label. No new paid live requests were made; source dates, authority, scope/channel constraints, query changes and conservative limits are detailed in `FALSE_FRESH.md`. Prior live results below remain historical.

## Latest extraction-error fix

54 Python tests and all 8 synthetic protocol cases pass. The saved first-case failure is confirmed as HTTP 429, not a genuine extraction miss. Typed errors and availability-aware metrics are validated offline, including saved-report reclassification and a mocked one-request benchmark stop. No live model/search calls were made. See `EXTRACTION_FAILURE.md`; previous live/native outcomes below remain historical and are not rerun or upgraded to success by this fix.

## Continuation results — supersede the initial setup record below

37 Windows Python tests pass; 8/8 synthetic protocol cases pass; 6 native Go tests including timeout and malformed report handling pass with race checking. The actual Bifrost loader succeeds, and 10 complete native gateway fixture checks pass, including skipping truncated provider answers with zero research calls. Existing Windows services and all provider credentials were preserved. No push, commit, deployment or submission was performed.

Live runs and failed experiments are published in `docs/LIVE_RESULTS.md`, `benchmarks/live-results.json` and `benchmarks/native-live.json`. Standalone live connectivity exists. The native live transport reached real Gemini/Tavily, but a truncated fragment received an unrelated supported verdict; it is classified as a failed live validation, not success. That defect is now regression-tested. HTTP 429 stopped further live work; the corrected native live run and full final-revision benchmark remain outstanding. Captured supported/uncertain HTML examples are labelled with their earlier revision provenance.

Source-policy, exact-excerpt correction, subject validation, publication-date handling and structured-JSON checks were added without changing the architecture. The Gemini request asks for minimal reasoning and a bounded 2,800-token output budget; runtime quota/support remain external constraints. The latest fixes are tested offline and through the real gateway with controlled provider output; do not infer new live accuracy measurements from them.

## Initial setup record (historical)

Run date: 5 November 2026 (IST). Source reviewed: Bifrost `afdce01b50a78199f59e38117cd4d5952d038b07`. Development host: Windows; native builds and gateway checks ran in existing Ubuntu WSL2. Go 1.27.3 and Ubuntu GCC were made available for native compilation. Docker was not needed. All temporary services were stopped after the checks.

| Check | Observed result | What it establishes |
|---|---|---|
| Windows Python 3.13 unit and HTTP tests | 19 passed | Validation, citation provenance, abstention, budget, immutable answer, HTTP auth and environment-file handling |
| Native Go tests | 4 passed | Adapter roundtrip, streaming/multi-choice rejection, opt-in/recursion bypass, explicit unavailable reports |
| Native `go test -race` | Passed | No race detected in the exercised tests; not a general proof of concurrency safety |
| Disabled post-hook benchmark | 4.754 ns/op, 0 B/op, 0 allocations/op | Local bypass cost on Intel i5-13420H; not whole-gateway overhead |
| Synthetic protocol cases | 8/8 passed | Scripted regression conformance, not model accuracy |
| Bifrost OSS `SharedObjectPluginLoader` smoke test | Passed | Real native plugin loading and execution with the Python service |
| Full dynamically linked Bifrost HTTP server + local provider | 9 checks passed | End-to-end generation, extraction/judging via Bifrost, cited reports, unchanged answer, recursion prevention, streaming rejection and failure behavior |
| Full gateway fixture timing | 29.21 ms | One local scripted run; not live Tavily/model latency |
| Git credential exclusion | `.env` and `work/` ignored | Credentials and compiled assets excluded from source packaging |
| Remote CI workflow | Added, not run remotely | Cross-platform test and native build instructions are present |
| Live model + Tavily accuracy/cost | Not run | User credentials and model configuration are still required |

Artifacts: `benchmarks/fixture-results.json`, `benchmarks/native-bypass.txt`, `benchmarks/gateway-smoke.json`, `demo/report.json` and `demo/report.html`.

The full gateway test uses a scripted OpenAI-compatible local provider. Extraction and judgement requests use the real `BifrostLLM` HTTP client and pass back through the real Bifrost server. Tavily evidence is supplied by the synthetic fixture search client. Separate wire-contract tests validate Tavily's actual request shape, but no live Tavily request has been made. No claim of real-world precision, recall, latency or cost savings is supported yet.

The four-case live smoke corpus and a broader independent benchmark plan are prepared. Submission readiness also requires official problem-statement confirmation, a live recording and publication of the repository. This task has not contacted maintainers, opened a PR, deployed a public service or submitted the entry.
