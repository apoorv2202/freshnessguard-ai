# Retrieval abstention and dated-release proof — 6 November 2026

## Diagnosis of the saved run

`work/post-semantic-single-live.json` records an available pipeline: one extraction, one Tavily search, one judge, 13,392.77 ms, no upstream errors. The model proposed **uncertain**, gave no citation IDs/quotes/correction, and explained that the evidence covered Django releases and Python 3.9.7 rather than the current latest stable Python series. No `semantic_validation` rejection was recorded: the guard did not overturn a proposed outdated verdict.

The saved query was:

`Python current latest stable release series official release information as of 2026-11-06`

| Retrieved source | Saved content/date | Assessment |
|---|---|---|
| `https://planet.python.org` | Feed updated 5 November, publication metadata 22 October 2026; PyCharm and Django news | Recent content, wrong evidence. A feed hosted on an official domain is not an authoritative Python release statement. Previously mislabelled primary |
| `https://python.org/downloads/release/python-397` | Python 3.9.7 artifact listing and implementation details; publication date absent | Historical artifact, older than the claimed series, without a newer stable-release fact |

Neither source can establish that a release newer than the claimed series exists. Changing the verdict to outdated from those snippets alone would fabricate a conclusion. **The observed abstention was justified; its immediate cause was retrieval quality/missing evidence, not a semantic rejection.** Whether the old verbose date-qualified query caused that ranking cannot be proved without another live run.

The old semantic guard also had a separate restriction: it required a recent literal latest assertion even to refute an old maximum. That was unnecessarily strong. A dated authoritative newer stable release is a counterexample; it need not be the exact newest release today.

## Retrieval changes

- Queries now cover latest/current/newest/most-recent version claims and natural-language version comparisons. Latest queries omit the alleged value; comparison queries ask for release history/dates with the compared versions, not confirmation of the alleged direction.
- Known-entity policy supplies trusted release-index URLs as retrieval hints (locations, not version answers). For Python, the query targets the downloads index and developer-guide versions page. It avoids the artificial as-of search phrase; check time remains in report metadata.
- Known feed/forum hosts are excluded from the Python search request; aggregator hosts no longer receive a primary-source badge.
- A version lookup can request at most eight results in the same basic Tavily request. The engine inspects at most eight, deduplicates URL aliases and prioritizes trusted release indexes, then official release artifacts. It supplies at most four bounded snippets to the judge.
- Source role/authority, actual query, returned/selected counts and retrieval strategy remain inspectable. Ranking is not a truth certificate. No extra search retry, direct page fetch or model call was added. A better live retrieval outcome has **not** yet been measured.

New planned query for this saved case:

`Python latest stable releases downloads versions release dates https://www.python.org/downloads/ https://devguide.python.org/versions/`

## Two different proof obligations

**Supported latest:** still requires eligible, current evidence that entails the complete latest claim. Historical announcements, support status and same-branch maintenance are not enough. The existing recent as-of rules, exact quotations, contradiction checks and future-date rejection remain.

**Outdated latest:** a quoted authoritative stable/final release fact with a version numerically greater in the claimed scope can refute the old maximum. The release/effective date must be explicitly present in the evidence and no later than the check date; it may be more than 30 days old. A historical announcement can establish that release event without establishing what is latest today.

The parser requires a concrete entity/version relation, explicit stable/final/GA wording, a single unambiguous version and literal dated context in a bounded source passage. It recognizes ISO and common English release-date formats. It preserves `as_of`, `effective_date` and `release_date` distinctions instead of relabelling publication/retrieval times as release dates. Metadata alone supplies no release proof.

Series comparisons use major/minor granularity: a same-series patch cannot refute a latest-series claim. Exact-version comparisons may use a newer patch. Preview/alpha/beta/RC and future/planned releases do not count as stable witnesses. LTS scope is not silently substituted. Known official withdrawal or unreleased-status contradictions block the affected witness. Unknown entities need a configured authority policy for the new historical-release proof path.

The judge prompt now states this asymmetry consistently: older evidence is not automatically irrelevant, but it cannot prove today's latest status. Corrections are still exact excerpts of accepted source quotes and describe a release counterexample; they do **not** assert an invented exact newest version. `semantic_validation.proof_kind`, dated `release_witnesses` and observed uncited witnesses document the proof used. No current Python version answer is hardcoded.

## Offline validation

100 Python tests and all eight synthetic protocol cases pass. Tests retain both saved failures: the previous stale-banner false-fresh result still abstains, and this missing-evidence run still abstains. New tests demonstrate a full controlled pipeline returning outdated from a synthetic, authoritative, dated newer stable release, with one simulated search/two simulated model calls, exact correction text, coverage 1 and score 0. These are regression fixtures, not live accuracy measurements.

Other regressions cover current indexes beyond the old four-result cutoff, aggregator authority, exclusion/request bounds, current/newest/most-recent queries, neutral comparisons, dates older than 30 days, human-readable dates, metadata-only dates, wrong entity, negated release facts, previews, future releases, series/patch scope, LTS and withdrawal conflicts. Existing quote, API-error, privacy, authentication and recursion tests remain green. All 6 native Go tests with race checking and 10 full synthetic gateway checks also pass; no native Go source or repository module files were changed.

Reproduce from the existing repository:

```powershell
python -m unittest discover -s tests -v
python -m benchmarks.run
```

`tests/fixtures/retrieval_abstention.json` preserves selected public saved evidence. `work/retrieval-diagnosis.json` contains the old/new query plan and corrected source-role assessment. The original measured benchmark was not edited.

## Safest next single live check — prepared, not executed

```powershell
python -m benchmarks.live --env-file .env --max-cases 1 --max-searches 1 --interval-seconds 0 --output work/release-index-single-live.json
```

Inspect the new query, selected release-index/artifact URLs, exact stable-release/date quote, numeric scope, `proposed_assessment`, `semantic_validation.release_witnesses` and final correction. Outdated is warranted only with the required counterexample. If the returned snippets still lack one, uncertain remains correct; do not manufacture a version/date to satisfy the expected label. Stop on 429/503. FreshnessGuard does not retry; gateway-internal retries remain outside its logical call counter. The benchmark imports new code directly; restart an existing standalone verifier separately to load changes.

No new paid live calls, credential changes, pushes or architectural rewrites were made. Current query ranking, date parsing and English release wording remain bounded heuristics; retrieval can still miss evidence. Final live stale recall and latency improvements are unmeasured.
