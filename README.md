# 🛡️ FreshnessGuard AI

### AI Answers Have an Expiry Date.

**An evidence-backed freshness verification layer for AI-generated answers, powered by Bifrost and Tavily.**

FreshnessGuard AI verifies time-sensitive claims against external evidence without silently modifying the original AI-generated answer.

Instead of assuming that a confident answer is correct, FreshnessGuard extracts individual claims, retrieves relevant evidence, validates citations and quotations, and generates an inspectable verification report.

**Built for the Global AI Hackathon 2026 — Bifrost + Tavily**

[![GitHub](https://img.shields.io/badge/GitHub-apoorv2202-181717?logo=github)](https://github.com/apoorv2202/freshnessguard-ai)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/Frontend-React-149ECA?logo=react&logoColor=white)
![Go](https://img.shields.io/badge/Native_Plugin-Go-00ADD8?logo=go&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌍 The Problem

AI-generated answers can become outdated even when they sound completely confident.

Consider questions such as:

- What is the latest stable Python release?
- Which version of an API is currently supported?
- Has a software framework deprecated a feature?
- Is a particular model or service still available?
- Has a product specification or official policy changed?

Language models may generate answers using information that no longer reflects the latest available evidence.

**And simply attaching a citation does not guarantee correctness.**

A citation may reference an obsolete document, an irrelevant page, or a passage that does not support the claim.

### Our Approach

FreshnessGuard adds a verification layer that:

1. Preserves the original AI answer.
2. Extracts time-sensitive claims.
3. Searches for supporting or contradicting evidence.
4. Prioritizes relevant and authoritative sources.
5. Validates exact quotations and applicable release evidence.
6. Produces transparent verdicts and citations.
7. Explicitly reports uncertainty when evidence is insufficient.

**The goal is not to make every AI answer appear correct. It is to make the evidence and limitations visible.**

---

## 💡 What Is FreshnessGuard AI?

FreshnessGuard AI is an opt-in verification system integrated with the Bifrost AI gateway.

It combines three major components:

| Component | Responsibility |
|---|---|
| **Bifrost** | Routes model requests for claim extraction and evidence judgment; hosts the native verification plugin |
| **Tavily** | Retrieves external search evidence relevant to individual claims |
| **FreshnessGuard** | Orchestrates verification, validates quotations and citations, applies release checks, and generates reports |

FreshnessGuard can operate through a native Bifrost integration or a standalone Python verification endpoint.

The native integration preserves the original response and attaches a separate freshness report.

---

## ⚙️ How It Works

```text
                    USER PROMPT
                         |
                         v
                  AI MODEL RESPONSE
                         |
                         v
              +----------------------+
              | Original Answer      |
              | Preserved Unchanged  |
              +----------------------+
                         |
                         v
              +----------------------+
              | Claim Extraction     |
              | Via Bifrost Model    |
              +----------------------+
                         |
                         v
              +----------------------+
              | Time-Sensitive       |
              | Claim Selection      |
              +----------------------+
                         |
                         v
              +----------------------+
              | Tavily Search        |
              | External Evidence    |
              +----------------------+
                         |
                         v
              +----------------------+
              | Evidence Ranking     |
              | Official Sources     |
              +----------------------+
                         |
                         v
              +----------------------+
              | Model Assessment     |
              | + Deterministic Gate |
              +----------------------+
                         |
                         v
              +----------------------+
              | Freshness Report     |
              | Verdicts + Citations |
              +----------------------+
```

The original answer remains intact throughout the process.

The verifier's decisions are reported separately, allowing users to inspect the evidence instead of relying on an unexplained replacement answer.

---

## ✨ Key Features

### 1. Original Answer Preservation

FreshnessGuard does not silently rewrite the generated response.

It attaches verification metadata and a separate evidence report, keeping the original answer available for inspection.

### 2. Atomic Claim Extraction

A Bifrost-routed model extracts concrete, time-sensitive claims from the original answer.

Extracted claims must correspond to exact spans of the input answer. Unsupported paraphrases are rejected.

### 3. Tavily-Powered Evidence Retrieval

FreshnessGuard generates targeted search queries for selected claims.

Tavily supplies external search candidates, which are ranked and filtered before evidence assessment.

For supported release claims, official sources receive additional scrutiny.

### 4. Deterministic Citation Validation

The verifier checks whether:

- A cited source identifier exists in the retrieved evidence.
- A proposed quotation occurs in the actual source content.
- Required dates or version information are present.
- Applicable official-source requirements are satisfied.
- Supported release-version checks pass.

Exact quotation matching establishes that text came from the selected evidence. It does not independently prove semantic correctness.

### 5. Evidence-Backed Verdicts

Each checked claim can receive an explicit result:

| Verdict | Meaning |
|---|---|
| ✅ `supported` | Accepted evidence supports the checked claim |
| ⚠️ `outdated` | Accepted evidence establishes that the claim is stale |
| ❔ `uncertain` | The verifier cannot establish a decisive result |
| ➖ `not_checked` | The claim did not receive a freshness check |
| ⛔ `unavailable` | A verification dependency or step failed |

### 6. Explainable Verification Reports

Reports can include:

- Extracted claims
- Individual verification outcomes
- Evidence quotations
- Citation URLs
- Proposed corrections for outdated claims
- Evidence coverage
- Freshness score
- Search usage
- Failure diagnostics

### 7. Explicit Failure Handling

FreshnessGuard handles insufficient evidence, invalid citations, malformed model responses, provider failures, and exhausted request budgets.

When a reliable conclusion cannot be established, the verifier can abstain instead of inventing certainty.

### 8. Saved Demo Mode

A credential-free demonstration is available through the frontend.

Judges can explore representative saved verification reports without needing live model-provider access.

Saved scenarios are explicitly distinguished from live verification.

---

## 🧠 Bifrost Integration

FreshnessGuard includes a native Go HTTP transport plugin for the Bifrost AI gateway.

The integration supports opt-in verification of compatible non-streaming text chat completions.

A request can enable verification using:

```http
x-freshnessguard: verify
```

The native plugin integrates with Bifrost's request and response hooks.

It preserves the original model-generated answer and attaches verification results when available.

### Native Integration Capabilities

- Opt-in verification
- Request and response hooks
- Non-streaming chat support
- Recursion prevention for internal model requests
- Bounded verification deadlines
- Explicit verification failure reporting
- Preservation of original model output

The integration is advisory, not an authorization or enforcement boundary.

Streaming verification is not supported by the current native plugin.

---

## 🔎 Tavily Integration

Tavily provides the external search layer used during claim verification.

FreshnessGuard uses bounded search queries to retrieve evidence candidates relevant to the extracted claims.

The verifier then evaluates source relevance, citation validity, quotation integrity, and applicable release-version requirements.

### Evidence Handling

FreshnessGuard can:

- Search for evidence related to individual claims.
- Prefer official documentation for supported release topics.
- Filter unsuitable sources.
- Check exact evidence quotations.
- Fetch a limited number of allowlisted official pages when necessary.
- Reject unsupported decisive verdicts.

The system does not treat every retrieved webpage as authoritative.

---

## 🖥️ Frontend Workbench

The React-based frontend provides four primary pages:

| Page | Purpose |
|---|---|
| **Home** | Introduces FreshnessGuard and its verification approach |
| **Verify** | Provides the verification interface |
| **Examples** | Displays saved demonstration scenarios |
| **Integrations** | Explains the system's integration architecture |

The frontend supports both saved demonstration workflows and an explicitly enabled local live-verification workflow.

Saved demos are available without external API credentials.

---

## 🧪 Testing and Validation

FreshnessGuard underwent local regression testing, scripted benchmark evaluation, native plugin checks, and Bifrost gateway smoke testing.

### Final Local Release Validation

| Test category | Result |
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

These results were reported for the final local release validation.

### What These Results Demonstrate

The tests exercise:

- Claim extraction and verification logic
- Evidence and citation validation
- Deterministic release checks
- Error handling and abstention behavior
- Frontend behavior
- Native plugin loading
- Bifrost gateway integration
- Scripted provider and evidence scenarios

**Important:** These are local tests and scripted evaluations. They are not measurements of general live fact-checking accuracy.

The full gateway smoke uses the actual Bifrost gateway, native Go plugin, and Python verifier with controlled local provider responses and evidence.

### Gateway Smoke Verification

Two important scenarios demonstrate the verifier's evidence policy.

**Scenario A — Qualifying release evidence**

A dated official Python release fixture satisfied the required checks.

Result:

```text
Verdict: OUTDATED
Citation: Accepted
Evidence: Qualifying dated release passage
```

**Scenario B — Nonqualifying evidence**

A fictional ExampleSDK release claim used evidence from `example.com`, which did not satisfy the official-source requirement.

Result:

```text
Verdict: UNCERTAIN
Citation: Not accepted
Evidence: Insufficient for a decisive release verdict
```

The second scenario is intentional: FreshnessGuard should not declare a claim outdated merely because an unqualified source says so.

---

## 📊 Freshness Score and Coverage

FreshnessGuard separates the quality of accepted evidence from the proportion of claims successfully verified.

### Freshness Score

```text
Freshness Score =
100 × Supported / (Supported + Outdated)
```

Only time-sensitive claims with accepted decisive evidence contribute to this score.

When there are no such verdicts, the score is not assessed.

### Evidence Coverage

```text
Evidence Coverage =
Evidence-backed time-sensitive claims
-------------------------------------
All extracted time-sensitive claims
```

Uncertain claims reduce coverage.

Historical or otherwise unverified `not_checked` claims are excluded from the time-sensitive denominator.

A high freshness score with low coverage must not be interpreted as comprehensive verification.

---

## 🎬 Demonstration

### Example: An Outdated Software-Release Claim

Consider the statement:

> The latest stable Python release series is 3.11.

FreshnessGuard attempts to verify the release claim using external evidence.

### Captured Live Result — November 6, 2026

```text
Claim: The latest stable Python release series is 3.11.

Result: UNCERTAIN

Reason:
The proposed evidence quotation omitted the
release date required by the verifier.

Accepted citations: None
```

The verifier abstained because the selected quotation did not satisfy its release-evidence requirements.

### Separate Offline Corrected-Evidence Replay

The saved evidence was replayed with a complete dated passage.

```text
Claim: The latest stable Python release series is 3.11.

Result: OUTDATED

Evidence:
Complete dated release passage

Mode:
Offline corrected-evidence replay
```

This replay used no new model, search, or page-fetch calls.

It is not a second live verification.

The repository also documents an earlier live observation and distinguishes it from the later captured result and offline evaluation.

---

## 🚀 Quick Start

### Prerequisites

For the saved browser demo:

- Node.js 22 or newer
- npm

For the Python verifier:

- Python 3.11 or newer

For native gateway integration:

- Linux or WSL Ubuntu
- A compatible Go toolchain
- C build tools
- The pinned Bifrost upstream source
- Matching compiler and build configuration for the gateway and plugin

Live verification additionally requires configured model-provider access through Bifrost and a Tavily API key.

### 1. Clone the Repository

```bash
git clone https://github.com/apoorv2202/freshnessguard-ai.git
cd freshnessguard-ai
```

### 2. Run the Saved Browser Demo

On Windows PowerShell:

```powershell
npm.cmd ci --prefix frontend

Remove-Item Env:FRESHNESSGUARD_ENABLE_LIVE -ErrorAction SilentlyContinue

npm.cmd run dev --prefix frontend
```

Open the local URL displayed by Vite.

Navigate to **Examples** and select a saved scenario.

This workflow does not require Gemini, Tavily, Bifrost, or the Python verifier.

### 3. Run the Offline Python Demo

From the repository root:

```powershell
python -m freshnessguard.cli demo
python -m scripts.render_demo
Start-Process ./demo/report.html
```

The generated report provides a portable demonstration of the verification report format.

The demonstration uses synthetic inputs and scripted evidence.

### 4. Run the Python Tests

```powershell
python -m unittest discover -s tests -v
```

### 5. Run the Offline Benchmark

```powershell
python -B -m benchmarks.final_offline
```

The offline benchmark evaluates expected behavior on fixed fixtures, not live-world accuracy.

---

## 🛠️ Standalone Verification Service

FreshnessGuard also provides a standalone Python verification endpoint.

Start the local service with synthetic evidence:

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

This allows local inspection of verification responses without using live providers.

---

## 🔐 Environment Configuration

Copy the example environment file before configuring live verification:

```powershell
Copy-Item .env.example .env
```

Populate the local `.env` with the required settings.

| Variable | Purpose |
|---|---|
| `BIFROST_URL` | Bifrost's OpenAI-compatible API base URL |
| `BIFROST_MODEL` | Configured provider/model identifier |
| `BIFROST_VIRTUAL_KEY` | Gateway virtual key, if required |
| `TAVILY_API_KEY` | Tavily API credential |
| `FRESHNESSGUARD_TOKEN` | Shared local verifier authentication token |

The Gemini provider credential belongs in the Bifrost provider configuration.

For local frontend live verification:

```powershell
$env:FRESHNESSGUARD_ENABLE_LIVE = '1'
```

The frontend's server-side process must also receive the same verifier token.

**Never commit `.env`, API credentials, authentication tokens, or provider secrets.**

Do not expose credentials through `VITE_*` environment variables, because those can be included in client-side builds.

---

## 🌐 Local Live Verification

Live verification requires three local components:

1. Bifrost gateway
2. Python verifier
3. Vite frontend

### Terminal 1 — Bifrost

Start your configured Bifrost gateway on loopback port `8080`.

Follow the upstream Bifrost installation instructions for your operating system and provider configuration.

The repository's documented Windows workflow also supports an existing cached Bifrost binary.

### Terminal 2 — Python Verifier

```powershell
python -m freshnessguard.cli serve --env-file .env --port 8765
```

### Terminal 3 — Frontend

```powershell
Set-Location frontend

$env:FRESHNESSGUARD_TOKEN = [System.Net.NetworkCredential]::new(
    '',
    (Read-Host 'Verifier token' -AsSecureString)
).Password

$env:FRESHNESSGUARD_ENABLE_LIVE = '1'

npm.cmd run dev
```

Open the Verify page and select the live-verification workflow.

### Before Running a Live Check

Confirm that:

- Bifrost is running.
- The Python verifier is running.
- The configured model supports structured JSON output.
- Tavily credentials are valid.
- The provider has available quota.
- The verifier token matches between services.

Health checks confirm process availability, not provider readiness.

Live verification can incur model-provider and Tavily usage charges.

---

## 🐧 Native Bifrost Plugin — WSL Ubuntu

FreshnessGuard's native integration uses Bifrost's supported shared-object plugin loading mechanism.

The project was developed against the inspected upstream Bifrost source revision:

```text
afdce01b50a78199f59e38117cd4d5952d038b07
```

The inspected upstream modules declared Go `1.27.3`.

Native plugin builds require a compatible toolchain and matching build conditions.

### Build the Plugin

From the project directory inside Ubuntu:

```bash
bash scripts/build-plugin.sh
```

### Run the Native Loader Smoke

```bash
python3 -m scripts.native_smoke --upstream "$PWD/work/bifrost"
```

### Build the Gateway

```bash
bash scripts/build-gateway.sh
```

### Run the Gateway Smoke

```bash
python3 -m scripts.gateway_smoke
```

The gateway smoke uses controlled local evidence and provider responses.

It exercises the real gateway and native plugin integration without requiring paid live-provider calls.

### Native Integration Notes

- Gateway and plugin must use compatible Go and CGO build configurations.
- The plugin must be loaded by a compatible dynamically linked gateway.
- The native plugin should not be copied into an arbitrary static release binary.
- Plugin configuration must be merged into the gateway's configuration.
- The verifier and gateway must have compatible network connectivity and shared authentication configuration.

When using WSL, do not assume a Windows loopback service is automatically reachable from the Ubuntu environment.

See the repository's integration documentation and build scripts for complete reproduction details.

---

## 🧰 Repository Structure

```text
freshnessguard-ai/
|
|-- .github/
|   `-- workflows/
|
|-- benchmarks/
|   |-- final_offline.py
|   `-- gateway-smoke.json
|
|-- demo/
|   |-- report.html
|   `-- report.json
|
|-- docs/
|
|-- freshnessguard/
|   `-- Core Python verification system
|
|-- frontend/
|   `-- React verification workbench
|
|-- integrations/
|   `-- Bifrost native integration
|
|-- scripts/
|   |-- build-plugin.sh
|   |-- build-gateway.sh
|   |-- gateway_smoke.py
|   `-- Native and demo utilities
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

Some generated benchmark outputs and local build artifacts may be absent from a fresh checkout until the relevant scripts are run.

---

## 🛡️ Reliability and Safety Design

FreshnessGuard is designed to make verification failures explicit.

### Deterministic Safeguards

The verifier checks evidence identifiers and exact quotations before accepting decisive results.

For supported release claims, it also applies official-source and version-evidence rules.

### Bounded Resource Usage

The current implementation includes limits on:

- Input size
- Extracted claims
- Time-sensitive claims selected for search
- Tavily search requests
- Model requests
- Retrieved source content
- Official-page fetches
- Concurrent verification operations

### Rate-Limit Handling

Upstream HTTP 429 responses can stop additional paid checks for the affected answer.

The report exposes the failure rather than manufacturing a successful verification.

The frontend can offer saved demonstrations when live verification is unavailable.

### Recursion Prevention

Internal model requests do not opt into FreshnessGuard verification again.

This prevents the verifier from recursively verifying its own model calls.

### Original Answer Preservation

Verification failures do not silently replace the original AI-generated response.

Unavailable verification is explicitly reported.

---

## ⚠️ Current Limitations

FreshnessGuard AI is a prototype and should not be treated as a universal fact-checking guarantee.

### Verification Scope

- The native integration currently supports compatible non-streaming text chat completions.
- Not every claim is extracted or checked.
- Release-specific deterministic checks cover a defined set of technologies and source policies.
- General semantic support still involves model judgment.
- Exact quotation matching proves textual provenance, not factual truth.
- Retrieval time does not establish that the source itself is current.
- An uncertain or unavailable result is not evidence that the original claim is correct.

### Operational Limits

- The documented development service is loopback-oriented.
- No public production deployment is established by the local test results.
- No complete multi-tenant authentication and isolation product is included.
- Verification can be affected by provider quotas, latency, and network failures.
- Some verification requests can exceed frontend time limits.
- A gateway timeout does not necessarily cancel work already executing in the Python service.

### Privacy and Security

Claims and evidence excerpts may be sent to the configured model provider.

Search queries are sent to Tavily.

Do not submit sensitive production data without an appropriate data-handling policy.

Retrieved source content is untrusted input. Deterministic checks reduce some risks but do not eliminate model-level prompt injection or factual errors.

---

## 📈 Future Improvements

Potential future work includes:

- Expanded official-source verification policies
- Broader claim categories
- Additional model-provider configurations
- More efficient evidence retrieval
- Improved report visualization
- Stronger production deployment controls
- Additional adversarial evaluations
- Broader live evaluation with documented datasets
- Better monitoring of verification coverage and failures

These are possible future directions, not claims about features already implemented.

---

## 📚 Technical Documentation

For deeper technical information, explore:

- `docs/` — architecture, integration notes, limitations, and submission material
- `benchmarks/` — benchmark methodology and scripted evaluations
- `integrations/` — native Bifrost plugin implementation
- `scripts/` — build, demonstration, and gateway validation tools
- `tests/` — Python regression tests
- `frontend/` — browser workbench

The source code and test fixtures are intended to support inspection and local reproduction.

---

## 👨‍💻 Developer

**Apoorv Anand**

Computer Science and Engineering  
RV College of Engineering, Bengaluru

GitHub: [@apoorv2202](https://github.com/apoorv2202)

Project Repository: [FreshnessGuard AI](https://github.com/apoorv2202/freshnessguard-ai)

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
