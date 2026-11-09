# Troubleshooting and verified local workflow

## Windows service

From the existing project directory, `.env` is already configured. Do not copy an example file over it. Confirm configuration without exposing secrets:

```powershell
python -c "from freshnessguard.config import load_env; import os; load_env('.env'); print(os.environ.get('BIFROST_MODEL')); print({k:bool(os.environ.get(k)) for k in ['TAVILY_API_KEY','BIFROST_VIRTUAL_KEY','FRESHNESSGUARD_TOKEN']})"
python -m unittest discover -s tests -v
python -m freshnessguard.cli serve --env-file .env
```

If port 8765 is occupied by your existing verifier, stop it with Ctrl+C in its terminal and restart to load the fixes. The app does not hot-reload. Use `--port 8766` for a separate verifier if preserving the old process is necessary. Do not restart or reconfigure the working Bifrost gateway just to run offline tests.

`/verify` and `/annotate` require `Authorization: Bearer <FRESHNESSGUARD_TOKEN>`; the Bifrost model client separately sends its virtual key with `x-bf-vk`. These credentials have different purposes. Never print either header during recording.

## HTTP 429 / 503

Recent extraction and judgment 429s were Gemini provider responses. The local gateway records showed `RESOURCE_EXHAUSTED` for the free-tier `generate_content_free_tier_requests` metric and a daily limit of 20 for the configured model. The virtual key had no linked key, team, customer, or provider rate limit. This is an observation about that configuration, and other projects or tiers may differ.

Check the configured Google project's quota and reset status. Wait for available quota or have the account owner arrange approved capacity for that project. A short provider retry hint does not establish that daily quota has reset. FreshnessGuard surfaces a bounded numeric delay only when it receives a usable HTTP `Retry-After` header. The inspected gateway logs do not retain those headers.

FreshnessGuard does not retry automatically. A 429 or judgment timeout leaves later time-sensitive claims unverified and stops further paid checks for that answer. The Verify page offers the saved replay while keeping the original answer in its tab. For a partial benchmark, inspect `case_count`, warnings, missing claims, and evaluation rows before interpreting the results.

## Incomplete JSON or truncated generation

Gemini thinking can consume the output budget. The configured Flash request uses minimal reasoning; raising the bounded output cap alone may not resolve quota or backend parameter support. Truncated/filtered verification JSON is reported as unavailable. Truncated/filtered original gateway answers are preserved and explicitly left unverified. Do not call a fragment a factual claim or publish a score for it.

## Uncertain versus supported

Read `reason`, `validation_error`, `verification_error`, publication metadata and source URLs. A quote mismatch or unsupported correction is a deliberate abstention. Search relevance does not establish truth. An official-domain badge is provenance only, not a factual guarantee. Input-link warnings do not prove a URL is fabricated; linked contents were not fetched.

## WSL native builds (verified in this workspace)

Native Go plugins require the matching Linux Go compiler, CGO, dependency graph and libc. The available task-local compiler is in `../../work/toolchain/go/bin`, and the pinned upstream checkout is `../../work/bifrost` relative to this project. In Ubuntu, from this project:

```bash
export PATH="$(realpath ../../work/toolchain/go/bin):$PATH"
bash scripts/build-plugin.sh "$(realpath ../../work/bifrost)"
python3 -m scripts.native_smoke --upstream "$(realpath ../../work/bifrost)"
bash scripts/build-gateway.sh "$(realpath ../../work/bifrost)"
python3 -m scripts.gateway_smoke
```

For a fresh checkout, install matching Go 1.27.3 plus GCC/libc development headers and use the build script's default ignored `work/bifrost` source location. Build scripts accept existing paths and now resolve relative paths before changing directories. `build-gateway.sh` produces an API-only gateway with an explicit dashboard placeholder. Build the upstream UI separately for a full dashboard.

## Native live test under WSL NAT

This machine uses NAT: WSL cannot reach Windows `127.0.0.1:8080`. The isolated test helper uses WSL interop, rather than changing networking or exposing a credential-bearing server. A local Linux bridge invokes `scripts/live_worker.py` using Windows Python; the worker reads `.env` itself and calls the existing Windows gateway. Secrets never appear in command arguments. Native Bifrost and its post-hook still execute for real. This bridge is test infrastructure, not a proposed production architecture.

After Gemini quota is available, run in PowerShell from the existing project:

```powershell
$project = (Get-Location).Path
$linuxProject = (wsl -d Ubuntu -- wslpath -u $project).Trim()
$windowsPython = (Get-Command python).Source
$linuxPython = (wsl -d Ubuntu -- wslpath -u $windowsPython).Trim()
wsl -d Ubuntu --cd $linuxProject -- python3 -m scripts.native_live --windows-python $linuxPython --windows-project $project
```

The helper uses one generation, one extraction, at most one search and one judge, without retries. It requires the matching gateway/plugin built above, starts only isolated temporary services, and stops them when done. Existing Windows ports 8080 and 8765 remain untouched. Review `work/native-live-result.json`; a meaningful complete answer, no provider failures and relevant evidence are required. The first run demonstrated transport but failed semantic review; it must not be reused as a success claim.

## Privacy and packaging

`.env`, `work/`, compiled plugins and private raw benchmark outputs are ignored. `scripts.publish_validation` publishes selected metrics and URLs and checks them against configured credential values. Public HTML samples contain only public test claims and retrieved evidence. Before packaging or recording, review answers as well as keys: a secret-free API request can still contain private business information. No push, deployment or hackathon submission is performed automatically.
