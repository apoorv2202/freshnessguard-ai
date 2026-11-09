# 🛡️ FreshnessGuard AI

### AI Answers Have an Expiry Date.

**An evidence-backed freshness verification layer for AI-generated answers, powered by Bifrost and Tavily.**

FreshnessGuard AI verifies time-sensitive claims against external evidence without silently modifying the original AI-generated answer.

Instead of trusting a confident answer at face value, FreshnessGuard extracts individual claims, retrieves relevant evidence, validates citations and quotations, and produces an inspectable verification report.

**Built for the Global AI Hackathon 2026 — Bifrost + Tavily**

[![GitHub](https://img.shields.io/badge/GitHub-apoorv2202-181717?logo=github)](https://github.com/apoorv2202/freshnessguard-ai)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/Frontend-React-149ECA?logo=react&logoColor=white)
![Go](https://img.shields.io/badge/Native_Plugin-Go-00ADD8?logo=go&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

### 📊 Project Presentation

**[View / Download the FreshnessGuard AI Pitch Deck (PPTX)](docs/FreshnessGuard-AI-Final-Pitch.pptx)**

The presentation covers the problem, proposed solution, verification architecture, Bifrost and Tavily integration, demonstrations, and validation results.

### Project Availability

| Resource | Status |
|---|---|
| Source code | Available on GitHub |
| Pitch presentation | PPTX in `docs/` |
| Saved browser demonstration | Available to run locally |
| Python verification service | Available to run locally |
| Native Bifrost integration | Source and build instructions available |
| Public hosted application | Not deployed yet |

**Note:** FreshnessGuard AI is currently distributed as a source-code project with reproducible local demonstrations. A public hosted application is not yet available.

---

## 🌍 The Problem

AI-generated answers can become outdated even when they sound confident.

Examples include:

- Recommending an old software release.
- Referring to a deprecated API.
- Describing a service that has changed.
- Reporting obsolete product information.
- Repeating an outdated technical recommendation.

Language models can produce plausible responses that no longer reflect the latest available evidence.

Simply attaching citations does not guarantee accuracy. A source may be irrelevant, outdated, or insufficient to establish the claim.

### Our Approach

FreshnessGuard introduces an independent verification layer that:

1. Preserves the original AI-generated answer.
2. Extracts concrete time-sensitive claims.
3. Retrieves relevant external evidence.
4. Prioritizes appropriate authoritative sources.
5. Validates quotations, citations, and supported release evidence.
6. Produces explainable verification outcomes.
7. Explicitly reports uncertainty when evidence is insufficient.

**The goal is not to make every AI answer appear correct. It is to make the available evidence and its limitations visible.**

---

## 💡 What Is FreshnessGuard AI?

FreshnessGuard AI is an opt-in freshness verification system integrated with the Bifrost AI gateway.

It combines three main components:

| Component | Responsibility |
|---|---|
| **Bifrost** | Routes model requests and hosts the native verification plugin |
| **Tavily** | Retrieves external evidence relevant to time-sensitive claims |
| **FreshnessGuard** | Extracts claims, orchestrates verification, validates evidence, and generates reports |

The system can operate through a native Bifrost integration or a standalone Python verification endpoint.

The original AI-generated answer remains unchanged, while verification information is presented separately.

---

## ⚙️ System Architecture

```text
                   USER PROMPT
                        |
                        v
                 AI MODEL RESPONSE
                        |
                        v
              +---------------------+
              | Original Answer     |
              | Preserved Unchanged |
              +---------------------+
                        |
                        v
              +---------------------+
              | Claim Extraction    |
              | Bifrost Model       |
              +---------------------+
                        |
                        v
              +---------------------+
              | Time-Sensitive      |
              | Claim Selection     |
              +---------------------+
                        |
                        v
              +---------------------+
              | Tavily Search       |
              | Evidence Retrieval  |
              +---------------------+
                        |
                        v
              +---------------------+
              | Evidence Ranking    |
              | Source Filtering    |
              +---------------------+
                        |
                        v
              +---------------------+
              | Model Assessment    |
              | Deterministic Checks|
              +---------------------+
                        |
                        v
              +---------------------+
              | Freshness Report    |
              | Verdicts + Sources  |
              +---------------------+
```

### Verification Pipeline

**Step 1 — Claim extraction**

A Bifrost-routed model extracts concrete claims from the original answer. Extracted claims must correspond to exact text spans.

**Step 2 — Time-sensitivity analysis**

The verifier selects claims that may depend on changing information.

**Step 3 — Evidence retrieval**

Tavily searches for relevant external information using bounded search requests.

**Step 4 — Evidence assessment**

The verifier evaluates candidate evidence using model judgment and deterministic validation rules.

**Step 5 — Report generation**

The system produces claim-level verdicts, accepted evidence quotations, citations, coverage metrics, and diagnostics.

---

## ✨ Key Features

### 1. Original Answer Preservation

FreshnessGuard never silently rewrites the original response.

Verification information is attached separately so users can distinguish the model's answer from the verifier's findings.

### 2. Atomic Claim Extraction

The verifier extracts concrete claims grounded in exact substrings of the original answer.

Unsupported paraphrases and malformed extraction outputs are rejected.

### 3. Tavily-Powered Search

Time-sensitive claims are checked using targeted external searches.

Search results are ranked and filtered before evidence assessment.

### 4. Deterministic Evidence Validation

The verifier checks:

- Whether a citation identifier exists in the retrieved evidence.
- Whether a proposed quotation occurs in the actual source content.
- Whether required release dates or version details are present.
- Whether applicable official-source policies are satisfied.
- Whether supported deterministic release checks pass.

Quotation matching establishes provenance, not independent factual truth.

### 5. Explainable Verification Outcomes

| Verdict | Meaning |
|---|---|
| `supported` | Accepted evidence supports the checked claim |
| `outdated` | Accepted evidence establishes that the claim is stale |
| `uncertain` | Evidence is insufficient for a decisive result |
| `not_checked` | The claim did not receive a freshness check |
| `unavailable` | A verification dependency or step failed |

### 6. Transparent Reports

Verification reports can include:

- Extracted claims and individual verdicts
- Accepted quotations and citation URLs
- Proposed corrections for outdated claims
- Freshness score and evidence coverage
- Search usage and failure diagnostics

### 7. Explicit Abstention

Insufficient evidence, invalid citations, conflicting sources, malformed model responses, or unavailable dependencies can produce an uncertain or unavailable result rather than an unsupported conclusion.

### 8. Saved Demonstration Mode

The frontend includes saved scenarios that can be explored without external API credentials.

These scenarios are explicitly identified as saved or synthetic demonstrations.

---

## 🧠 Bifrost Integration

FreshnessGuard includes a native Go HTTP transport plugin using Bifrost's shared-object plugin loading mechanism.

Compatible non-streaming chat completions can opt into verification with:

```http
x-freshnessguard: verify
```

The native integration supports:

- Request and response hooks
- Opt-in verification
- Original answer preservation
- Internal-request recursion prevention
- Bounded verification deadlines
- Explicit reporting of verification failures
- Compatible non-streaming text chat responses

The integration is advisory rather than an authorization or enforcement boundary.

Streaming verification is not supported in the current native plugin.

---

## 🔎 Tavily Integration

Tavily provides the external evidence retrieval layer.

FreshnessGuard uses targeted queries to retrieve search candidates for individual claims.

Evidence handling includes:

- Claim-specific search
- Source ranking
- Official-source preference for supported release topics
- Exact quotation validation
- Limited official-page retrieval when needed
- Explicit abstention when decisive evidence cannot be established

A retrieved search result is not automatically treated as proof.

---

## 🖥️ Frontend Workbench

The React frontend includes four pages:

| Page | Purpose |
|---|---|
| **Home** | Introduces the verification system |
| **Verify** | Provides the verification interface |
| **Examples** | Shows saved demonstration scenarios |
| **Integrations** | Explains Bifrost and Tavily integration |

The frontend supports a credential-free saved-demo workflow and an explicitly enabled local live-verification workflow.

**The frontend has not yet been publicly deployed.**

---

## 🧪 Testing and Validation

FreshnessGuard was evaluated using local regression tests, scripted benchmarks, native plugin checks, and gateway integration smoke tests.

### Final Local Release Results

| Test category | Reported result |
|---|---|
| Python regression tests | **173 passed** |
| Frontend tests | **14 passed** |
| Frontend production build | **Passed** |
| Reliability benchmark | **25/25 passed** |
| Protocol benchmark | **8/8 passed** |
| Acquisition scenarios | **4/4 passed** |
| Bifrost gateway smoke | **13/13 passed** |
| Native Go race tests | **Passed** |
| Native plugin loader smoke | **Passed** |

These results were reported for the final local release.

The scripted evaluations exercise expected behavior using controlled evidence and provider responses.

**These results do not establish general live-world fact-checking accuracy.**

### Gateway Smoke Scenarios

**Qualifying official release evidence**

A dated official Python release fixture satisfied the verification requirements.

```text
Verdict: OUTDATED
Citation: Accepted
Evidence: Qualifying dated release passage
```

**Nonqualifying release evidence**

A fictional ExampleSDK release claim relied on evidence from `example.com`, which did not satisfy the required official-source policy.

```text
Verdict: UNCERTAIN
Citation: Not accepted
Evidence: Insufficient for a decisive verdict
```

This demonstrates the intended behavior: an unqualified source should not automatically produce an outdated verdict.

---

## 📊 Freshness Score and Evidence Coverage

### Freshness Score

```text
Freshness Score =
100 × Supported / (Supported + Outdated)
```

Only time-sensitive claims with accepted decisive evidence contribute.

If no evidence-backed decisive verdicts exist, the score is not assessed.

### Evidence Coverage

```text
Evidence Coverage =
Evidence-backed time-sensitive claims
-------------------------------------
All extracted time-sensitive claims
```

Uncertain claims lower coverage.

Historical and other `not_checked` claims are outside the time-sensitive denominator.

A high freshness score with low evidence coverage does not mean the entire answer has been verified.

---

## 🎬 Demonstration and Evidence Provenance

### Example Claim

> The latest stable Python release series is 3.11.

### Captured Live Verification — November 6, 2026

```text
Claim: The latest stable Python release series is 3.11.

Verdict: UNCERTAIN

Reason:
The proposed evidence quotation omitted the
release date required by the verifier.

Accepted citations: None
```

The verifier abstained because the quotation did not satisfy the required release-evidence checks.

### Separate Offline Corrected-Evidence Replay

```text
Claim: The latest stable Python release series is 3.11.

Verdict: OUTDATED

Evidence:
A complete dated release passage.

Mode:
Offline corrected-evidence replay.
```

The offline replay used saved evidence without new model, search, or page-retrieval calls.

It is not another live verification.

An earlier live observation is documented separately in the repository's demonstration materials.

### Recommended Demonstration

For a repeatable walkthrough, use the frontend's **Saved Demo** experience.

The saved examples demonstrate successful evidence handling, uncertainty, and simulated upstream failures.

They should not be represented as fresh live verification.

---

## 🚀 Run FreshnessGuard AI Locally

FreshnessGuard AI is currently available as a source-code project with reproducible local demonstrations.

**A public hosted demo is not yet available.**

### Prerequisites

For the browser demo:

- Node.js 22 or newer
- npm

For the Python verifier:

- Python 3.11 or newer

### Step 1 — Clone the Repository

```bash
git clone https://github.com/apoorv2202/freshnessguard-ai.git
cd freshnessguard-ai
```

### Step 2 — Run the Saved Browser Demo

On Windows PowerShell:

```powershell
npm.cmd ci --prefix frontend

Remove-Item Env:FRESHNESSGUARD_ENABLE_LIVE -ErrorAction SilentlyContinue

npm.cmd run dev --prefix frontend
```

Open the local URL shown by Vite.

Navigate to **Examples** and select a saved scenario.

This does not require Tavily credentials, Gemini credentials, Bifrost, or the Python verifier.

### Step 3 — Run the Offline Python Demo

From the repository root:

```powershell
python -m freshnessguard.cli demo
python -m scripts.render_demo
Start-Process ./demo/report.html
```

The generated report is a portable demonstration of the verification report format.

Its model decisions and search evidence are scripted.

### Step 4 — Run Regression Tests

```powershell
python -m unittest discover -s tests -v
```

### Step 5 — Run the Offline Benchmark

```powershell
python -B -m benchmarks.final_offline
```

These commands evaluate the local implementation and fixed test scenarios, not live fact-checking accuracy.

---

## 🛠️ Standalone Python Verification Service

Start the verifier using synthetic evidence:

```powershell
python -m freshnessguard.cli serve --fixture
```

In another PowerShell terminal:

```powershell
$body = @{
    answer = 'The latest stable version of ExampleSDK is 3.0.'
} | ConvertTo-Json

Invoke-RestMethod `
    http://127.0.0.1:8765/verify `
    -Method Post `
    -ContentType application/json `
    -Body $body
```

The endpoint allows local inspection of verification results without live external providers.

---

## 🔐 Environment Configuration

For live verification, create a local environment file:

```powershell
Copy-Item .env.example .env
```

Configure the required values:

| Variable | Purpose |
|---|---|
| `BIFROST_URL` | Bifrost OpenAI-compatible base URL |
| `BIFROST_MODEL` | Configured provider/model identifier |
| `BIFROST_VIRTUAL_KEY` | Gateway virtual key, if required |
| `TAVILY_API_KEY` | Tavily API credential |
| `FRESHNESSGUARD_TOKEN` | Local verifier authentication token |

Configure the Gemini provider credential in Bifrost itself.

The verifier token should contain at least 24 characters and must match between the verifier and frontend's server-side process.

**Never commit `.env` or expose credentials in client-side `VITE_*` variables.**

---

## 🌐 Local Live Verification

Live verification requires three locally running components.

### Terminal 1 — Bifrost Gateway

Start a configured Bifrost gateway on loopback port `8080`.

The gateway must have a working model-provider configuration.

Follow the upstream Bifrost setup instructions for your platform.

### Terminal 2 — Python Verifier

```powershell
python -m freshnessguard.cli serve --env-file .env --port 8765
```

### Terminal 3 — Vite Frontend

From the repository root:

```powershell
Set-Location frontend

$env:FRESHNESSGUARD_TOKEN = [System.Net.NetworkCredential]::new(
    '',
    (Read-Host 'Verifier token' -AsSecureString)
).Password

$env:FRESHNESSGUARD_ENABLE_LIVE = '1'

npm.cmd run dev
```

Open the local Verify page.

Before making a live request, confirm the configured model supports structured JSON output and that Tavily and model-provider quotas are available.

Health endpoints confirm local process availability, not live-provider readiness.

Live verification may consume model-provider and Tavily credits.

---

## 🐧 Native Bifrost Plugin — WSL Ubuntu

FreshnessGuard's native Go integration uses the existing Bifrost shared-object plugin loader.

The inspected upstream source revision was:

```text
afdce01b50a78199f59e38117cd4d5952d038b07
```

The inspected upstream modules declared Go `1.27.3`.

A compatible Go toolchain, C build tools, CGO, and matching gateway/plugin build settings are required.

### Build the Plugin

```bash
bash scripts/build-plugin.sh
```

### Native Loader Smoke

```bash
python3 -m scripts.native_smoke --upstream "$PWD/work/bifrost"
```

### Build the Gateway

```bash
bash scripts/build-gateway.sh
```

### Gateway Smoke

```bash
python3 -m scripts.gateway_smoke
```

The gateway smoke exercises the actual Bifrost HTTP gateway, native plugin, and verifier with controlled local provider responses and evidence.

It does not require live paid-provider calls.

### Deployment and Integration Considerations

- Build the plugin and gateway using compatible upstream source and toolchain settings.
- Use a dynamically linked gateway compatible with the shared-object loader.
- Merge `integrations/bifrost/config.fragment.json` into the gateway configuration.
- Set the plugin path to the absolute Linux `.so` location.
- Ensure the verifier and gateway can communicate over their configured network.
- Configure the same verifier authentication token for the native plugin and Python service.
- Do not assume Windows loopback services are reachable from WSL.

The normal static Bifrost release binary is not interchangeable with the required dynamically linked build.

---

## 🧰 Repository Structure

```text
freshnessguard-ai/
|
|-- .github/
|   `-- workflows/
|
|-- benchmarks/
|   `-- Scripted evaluations and benchmark utilities
|
|-- demo/
|   |-- report.html
|   `-- report.json
|
|-- docs/
|   `-- FreshnessGuard-AI-Final-Pitch.pptx
|
|-- freshnessguard/
|   `-- Core Python verification system
|
|-- frontend/
|   `-- React browser workbench
|
|-- integrations/
|   `-- Native Bifrost plugin
|
|-- scripts/
|   `-- Build, smoke-test, and demo utilities
|
|-- tests/
|   `-- Python regression tests
|
|-- .env.example
|-- .gitignore
|-- LICENSE
|-- pyproject.toml
`-- README.md
```

The presentation entry assumes the PPTX has been uploaded to the documented location.

Some benchmark outputs and build artifacts are generated locally rather than committed.

---

## 🛡️ Reliability and Safety Design

### Deterministic Evidence Gates

Decisive verdicts require qualifying citations and evidence quotations.

Supported release topics also use deterministic source and version checks.

### Resource Limits

The implementation bounds:

- Input answer length
- Number of extracted claims
- Claims selected for search
- Search and model request budgets
- Source content size
- Official-page retrieval
- Concurrent verification requests

### Rate-Limit Handling

Provider HTTP 429 responses can stop additional paid verification checks.

The resulting report makes the failure explicit.

### Recursion Prevention

Internal verifier model calls do not trigger the native verification workflow again.

### Failure Transparency

Verification failures preserve the original answer and report an unavailable state where appropriate.

The completion of the reporting operation does not mean every claim has been verified.

---

## ⚠️ Known Limitations

FreshnessGuard AI is a prototype, not a universal fact-checking guarantee.

- Only compatible non-streaming text chat completions are supported by the native plugin.
- Some claims are not extracted or checked.
- General semantic judgments remain model-assisted.
- Exact quotation matching establishes provenance, not factual truth.
- Retrieval time does not guarantee source freshness.
- Unsupported release topics may produce uncertain outcomes.
- Provider rate limits, latency, and network failures can interrupt verification.
- Multi-claim requests can exceed browser adapter deadlines.
- Gateway timeouts do not necessarily cancel ongoing verifier work.
- The local development service is not a production-grade public API.
- No complete multi-tenant authentication and isolation system is included.
- A public deployment has not yet been completed.

### Privacy Considerations

Answer claims and source excerpts may be sent to the configured model provider.

Search queries are sent to Tavily.

Do not submit sensitive production answers without an approved data-handling policy.

Retrieved source content is treated as untrusted data, but model-level prompt injection remains a risk.

---

## 📈 Future Improvements

Potential future directions include:

- Broader official-source policies
- Additional claim categories
- More model-provider configurations
- Improved evidence retrieval efficiency
- Expanded live evaluation datasets
- Better verification analytics
- Production-ready authentication and isolation
- Public frontend hosting
- Secure cloud deployment of the verifier and Bifrost gateway

These are future possibilities, not currently deployed capabilities.

---

## 📚 Documentation

Additional technical materials are available in:

- `docs/` — architecture, integration notes, and project presentation
- `benchmarks/` — scripted evaluations and benchmark methodology
- `integrations/` — Bifrost plugin implementation
- `scripts/` — build and verification utilities
- `tests/` — regression tests
- `frontend/` — React workbench

The project includes source code and test fixtures for inspection and local reproduction.

---

## 👨‍💻 Developer

**Apoorv Anand**  
Computer Science and Engineering  
RV College of Engineering, Bengaluru

GitHub: [@apoorv2202](https://github.com/apoorv2202)

Project: [FreshnessGuard AI](https://github.com/apoorv2202/freshnessguard-ai)

Developed as a solo hackathon project.

---

## 📄 License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for details.

---

## ⭐ Final Thought

### AI answers should not require blind trust.

A confident response is not the same as a verified response.

FreshnessGuard AI makes evidence, citations, uncertainty, and verification limitations visible while preserving the original answer.

**Keep the answer. Check the evidence. Make freshness visible.**

Built with **Bifrost + Tavily**.
