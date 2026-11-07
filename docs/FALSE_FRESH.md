# False-fresh investigation — 6 November 2026

Later refinement: `RETRIEVAL_ABSTENTION.md` distinguishes proof of today's latest from proof that a newer stable release already existed. The latter may use an older, explicitly dated authoritative announcement; the historical false-fresh case here remains rejected. Query wording and source selection were also improved. The descriptions below record the earlier guard revision.

## What the saved live run actually shows

`work/full-live-check.json` records a complete, available pipeline: one extracted claim, one Tavily search, two logical model calls, 7,728.93 ms, no upstream errors. The proposed and accepted verdict was `supported` for “The latest stable Python release series is 3.11.” Quote provenance passed, but temporal entailment did not.

| Source | Saved evidence | Why it cannot establish the current latest series |
|---|---|---|
| `s1`: [Python community thread](https://discuss.python.org/t/python-latest-stable-version/24563) | Published 7 March 2023; a reply calls 3.11.2 latest | Community authorship, historical time context; an official host is not an official current release statement |
| `s2`: [Python 3.9.0 release page](https://www.python.org/downloads/release/python-390) | Body says release date 5 October 2020 and labels the page legacy; embedded banner calls 3.11 the latest feature series | A version-specific historical snapshot can retain an old “now/latest” banner. Saved publication metadata (31 October 2025) is neither that release date nor proof of currentness |
| `s3`: same release path without `www` | Same text, no publication date | Duplicate evidence, not independent corroboration |

All were retrieved on 6 November 2026. Retrieval time does not move their assertions into that effective time. The judge's explanation claimed multiple official/community sources confirmed latest status; it failed to distinguish the historical assertion from a current one. This exact run is **not merely** a “still supported” misreading: the snippets explicitly say “latest,” but in an obsolete context. The broader supported-versus-latest mistake is covered separately by regressions.

The generated original search query was not stored, so its role in retrieving these pages cannot be proved. The returned results themselves were inadequate. No new model, Tavily or public web requests were needed for this investigation.

## Root causes

1. Retrieval returned old discussion/legacy pages, not a current release/status assertion.
2. Domain authority classified `discuss.python.org` as primary and did not distinguish version snapshots from current information.
3. The model ignored the time reference despite the existing prompt; its self-reported no-conflict flag was insufficient.
4. Verdict validation established source membership, exact quotes and non-future dates, but not whether the quoted predicate/time/scope entailed the complete claim.

Thus citation provenance of 1.0 and a primary-domain count were compatible with a false-fresh verdict. Neither metric is factual correctness.

## Changes

- Added an independent, bounded latest-version semantic guard in `freshnessguard/semantics.py`, applied after the existing citation checks and before accepting either decisive verdict.
- Requires an affirmative, entity-matching latest assertion in the same stable/LTS channel and version/series scope. Stable, supported, latest patch in an old branch, latest LTS and latest stable overall are not interchangeable. Questions, speculative/negated language and prereleases do not establish stable support.
- Requires explicit dated effective/as-of evidence in the accepted assertion. Retrieval/publication metadata alone is not enough. The current conservative eligibility window is 30 days, rejects future dates, and is an engineering heuristic—not a guarantee a version has not changed since the stated date. Undated or unsupported formats abstain.
- Rejects historical version snapshots and community sources as proof of current latest status. Known-entity policies require eligible official sources; unknown entities retain explicitly `unassessed` authority rather than being falsely labelled official.
- Checks all retrieved eligible assertions for contradiction, including uncited newer versions. It compares numeric versions and respects release-series granularity. Conflicting current assertions abstain even when the model reports no conflict.
- Neutral latest-version queries omit the alleged version, use entity/scope/channel plus check date, and are saved for audit. This changes no search/model call budgets.
- Collapses obvious `www`/non-`www` URL aliases; marks source roles before judging; strengthens the prompt about historical “now/latest” notices.
- Keeps `proposed_verdict`, a bounded provenance-validated `proposed_assessment`, and semantic rejection reasons for audit. Rejected decisions clear accepted quotes/citations/corrections and become `uncertain`; original answers remain unchanged.

No Python version answer is embedded in production rules. Tests use arbitrary Widget versions as well as the saved Python evidence. No third-party dependencies or architecture replacement were introduced. Authentication, recursion prevention, structured API failures and strict quote validation remain in place.

## Offline reproduction and result

`tests/fixtures/stale_latest_python.json` contains selected public evidence and a reconstructed accepted decision. The raw model completion was not saved; `evidence_conflict=false` is inferred from acceptance by the old validator, not claimed as a new observation.

```powershell
python -m unittest discover -s tests -v
python -m benchmarks.run
python -m benchmarks.semantic_replay --input work/full-live-check.json --output work/false-fresh-replay.json
```

The saved proposal now becomes **uncertain**, score **null**, coverage **0**, accepted decisive citations **0**, false-fresh count **0**. It remains a false negative against the benchmark's independent `outdated` label: stale recall is **0**, not improved accuracy. The old evidence cannot justify inventing a current replacement version. Original live measurements are retained separately; replay makes **zero API calls** and is not a new live benchmark.

78 Python tests and all 8 synthetic protocol cases pass. Tests cover the exact saved failure, support-status confusion, historical/undated/future evidence, snapshot URLs, uncited contradictions, scope/channel mismatches, entity mismatch, questions/speculation, numeric version comparison and legitimate dated supported/outdated cases. All 10 synthetic native gateway checks and 6 native Go tests with race checking pass. Native tests used cached dependencies and a temporary module override to the existing pinned source; repository Go module files were not changed.

## Limits and next single live test

This is a conservative English-language guard for explicit numeric version superlatives, not a general entailment model. It intentionally increases abstention when dates or context cannot be resolved. The 30-day window can still contain stale assertions; cache lag, omitted evidence and model errors remain risks. Clear present-day official evidence and independent quality evaluation are still needed. Do not market provenance or these regression passes as general detector accuracy.

After checking quota, prepare one controlled live verification (not executed during this fix):

```powershell
python -m benchmarks.live --env-file .env --max-cases 1 --max-searches 1 --interval-seconds 0 --output work/post-semantic-single-live.json
```

This permits one extraction, at most one Tavily search and one judge, without FreshnessGuard retries. Gateway-internal retries are outside this logical call counter. Inspect `search_query`, source roles, dates, `proposed_assessment`, `semantic_validation`, final verdict and accepted quotes. `uncertain` is acceptable when current evidence is absent; `supported` requires human review of the whole latest-version assertion. Stop on 429/503. Restart any long-running verifier separately to load changed code; this benchmark imports the new code directly.
