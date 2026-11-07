# Targeted live diagnosis and backend freeze plan

Historical diagnosis below. The three blockers were subsequently fixed and tested offline on 7 November; see `BACKEND_FREEZE.md` for the final changes and `FRONTEND_CONTRACT.md` for the next workstream. The original measured live result remains unchanged.

Source: unchanged `work/targeted-source-single-live.json`, checked at `2026-11-06T18:02:32.934466+00:00`. This investigation used saved data, local code inspection and offline construction/replay only. No paid calls, credential changes, backend implementation changes or pushes were made.

## Seven answers

1. **Selected URL:** `https://www.python.org/downloads/release/python-3140/`, discovered as the literal reference `python.org/downloads/release/python-3140/` in source s1. It became fetched source **s5**.
2. **Retrieval succeeded:** `source_retrieval.status=ok`; 277.2875 ms, 53,931 HTML bytes, 6,076 extracted characters, no text truncation. The included text matches its saved SHA-256. Raw HTML was not retained, so its body hash cannot independently be recomputed here.
3. **Actual sufficient evidence:** the saved text contains this exact contiguous excerpt:

   ```text
   Release date: Oct. 7, 2025

   This is the stable release of Python 3.14.0
   ```

   The page also notes that 3.14.0 was superseded by 3.14.10. That does not invalidate the historical stable-release counterexample and does not prove what is latest today. The unrelated fallback-script notice did not prevent extraction of the dated release fact.
4. **Gemini proposed outdated**, cited s5, and quoted only `This is the stable release of Python 3.14.0`. Its correction was the exact substring `Python 3.14.0`. It omitted the immediately adjacent release date despite the existing prompt requiring it.
5. **Semantic validation correctly rejected the quote for `explicit_release_or_effective_date_missing`.** Full-source parsing accepted one release fact: `observed_release_witnesses=[{source_id:s5, version:3.14, date:2025-10-07, date_kind:release_date}]`. Quoted `release_witnesses=[]`. Source discovery and entailment succeeded; the failure boundary is model-selected quote completeness. No age-limit, authority, SSRF, extraction or retrieval error caused this result. Zero decisive primary sources counts final accepted verdicts, not the number of official sources retrieved.
6. **Judgment was the slowest stage:**

   | Stage | Seconds |
   | --- | ---: |
   | Claim extraction | 4.017 |
   | Tavily search | 2.737 |
   | Official-page retrieval | 0.277 |
   | Gemini judgment | 4.806 |
   | Semantic checks | 0.079 |
   | Total | 11.919 |

   The two model stages consumed about 74% of total time. Retrieval was about 2.3%. Rounded stage values do not include all local bookkeeping.
7. **Token usage was input-heavy:** 6,546 prompt + 236 completion = 6,782 tokens, aggregated across both model calls. There were five evidence sources with 11,142 content characters: four overlapping snippets totaling 5,066 plus the 6,076-character fetched page. The full page includes navigation, feature descriptions, a poem and artifact/hash tables unrelated to the release proof. Both system prompts, JSON source metadata, provenance fields and escaped text add input. This supports prompt/evidence volume as the main cost driver, not a large generated answer. Per-call token counts and provider reasoning-token details are not retained, so an exact extraction-versus-judge allocation cannot be recovered. Do not infer 6,782 output tokens or extra model calls.

## Offline proof check

`work/targeted-source-offline-diagnosis.json` records a human-selected exact excerpt replay. With the date-plus-stable excerpt above, unchanged `_apply_decision` and semantic validation return **outdated**, with the cited release witness dated 2025-10-07. This is not a new Gemini result, a benchmark relabeling or a successful live rerun. The original live result remains uncertain. No backend code was changed to force a verdict.

## Critical findings and freeze gates

**Correctness release blocker:** complete proof is now available, but the judge can choose a date-free fragment and the backend abstains. The guard is working; end-to-end stale detection remains unreliable. A narrowly scoped maintenance fix should make the model select a complete validated witness, without another judgment call or looser citation rules. Candidate: provide deterministic existing-parser witness spans as untrusted evidence selections, retain exact source-span provenance, and require the judge to select the complete span. Do not silently widen a quote, fabricate a date or infer acceptance from a URL. Save this actual failure as a regression first; both incomplete and complete quote cases must pass their expected outcomes.

