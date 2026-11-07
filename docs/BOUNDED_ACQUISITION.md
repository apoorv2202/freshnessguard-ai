# Bounded official-page evidence acquisition

Implemented and validated offline on 6 November 2026. No paid live calls, credential changes or GitHub pushes were made. Semantic acceptance rules are unchanged.

## Existing capabilities inspected

The repository has a Tavily Search client with `include_raw_content=false`; it has no Extract client or general HTTP fetching dependency. [Tavily's Extract API](https://docs.tavily.com/documentation/api-reference/endpoint/extract) offers single-URL extraction and text/Markdown formats. Its documented request options do not expose enforcement of redirect count or destination-IP validation. Fetching all search results with raw content would also add work to the normal path. This implementation therefore uses a small standard-library HTTPS client with explicit destination controls. It does not add a package or a Tavily extraction request.

## Flow and budgets

1. Claim extraction and the existing bounded Tavily search are unchanged.
2. For latest-version claims, run the existing semantic guard as an evidence-planning check. A sufficient current assertion or newer dated stable-release witness skips retrieval. This is not a verdict: the judge must still cite exact evidence and final validation still runs.
3. If evidence is insufficient, inspect only the four retained, ranked official sources and up to 16 link references per source. Prefer an allowlisted version-specific release link over an allowlisted index. Do not synthesize a URL from an alleged/new version number. A link's presence is only a retrieval hint, never proof.
4. Make at most **one GET per answer across all claims**, with no redirects, retries, link following or alternate-address attempts. The live benchmark additionally caps GETs across the **entire run**, using `--max-retrievals 0|1` (default 1).
5. Append the retrieved text as a separate source, retaining the original snippets, including contradictory evidence. The selected search source count remains at most four; judge sources can be five.
6. Send all evidence to the existing single Gemini judgment call. Normal single-claim cost remains one search, two logical model calls and zero or one direct GET. No second judgment call is introduced.
7. Apply unchanged quote, citation, correction and semantic validation. Missing dates, prereleases, ambiguous scope and inadequate evidence still require uncertain. Publication metadata or retrieval times are never substituted for a release/effective date.

The observed Python snippet explicitly exposes `python.org/downloads/release/python-3140/`. Offline target selection now selects that path using the configured `www.python.org` canonical origin, with the exact original reference and parent source `s1` retained. No page content, stable status or release date was invented or fetched during this investigation.

## Destination and resource controls

- Exact operator-configured host **and full path-pattern** allowlists, not arbitrary official-domain subdomains. Current rules cover selected Python release/index pages and Node.js release/download pages. Unknown entities and shared GitHub hosting have no automatic retrieval rule.
- HTTPS on port 443 only. Reject userinfo, queries, fragments, encoded paths, backslashes, control/whitespace characters, non-ASCII/trailing-dot hosts, dot segments and paths outside the release rules. Only a registered apex/www alias may be canonicalized to an index origin; the original reference is retained separately.
- Validate every DNS answer as public. Block loopback, private, link-local, metadata, multicast, mapped IPv6 and known transition/NAT64 address forms. A mixed public/private answer set is rejected.
- Pin the socket connection to a validated numeric address. No second DNS lookup occurs for HTTP/TLS; hostname certificate verification and SNI use the original allowlisted hostname. Environment proxy settings, cookies and API credentials are not used.
- Redirect policy: reject every 3xx, including same-host redirects. No Location target is requested. This deliberately sacrifices availability for predictable destination enforcement.
- Six-second network deadline includes DNS, connection, TLS, response headers and body. DNS wait is capped at one second using one daemon resolver; it cannot initiate an HTTP request after timeout. A socket watchdog bounds slow header/body reads. Socket phases also use the remaining deadline. There are no retries.
- Headers are bounded to 32,768 bytes; response body to 256,000 bytes. Reject oversized declared/streamed bodies, compressed content and media types other than HTML/plain text. Decoding is strict UTF-8; unsupported encodings abstain rather than guess.
- HTML is parsed without browser execution, external resources or embedded fetches. Script/style/template/head/navigation/hidden containers are omitted, nesting is capped at 128, and visible text is limited to 16,000 characters. Truncation is explicit. This is deterministic text extraction, not complete browser/CSS rendering.

Network/safety failures are recorded in `claim.source_retrieval` with a safe error code. They do not trigger another URL or model call. The original snippets are still judged once. Acquisition is optional, so its failure is a degraded evidence path rather than a failed claim-extraction/model API call; it must not be mistaken for successful retrieval.

## Provenance and trust

The new source records requested URL, parent source, discovery method, original URL reference, retrieval time, raw-body SHA-256, included-text SHA-256, byte count, content type and text-truncation status. Citations refer to the newly retrieved source ID, not the parent snippet. Exact quotes must occur in its actual included extracted text; the normal whitespace-only matching rule remains unchanged. Quotes are not checked against invented summaries or a link's label. No fetched publication date is fabricated.

The existing judge system prompt explicitly treats source text as untrusted data and ignores embedded instructions. Retrieval never executes source content, uses it as configuration, or asks a model to generate the next URL. Existing report rendering escapes text. No raw HTTP request/header/environment logging is added.

## Structured timings

Every completed verifier report has `metrics.timings_ms`:

- `extraction`: claim model call and extraction validation, including failure time.
- `search`: search API call, including failure time.
- `source_retrieval`: candidate selection and optional source retrieval, including failure time; zero when skipped before selection.
- `judgment`: the single evidence judgment call, including failure time.
- `semantic_validation`: the planning checks plus final semantic guard.
- `total`: total verifier time, matching `metrics.latency_ms`.

These are aggregate stages across claims. Other local bookkeeping remains in total; stage values and independently calculated medians are not expected to sum exactly to total. Source retrieval has its own `source_retrieval_calls` counter and is not misreported as a Tavily credit or another search.

## Offline validation

**130 Python tests pass**, including the complete fetch/text-extraction/judge/semantic path with mocked transport. Regressions cover accepted dated newer stable releases; missing dates; prereleases; unchanged sufficient-snippet fast paths; exact provenance; fabricated-quote rejection; one-GET budgets across claims; observed Python artifact-link selection; blocked URLs; mixed/private/transition DNS; redirect refusal; DNS/connect/TLS/body timeouts; TLS hostname/IP pinning; header/body/text limits; compressed/binary content; safe HTML extraction; and bounded nesting. Existing authentication, privacy, recursion, API-error and semantic tests remain green.

All **8 synthetic protocol cases** and **4 acquisition scenarios, 25 iterations each**, pass. Compile checks pass. No native Go source changed; native Go/gateway checks were not repeated for this Python-only change.

```powershell
python -m unittest discover -s tests -q
python -m benchmarks.run
python -m benchmarks.acquisition
```

Measured local medians from `benchmarks/acquisition-results.json`:

| Synthetic case | GETs | Total ms | Retrieval-stage ms | Semantic-stage ms |
| --- | ---: | ---: | ---: | ---: |
| Sufficient snippet | 0 | 0.90 | 0 | 0.6212 |
| Dated release retrieved | 1 | 1.01 | 0.1340 | 0.5900 |
| Missing release date | 1 | 0.99 | 0.1649 | 0.4480 |
| Preview retrieved | 1 | 1.23 | 0.2141 | 0.4983 |

Search, model and network are mocked in this benchmark; only local planning, parsing and validation run. These are **not live latency or accuracy measurements**. Real retrieval can add up to its six-second network budget plus bounded local work, and a larger evidence payload can affect model latency. The report records timings rather than assuming this is faster live.

## Single bounded live validation plan — not executed

From the existing repository, after reviewing the offline results:

```powershell
python -m benchmarks.live --env-file .env --max-cases 1 --max-searches 1 --max-retrievals 1 --interval-seconds 0 --output work/targeted-source-single-live.json
```

Maximum: one search, one allowlisted official-page GET and two logical model calls. No FreshnessGuard retries or additional judgment. Stop on upstream overload; gateway-internal retries are outside these logical counters.

Inspect selected target and parent source; acquisition status; byte/text bounds and hashes; actual retrieved source text; proposed citation IDs and quotes; `semantic_validation.release_witnesses`; final correction; and every timing stage. Accept outdated only if the final quote genuinely proves an explicitly dated newer stable release in the claimed scope. Redirect, blocked URL, missing date, unsupported encoding or insufficient text must preserve abstention. `--max-retrievals 0` disables acquisition for a future explicitly authorized baseline; no paired live run was made here.

The real official page/TLS path and live stale recall remain unmeasured. The 16,000-character/paragraph limits can miss relevant text; JavaScript-only pages, redirects and unsupported page formats deliberately remain unavailable. Acquisition remains limited to latest-version claims and explicitly configured hosts/paths.
