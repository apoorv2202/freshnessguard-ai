# FreshnessGuard AI

An opt-in freshness verification plugin for the Bifrost AI gateway, backed by Tavily search. Built for a solo Windows workflow, targeting Bifrost problem 04 and Tavily problem 01, with a personal submission target of **10 November 2026 (IST)**.

The gateway preserves the original answer and adds `freshnessguard` reports: atomic claims, `supported` / `outdated` / `uncertain` verdicts, evidence quotes, citation URLs, corrections, coverage and search usage. A standalone `/verify` endpoint handles existing answers.

**Demo status:** the React workbench includes Home, Verify, Examples, and Integrations. The Python verifier and native Go plugin are frozen for the demo. One authorized live run through Vite marked “The latest stable Python release series is 3.11.” as outdated with one accepted official citation, 100% coverage, and freshness 0/100 in 9.66 seconds. This is a measured single-run result. The [frontend contract](docs/FRONTEND_CONTRACT.md) documents report and fixture provenance.

See [measured live outcomes](docs/LIVE_RESULTS.md), [troubleshooting](docs/TROUBLESHOOTING.md), [demo script and pitch](docs/DEMO_SCRIPT.md), and [submission status](docs/SUBMISSION.md). Open `demo/report.html` for synthetic outdated/supported examples, `demo/live-supported.html` for a captured official-source live result, and `demo/live-uncertain.html` for a captured live abstention. Live examples identify their capture revision and are not presented as validation of subsequent changes.

## Run the offline demo — Windows

Python 3.11+; no third-party Python dependencies required. In PowerShell, from this folder:

```powershell
python -m freshnessguard.cli demo
python -m scripts.render_demo
Start-Process ./demo/report.html
python -m unittest discover -s tests -v
python -m benchmarks.run
```

The offline demo is explicitly **synthetic**: model decisions and search responses are scripted. It proves report plumbing and failure handling, not fact-checking accuracy. `demo/report.html` is a portable sample report; `demo/report.json` is the corresponding API output.

Run the local service with synthetic evidence:

```powershell
python -m freshnessguard.cli serve --fixture
```

In another terminal:

```powershell
$body = @{answer='The latest stable version of ExampleSDK is 3.0.'} | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8765/verify -Method Post -ContentType application/json -Body $body
```

## Run the browser demo on Windows

Use Python 3.11+, Node.js with npm, and the existing Bifrost installation. Install the frontend dependencies ahead of the demo with `npm.cmd ci --prefix frontend` if they are missing.

### Live verification

Use three PowerShell terminals. Keep each service on loopback.

1. **Bifrost on 8080.** Start the existing configured gateway with its existing Gemini provider and virtual key. If using the cached Windows v2.4.0 binary, run the command below. If the gateway is already running, check its health and reuse it. Startup can contact Gemini for model discovery.

   ```powershell
   node -e "const p=require('node:child_process').spawnSync(process.env.LOCALAPPDATA+'/bifrost/v2.4.0/bin/bifrost-http.exe-0',['-host','127.0.0.1','-port','8080','-app-dir',process.env.APPDATA+'/Bifrost'],{stdio:'inherit'}); process.exit(p.status ?? 1)"
   ```

2. **Python verifier on 8765.** From the repository root, start the verifier with the local `.env` file. Restart any older verifier first so it loads the current code.

   ```powershell
   python -m freshnessguard.cli serve --env-file .env --port 8765
   ```

3. **Vite on 5173.** From the repository root, open another PowerShell terminal and enter the same verifier token at the masked prompt.

   ```powershell
   Set-Location frontend
   $env:FRESHNESSGUARD_TOKEN = [System.Net.NetworkCredential]::new('', (Read-Host 'Verifier token' -AsSecureString)).Password
   $env:FRESHNESSGUARD_ENABLE_LIVE = '1'
   npm.cmd run dev
   ```