**Confirmed API-client security defect:** `freshnessguard/clients.py:post_json` uses the default urllib redirect handler for authenticated Tavily/Bifrost requests. An offline `HTTPRedirectHandler.redirect_request` construction with synthetic Authorization/x-bf-vk headers and a cross-host 302 retained both headers. No network was used. Thus an upstream redirect could expose credentials. This is a conditional vulnerability, not evidence that the saved run leaked anything. The new official-page retriever separately rejects redirects and is not affected. Reject API redirects before following them; test 301/302/303/307/308, verify no second request and no secret-bearing exception/log output. This is a security fix within the freeze, not a new feature.

**Native integration security/correctness gaps:** `integrations/bifrost/main.go` uses an `http.Client` with no `CheckRedirect`; validating only the initial loopback service URL does not constrain redirected destinations. A 307/308 could forward completion data to a different destination. Configure the verifier client to reject redirects and bypass environment proxies explicitly. Its envelope validation also accepts `status=checked,reports=[]` for a text completion, so a malformed service response can look checked without any verification report. Validate report shape and choice correspondence, expose incomplete/unavailable states accurately, and ensure the frontend never equates transport `checked` with claim `supported`. These are findings from local code, not observed failures/exploits in this benchmark.

No evidence of a source-fetch SSRF bypass, forged decisive citation, extra paid call or false-fresh verdict was found in this saved run. This is a bounded review, not a comprehensive security audit. Existing opt-in/recursion headers are not an enforcement boundary for mandatory verification.

## Freeze and next work — plan only

### 1. Freeze new backend features now; allow only named release blockers

- Keep schema version 1 and existing `/verify` and `/annotate` behavior; document the additive retrieval/timing fields.
- No new providers, search strategies, retries, model passes, streaming, caching, crawling, scoring changes or expanded authority registry.
- Resolve only the complete-witness citation regression, authenticated API redirects, native verifier redirects/envelope validation, and any reproducing security regressions. Preserve strict dates/channel/scope checks.
- Run Python tests and existing synthetic/acquisition benchmarks. Retain the original failed live result. No paid rerun until these gates are complete and a new bounded validation is explicitly requested.

### 2. Build the focused React frontend against frozen fixtures

- React + TypeScript single-screen workbench: answer input, Verify action, original answer, claim verdicts, exact quotes, source URLs, corrections and visible reasons for abstention.
- Show coverage beside score; null score is unavailable/unassessed, never 0 or 100 by default. Show retrieval state, observed-versus-cited witnesses, stage timings and reported model/search/GET usage in expandable details.
- Start with saved failed-live and clearly labeled synthetic supported/outdated/uncertain fixtures. No fake live success or auto-triggered paid request on page load.
- Render all answer/evidence text as escaped text; no raw HTML/Markdown execution. Validate clickable HTTPS links. Never put Tavily/provider/verifier credentials in the React bundle, browser storage or captured report.
- Use a same-origin server-side adapter to the authenticated loopback verifier/gateway. The browser does not call Tavily/Gemini directly; server-side secrets stay in environment. Keep the interface local until authentication/origin protections and deployment boundaries are reviewed. Avoid permissive CORS as a shortcut.
- UI checks: unavailable versus uncertain, null metrics, busy/timeouts, malformed response, keyboard accessibility and exact original-text preservation. Deliver this scope before adding charts, accounts or extra pages.

### 3. Correct and validate the native Bifrost path

- Keep the existing final HTTP transport-hook seam, pinned inspected Bifrost commit, matching Go toolchain/module graph and real shared-object loader. Do not invent an SDK seam or treat a standalone Python request as native validation.
- Apply the native maintenance fixes above. Preserve opt-out zero-work behavior, recursion prevention, answer/usage/tool-call preservation, non-streaming limits, content-length handling, deadlines and explicit fail-open status.
- Run native Go race tests, loader smoke and the full Bifrost HTTP gateway fixture tests against final backend code, including the new retrieval states and failed quote-completeness report.
- For the reproducible Windows demo, use the existing WSL/Linux native build with gateway and verifier colocated for loopback behavior. Keep the historical Windows/WSL bridge labeled as test infrastructure, not the production integration. Do not expose a token-bearing verifier to the browser or LAN to work around networking.
- Freeze native configuration/report contract after those checks. The UI reads nested report outcomes; `x-freshnessguard-status=checked` alone is never displayed as fresh/supported.

### 4. Submission rehearsal

Offline integrated UI/native demo first. Then a separately authorized, single bounded live verification on final code; inspect exact dated quote and native serialization before any broader evaluation. Present known failures and measured coverage honestly. Record/export a demo without secrets. No publishing, push or submission is included in this plan.

This turn changes documentation and writes an offline diagnosis artifact only. Existing 130-test results are historical from the implementation turn; no new full test pass is claimed for this read/replay investigation.
