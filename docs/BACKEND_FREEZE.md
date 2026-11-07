# Backend feature freeze — 7 November 2026 (IST)

The final backend scope is limited to the three requested fixes below. New backend feature development stops here; React/TypeScript/Tailwind fixture-first integration is the next workstream. Security defects or reproducing correctness regressions may still require maintenance. No paid live requests, credential-file changes, pushes or publishing occurred.

## Complete, exact evidence windows

`freshnessguard/semantics.py:complete_release_quotes` deterministically selects a complete adjacent source span only for an already grounded **outdated** latest-version decision. It never promotes uncertain to outdated or applies historical release context to supported verdicts.

The original quote must first pass existing citation/exact-substring checks and contain the relevant entity and one unambiguous full version. The same authoritative source must contain a parser-eligible contiguous dated stable-release window, at most 800 characters and at most three adjacent paragraphs. Date-only paragraphs must explicitly label release/as-of/effective time; intervening unrelated paragraphs and repeated/ambiguous anchors are refused. Nothing is stitched, paraphrased or supplied from publication/retrieval metadata. A single-sentence release/date statement is also eligible. Future, preview, LTS/scope, authority and withdrawal/conflict rules remain enforced by the unchanged final semantic validator.

`proposed_assessment` retains the original model quote. Final `quotes` contain the selected exact source substring. `quote_windows` records original/selected text, source ID, method and start/end Unicode-code-point offsets. Original source objects, URLs, body/text hashes and model correction excerpts remain unchanged. No second model call, search or retrieval is introduced.

The saved targeted-source failure is reproduced in `tests/fixtures/targeted_source_quote_failure.json`. The live model's short quote is selected into this actual same-source excerpt:

```text
Release date: Oct. 7, 2025

This is the stable release of Python 3.14.0
```

It passes the unchanged final guard as outdated in offline replay. The original live benchmark remains uncertain and unmodified. This is not a new live success or an exact-current-Python-version answer.

## Authenticated API redirects

`freshnessguard/clients.py` uses a dedicated opener whose redirect handler rejects redirects before constructing another request and closes the redirect response. All API redirects are rejected, including same-origin redirects. No authorization/virtual-key headers or request payload reach a Location target. Errors contain the fixed `api_redirect_blocked` code, not URLs, headers, bodies or credential values.

Tests cover 301/302/303/307/308 through both synthetic cross-host request construction and actual local redirect/destination servers. The destination receives zero requests. Existing HTTP error/timeout tests and client mocks remain compatible. The separate official-page retriever continues to enforce its existing no-redirect/SSRF policy.

## Native verifier hardening

`integrations/bifrost/main.go` rejects all verifier redirects and explicitly disables proxy use for its loopback verifier transport. Redirect, timeout, HTTP/read/size and invalid-report failures preserve the provider's original completion and usage. They attach a fixed unavailable envelope with safe `error.stage/category/code` plus status/error headers. Invalid original JSON cannot safely receive a merged envelope, so it gets explicit unavailable/error headers instead.

`integrations/bifrost/validation.go` validates schema-v1 report objects, required arrays/metrics, timestamp, score/coverage ranges, known statuses/verdicts, evidence field shape, exact source/quote/correction correspondence, expected choice indices and original answer identity. A text completion cannot accept `checked` with empty reports, unknown/missing choice indices, changed original text or malformed evidence. Duplicate choice reports are refused. Truncated responses require incomplete reports. Legitimate no-text responses may return no_text_to_check with empty reports. Nested unavailable/upstream errors remain explicit; transport checked is never a freshness verdict. Semantic truth remains the Python validator's responsibility.

`scripts/build-gateway.sh` now resolves the bootstrap module path through generated, version-specific workspace replacements for the pinned upstream core requirements. It leaves repository module files unchanged and builds matching gateway/plugin artifacts. This is a reproducibility repair needed for the final offline gateway check, not a gateway architecture change.

## Files and validation

Implementation: `freshnessguard/clients.py`, `engine.py`, `semantics.py`; native `main.go`, new `validation.go`, `main_test.go`; `scripts/build-gateway.sh`, `scripts/gateway_smoke.py`.

Regressions: new `tests/test_final_backend.py` and its observed-evidence JSON fixture. Generated protocol/acquisition/gateway benchmark artifacts are refreshed without treating them as live accuracy results.

Validation record:

- 140 Python tests pass; new tests reproduce complete-window selection and reject unrelated/missing/future/preview/ambiguous evidence, invented quotes and supported-claim promotion; redirects never reach a destination.
- 10 top-level native Go tests pass under `go test -race`, including redirect and malformed-envelope subcases. The loader Go module also compile-checks with race instrumentation; it has no test files.
- All 8 synthetic protocol cases and 4 acquisition scenarios (25 iterations each) pass, with zero actual paid calls. Acquisition scenarios retain two logical mocked model calls and at most one mocked GET.
- Matching native plugin/gateway builds and the full synthetic Bifrost HTTP fixture run validate opt-out, extraction/judgment through Bifrost, cited report serialization, immutable original answer/usage, recursion protection, streaming refusal, truncated answers and structured fail-open metadata.
- Python compile checks pass; four frontend JSON fixtures pass local shape and exact-quote/source checks. The TypeScript contract is prepared, not a compiled React application.

The native build uses the existing pinned upstream checkout/toolchain and cached modules with GOPROXY/GOSUMDB disabled. Work-directory test harnesses keep machine-specific paths out of repository module files. Local synthetic server tokens are ephemeral test values; no user credential file is read or rewritten.

## Frontend handoff

`docs/FRONTEND_CONTRACT.md` freezes backend/API and UI semantics. `frontend/contract/types.ts` provides TypeScript bindings. `frontend/fixtures/manifest.json` describes four local reports: mixed synthetic claims, the unchanged saved-live abstention, its explicitly labeled offline repaired replay, and synthetic unavailable extraction. Offline replay metrics report zero new API calls and do not borrow the failed live run's token/latency numbers.

Build the React + TypeScript + Tailwind premium dark cybersecurity workbench against these fixtures first. Keep provider/Tavily/verifier credentials server-side, use a future same-origin adapter, escape evidence text, and display null/zero coverage, abstention and native failures honestly. No React app, server adapter or live frontend integration is implemented in this backend-fix turn.

## Remaining risks and limits

- Final live stale detection and final native live behavior are unmeasured; no new paid validation was run. Historical failed benchmarks stay failed.
- Deterministic windows are bounded English/date heuristics, not general entailment. Missing/ambiguous dates or unavailable pages still abstain. A model that proposes uncertain is not overridden.
- Input token volume still includes full selected source text; prompt compression, caching and model changes are outside the freeze.
- Rejecting legitimate redirects may reduce availability; it deliberately prevents credential/payload forwarding. The new client behavior needs to remain enabled in future adapters.
- Native envelope checks establish structure/provenance, not independent semantic truth. Streaming, broader SDK endpoints, public/multi-tenant deployment and browser authentication changes remain out of scope.
- Frontend fixtures can contain saved live source text and historical metrics. Their manifest provenance must stay visible; an offline repaired fixture is not measured live success.