Check `GET /health` on ports 8080 and 8765 and open the [local Verify page](http://127.0.0.1:5173/verify). Health checks confirm local process availability. They do not test provider credentials or quota. When ready to incur model and search usage, choose **Live Verification**, paste `The latest stable Python release series is 3.11.`, and submit once. Expand the claim and inspect the accepted quote and official citation. A live report can abstain or report a provider failure.

| Setting | Where it belongs |
| --- | --- |
| Gemini provider key | Existing Bifrost provider configuration |
| `BIFROST_URL` | Python `.env`, the gateway's loopback OpenAI-compatible base URL |
| `BIFROST_MODEL` | Python `.env`, the configured provider/model identifier |
| `BIFROST_VIRTUAL_KEY` | Python `.env`, when required by Bifrost |
| `TAVILY_API_KEY` | Python `.env` |
| `FRESHNESSGUARD_TOKEN` | Python `.env` and Vite's server-side process environment. Use the same token, at least 24 characters. |
| `FRESHNESSGUARD_ENABLE_LIVE` | Vite server-side opt-in. Set to `1` only for the live development demo. |

Keep `.env` local. Never put credentials in a `VITE_*` variable or show the environment file or gateway settings during the demo.

### Offline fallback

If the live result is unavailable, times out, or lacks decisive evidence, explain the returned state and switch to **Saved Demo**. Open [Offline corrected evidence](http://127.0.0.1:5173/verify?demo=replay) or select that scenario from Examples. It uses saved source text and shows an accepted exact quote for the same Python claim. Present it as an **offline replay**. **Captured uncertain result** shows a historical abstention, and **Simulated upstream failure** is an intentional error example.

For a fully offline rehearsal, start Vite from the repository root without the live opt-in:

```powershell
Remove-Item Env:FRESHNESSGUARD_ENABLE_LIVE -ErrorAction SilentlyContinue
npm.cmd run dev --prefix frontend
```

Saved demos only need Vite and also work in the production build. Bifrost, Python, Gemini, and Tavily are unnecessary for the fallback.

## Live CLI and benchmark

Use the same Bifrost instance and local `.env` as the browser demo. The model must support JSON object output. The measured run used `gemini/gemini-3-flash-preview`. For a new setup, use [the environment template](.env.example) as a reference.

These commands consume Tavily credits and model usage:

```powershell
python -m freshnessguard.cli verify --env-file .env --answer-file answer.txt
python -m benchmarks.live --env-file .env
```

The live runner now defaults to eight developer-labelled cases and enforces a search budget (8 by default), saves partial results after every case, paces cases by 20 seconds, and stops on 429/503 without retrying. After the provider quota is available, start with a smaller validation run:

```powershell
python -m benchmarks.live --env-file .env --max-cases 3 --max-searches 2 --interval-seconds 30
```

Restart an already-running verification service after changing the code: it does not hot-reload. Keep the existing gateway and provider credentials unchanged. The configured Gemini Flash model requests minimal reasoning and a 2,800-token output cap to reduce thinking-related JSON truncation; backend support and quotas still govern actual completion.

Environment files support plain `NAME=value` entries and optional surrounding quotes, with no expansion or executable content. Only the five documented FreshnessGuard/Bifrost variables are accepted. They load only when `--env-file` is explicitly supplied. Errors never include upstream response bodies or key values.

## Native Bifrost integration — WSL Ubuntu

This is a real native HTTP transport plugin, using the existing OSS loader. It does not depend on an unofficial webhook feature or a separate client proxy. Native Go plugins require Linux/macOS, CGO and a dynamically linked gateway; the normal static release binary is insufficient.

Inspected upstream: `maximhq/bifrost` commit **afdce01b50a78199f59e38117cd4d5952d038b07**, retrieved 5 November 2026. Its modules declare Go **1.27.3**. Compiler, dependency graph, architecture, CGO/build flags and libc must match between gateway and plugin.

In Ubuntu, install Go matching the pinned source and the C build tools, then run from this project's Linux path:

```bash
bash scripts/build-plugin.sh
python3 -m scripts.native_smoke --upstream "$PWD/work/bifrost"
```

To build and exercise the entire HTTP gateway with a local mock provider:

```bash
bash scripts/build-gateway.sh
python3 -m scripts.gateway_smoke
```

This API-only build uses the real upstream HTTP backend and a small placeholder for its embedded dashboard. The smoke test runs generation, claim extraction and judging through Bifrost, with scripted provider responses and search evidence. It also tests opt-out, streaming rejection, recursion prevention and verifier failure over real HTTP. Results go to `benchmarks/gateway-smoke.json`. It does not claim live detector accuracy.

The build script clones the pinned source into ignored `work/bifrost` when absent. An existing upstream checkout can be passed as the first argument. The loader smoke command starts a temporary authenticated Python service and loads the `.so` with **Bifrost's actual `SharedObjectPluginLoader`**, then runs the request/response hooks. It uses synthetic evidence and has no paid API calls.

For a gateway deployment:

1. Build the gateway and plugin from this same upstream checkout and a **shared Go workspace**, including upstream `core`, `framework`, `transports`, all `plugins/*` modules and `integrations/bifrost`. Use CGO, the same Go compiler and build flags for both. Bifrost documents `make build DYNAMIC=1`; build its UI as required by that target. Do not copy this plugin into an arbitrary released binary.
2. Merge `integrations/bifrost/config.fragment.json` into the gateway's `config.json`; replace the plugin path with the absolute Linux `.so` path. Preserve any existing plugin/provider entries.
3. Run the verifier in the same Linux network namespace as Bifrost and export the same `FRESHNESSGUARD_TOKEN` into both processes. For WSL, run the Python service inside Ubuntu too. A Windows `127.0.0.1` service is not assumed reachable from WSL.
4. Send a non-streaming chat request with `x-freshnessguard: verify` and `n=1`. Remove the header to bypass verification.

Example request, from Ubuntu after the gateway and verifier are configured:

```bash
curl http://127.0.0.1:8080/openai/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'x-freshnessguard: verify' \
  -d '{"model":"YOUR_PROVIDER/YOUR_MODEL","stream":false,"n":1,"messages":[{"role":"user","content":"What Go version does Bifrost currently require?"}]}'
```

Add `x-bf-vk` using your local configuration when required. Live verification's internal model requests carry no opt-in header and add `x-freshnessguard-internal: 1`, preventing recursion. A client may bypass this advisory feature; it is not an enforcement or authorization boundary.

## Report interpretation

| Outcome | Meaning |
| --- | --- |
| `supported` | Accepted evidence supports the checked claim. |
| `outdated` | Accepted evidence shows the claim is stale. The correction is a quoted source excerpt. |
| `uncertain` | The verifier abstained because it could not establish a decisive result. |
| `not_checked` | The claim did not receive a freshness check, for example because it is historical. |
| `unavailable` | A verification dependency or step failed. Inspect the report's errors and treat the affected claim as unverified. |

`freshness_score = 100 × supported / (supported + outdated)` over decisive time-sensitive claims. It is `null` when there is no decisive evidence. `coverage` is the decisive fraction of **extracted time-sensitive claims**, not all possible claims in the answer. A high score with low coverage is not an all-clear.

Extraction uses a model through Bifrost, with a maximum of 8 exact-substring claims. Up to 5 time-sensitive claims are searched, using at most 5 basic Tavily calls and 6 model calls per single answer. Timeless claims are `not_checked`. Search failures, conflicting sources, invalid model output, invalid citations or quotes and exhausted budgets abstain. Every decisive verdict requires source IDs and evidence substrings that exist in the actual retrieved content.

The model assesses scope, dates and semantic support. Quote validation proves provenance, **not entailment or factual truth**. Retrieval time does not establish source freshness. No numerical confidence probability is invented. Only outdated claims get a proposed correction; original text is always retained.

Reliability guards require concrete subjects grounded in extracted claim text and skip provider answers marked `length` or `content_filter`. Empty extraction is `no_claims_extracted`, never an all-clear. Corrections are exact excerpts of cited evidence, not model paraphrases. Whitespace-only transcription differences resolve back to an exact original source span; invented words, punctuation and ellipses are not repaired. Recognized Python, Node.js and Bifrost claims require an accepted official source for decisive verdicts; GitHub policy checks the repository owner/path. Other entities have unassessed authority. Explicit unresolved conflicts, future-dated evidence, malformed JSON, duplicate JSON keys and ungrounded citations abstain. Input citation domains are flagged separately; their linked contents are not automatically fetched or authenticated.

## Limits and failure behavior

- Non-streaming text chat completions only. Opted-in streaming, malformed requests and `n>1` are rejected before the provider call. Other API shapes and tool-only answers are not verified.
- Input answer <=16,000 characters; native request/response <=256 KB; bounded snippets and 4 sources per search. Service accepts 2 active verifications and returns 429 when busy. No cross-user cache or retained answer database.
- Advisory fail-open: unavailable verification preserves the answer and adds explicit unavailable metadata/header. Inspect each report's status; outer `checked` means the reporting operation completed, not that every claim is correct.
- Extraction and Tavily use a 20-second socket timeout. Gemini judgment uses 45 seconds. Official-page retrieval has a 6-second deadline. The Vite adapter waits up to 120 seconds and the native hook up to 150 seconds. Verification requests are not automatically retried by FreshnessGuard. Multi-claim verification can exceed the browser adapter deadline.
  Plugin `config.timeout_ms` can reduce its request deadline (100–150000 ms). Timeout/malformed-service responses preserve the answer with explicit unavailable metadata. The deadline does not cancel work already running inside the Python service.
- Loopback-only development service. No public deployment, user authentication product, multi-tenant isolation or distributed cancellation is included. A request abandoned by the gateway may finish its bounded background verification work.
- Answer claims and source snippets are sent to the configured model; search queries go to Tavily. Do not use sensitive production answers without an operator-approved data policy. Embedded source instructions are treated as untrusted data, but prompt injection remains a model-level risk.

See [architecture review](docs/ARCHITECTURE.md), [benchmark methodology](benchmarks/README.md) and [submission checklist](docs/SUBMISSION.md) for what has and has not been validated.
