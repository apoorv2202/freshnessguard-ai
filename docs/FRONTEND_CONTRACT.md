# Backend frozen: React frontend integration contract

Backend feature development is frozen after the three release fixes in `BACKEND_FREEZE.md`. The React frontend supports saved demos and an opt-in local development adapter for live verification.

## Product and visual scope

One responsive, premium dark cybersecurity workbench: near-black/slate surfaces, restrained cyan accents, clear typography, subtle borders and readable status colors. Use green for supported, amber/red for outdated, neutral amber for uncertain, and a distinct unassessed state for not_checked. Always pair colors with text/icons. Avoid decorative threat counts or invented scan activity.

Primary flow: paste an AI answer (1–16,000 characters), select an explicitly labeled fixture or press Verify in a later live-enabled mode, show loading, then preserve the original answer beside claim cards. On narrow screens stack input, summary and claims. Provide keyboard focus, semantic buttons, accessible status announcements and readable contrast; respect reduced motion.

Each claim displays its final verdict and reason, exact source quotes, linked source title/URL, any exact correction excerpt, and check time. Display freshness score and coverage together. Expandable evidence details show proposed versus final verdict, original versus selected quote windows, retrieval status, semantic rejection reasons and stage timings. Observed witnesses are not accepted cited witnesses; official hosting alone is not proof. Corrections are source excerpts, not guaranteed statements of the exact latest version.

## Frozen backend routes

- `POST http://127.0.0.1:8765/verify`: JSON `{ "answer": "..." }`, server-side `Authorization: Bearer ...`, returns a schema-v1 `VerificationReport` directly.
- `POST /annotate`: accepts a non-streaming chat completion and returns it with `freshnessguard: GatewayAnnotation`. This route is for the native gateway; the paste-answer UI should use verify.
- Native Bifrost: existing `/openai/v1/chat/completions`, opt-in `x-freshnessguard: verify`; original choices/usage/tool calls are preserved. Read `freshnessguard.reports[].report`; transport `checked` never means the answer is supported.
- `GET /health`: process health only, not evidence/provider readiness.

Bindings: `frontend/contract/types.ts`. Additive optional fields must not break old fixtures. Runtime-check unknown JSON before rendering; TypeScript casts are not validation. Unknown schema/status, wrong field types or a text completion with empty/mismatched checked reports become a visible malformed-response error, not supported. Never invent default proof, score or usage numbers.

Backend HTTP errors currently use `{error: string}` with 400/401/404/413/429/503. A 200 report may still have upstream_error/unavailable, rejected evidence or zero coverage. Inspect the report, not only HTTP success. Optional acquisition failure is reported in `claim.source_retrieval.error`, while judging original snippets can still complete.

## Browser/server boundary

The development adapter exposes `POST /api/verify` with `VerifyInput` when explicitly enabled. It forwards only the answer to `http://127.0.0.1:8765/verify`, attaches the verifier token on the server, and validates the direct live report. Errors use `UIError`. The adapter rejects redirects and stops waiting after 120 seconds. The browser can stop waiting earlier. The Python verifier may continue working after either event.

Start the configured Bifrost gateway first. From the repository root, start the live verifier:

```powershell
python -m freshnessguard.cli serve --env-file .env --port 8765
```

From `frontend/` in a separate PowerShell terminal, enter the same verifier token when prompted:

```powershell
$env:FRESHNESSGUARD_TOKEN = [System.Net.NetworkCredential]::new('', (Read-Host 'Verifier token' -AsSecureString)).Password
$env:FRESHNESSGUARD_ENABLE_LIVE = '1'
npm.cmd run dev
```

Open `http://127.0.0.1:5173/verify`, choose **Live Verification**, paste an answer and submit. Use the exact loopback address printed by Vite. Production builds and preview serve saved demos. Remove `FRESHNESSGUARD_ENABLE_LIVE` from the development terminal and restart Vite to return to demo-only mode.

Tavily/provider/Bifrost/verifier credentials stay server-side, never in `VITE_*`, static files, URLs, localStorage, browser logs or fixtures. The browser never calls a provider or Tavily directly. Keep fixture mode fully offline and default until live integration is intentionally enabled. No API call on mount, typing, example selection or auto-refresh.

Keep local development same-origin via the frontend server/proxy; do not add wildcard CORS or bind the verifier to the LAN. The adapter must enforce request size, allowed content type/origin and local session/auth boundaries before calling the verifier, so another website cannot spend the user's API budget. Reject redirects and arbitrary upstream URLs. Resolve its fixed backend endpoint from server configuration, not request data. Any deployment/auth change requires a separate review; it is not part of frozen-backend feature scope.

## Field semantics

- `coverage` is 0..1; render `coverage * 100` as a percentage. It applies to extracted time-sensitive claims, not proof that extraction found every claim.
- `freshness_score` is 0..100 over decisive claims. `null` renders “Not assessed”, never 0 or 100. Zero coverage must not look like a fresh answer.
- `supported` means the entire claim passed available validation. `outdated` requires accepted evidence. `uncertain` means abstention; `not_checked` means no time-sensitive check was performed.
- `mode` and fixture provenance are separate: a fixture copied from a live report still needs “Saved live — captured at …”, not a live spinner/success badge. An offline repaired replay is not a successful live benchmark.
- `quotes[].text` is an exact substring of that source's included `content` (whitespace-only model transcription is resolved back to the original span). Selected quote windows additionally provide same-source offsets and retain the original model quote. Offsets count Unicode code points, not bytes or JavaScript UTF-16 units; use the quote text directly or `Array.from(content).slice(start, end).join("")` for highlighting. Escape all source/answer strings as text; never use raw HTML insertion. Validate source link scheme/credentials before rendering and use safe new-tab attributes. No automatic source-page requests from the browser.
- Retrieval and publication dates differ from release/effective dates. Show the date kind. Preserve citation IDs; do not use array order as the citation identifier.
- Timings and usage may be absent in historical/incomplete reports. Render missing values as unavailable; stage medians do not sum exactly to total. Token totals aggregate extraction and judgment; do not label them generated-output tokens.
- An envelope-level native failure has unavailable status, empty reports, a fixed explanation and structured `error` with safe stage/category/code. Preserve the original generated answer while clearly labeling it unverified.

## Fixture-first implementation order

`frontend/fixtures/manifest.json` lists local JSON reports:

1. Synthetic mixed supported/outdated/not_checked report, with citations and nonzero coverage.
2. Saved live targeted-source failure: uncertain despite an observed dated witness, because the original quote omitted its date. Keep this historical result unchanged.
3. Offline replay of the same evidence after complete-window selection: outdated, no new paid calls. Label explicitly as offline replay, not live success.
4. Synthetic unavailable extraction: null score, zero coverage and structured error.

First build all visible states against these files, including loading, busy, timeout and malformed-response UI states. Add runtime response validation, then the same-origin server adapter, then a user-triggered live action. Test responsive layouts, long quotes/URLs, zero/null metrics, missing optional fields, unsafe HTML/links and malformed/native-unavailable envelopes. Do not add accounts, databases, live streaming, dashboards for multiple users, new backend evidence features or unattended paid benchmarks.

Exit criteria: the React workbench renders all fixtures honestly, keeps credentials server-side, preserves original text, shows exact citation provenance and uncertainty, and integrates with the already-tested native contract without weakening backend validation.
