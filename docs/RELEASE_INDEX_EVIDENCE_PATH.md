# Release-index live evidence investigation

Investigated `work/release-index-single-live.json`, checked at 2026-11-06T16:09:00.455904+00:00. No paid calls were made for this investigation. The original measured file is unchanged.

## Finding

The model proposed **outdated**; citation provenance and exact quote validation passed, but semantic validation rejected the proposed proof. This is not an extraction/API failure and differs from the previous run where the model itself abstained. The retained official snippets suggest newer releases but contain no complete, explicitly dated stable-release witness usable under the existing proof rules. Safe abstention remains correct for this evidence.

The exact rejection was:

> No current dated eligible quote establishes a newer version in the claimed scope

`release_witnesses`, `observed_release_witnesses` and `observed_versions` were all empty. `proof_kind=current_latest_assertion` was the fallback label, not evidence that such an assertion had been found. The revised explanatory error distinguishes a current assertion from a historical dated release witness; no acceptance criteria changed.

## Evidence path and limits of the record

1. Extraction succeeded for "The latest stable Python release series is 3.11".
2. Tavily basic search was called once, max_results=8, include_domains=[python.org], exclude_domains=[planet.python.org, discuss.python.org], include_raw_content=false, include_answer=false and include_published_date=true. These options are reconstructed from the current matching client/engine code, not a retained HTTP request. Full URLs in a search query are hints, not a guarantee of returning those endpoints.
3. The report counts eight returned results and four selected sources. The **other four result URLs, titles, contents, dates and initial ranks were not saved**. There is no retained raw Tavily response. Available local gateway logs predate this run and do not recover that response. It is impossible to say whether selection discarded a better source, or whether the requested download/version indexes were ever returned. They were not selected.
4. The four source objects below are the evidence supplied to the Gemini judge: the engine passes `claim.sources` directly. The replay asserts this equality. Their content lengths are 1412, 828, 1389 and 1437 characters respectively, all below the verifier's 5000-character cutoff. No local content truncation occurred. Ellipses and truncated phrases already exist in the saved search snippets; their origin upstream cannot be determined from the record.
5. Gemini proposed outdated using s1 and s4. Its exact proposed assessment is retained below. `evidence_conflict=false` was not retained in the proposed-assessment object; it is reconstructed for replay because execution reached semantic validation after the conflict check. No raw Gemini response or transport envelope is claimed to be available.
6. Both citations matched their sources verbatim and the correction matched a quoted excerpt. These checks prove provenance, not entailment.
7. At semantic validation, the **s1 quote has no explicit release/effective date**. The **s4 quote has no explicit stable/final channel statement and no release/effective date**. Neither is a dated stable witness. No qualifying full-source witness was found either. Source publication dates and RSS `date:` entries cannot be silently relabelled release dates.

There is no demonstrated valid dated stable-release fact that was lost. The first demonstrated rejection is the semantic witness check after quote validation. The earlier retrieval/selection loss boundary remains unknown because four candidates were not persisted.

## Exact search query

```text
Python latest stable releases downloads versions release dates https://www.python.org/downloads/ https://devguide.python.org/versions/
```

## All retained search snippets / judge evidence

These are the four retained results, not a reconstruction of all eight. Content blocks below are exact saved strings; dates are publication metadata, not asserted release dates.

### s1: Posts tagged "releases" | Python Insider

URL: https://blog.python.org/tags/releases

Publication metadata: `None`. Retrieved: `2026-11-06T16:09:00.455904+00:00`. Role: `release_index`; official-domain flag: `True`.

```text
releases

### Python 3.12.12, 3.11.14, 3.10.19 and 3.9.24 are now available!

Thomas Wouters·

 is here!

Hugo van Kemenade·

!Two snakes enjoying a pie with 3.14 on the top and π crimping Python 3.14.0 is now available python.org/downloads/release/python-3140/ This is the stable re...

releases

### Python 3.14.0rc3 is go!

Hugo van Kemenade·

It’s 🪄 finally 🪄 the final 3.14 release candidate!  Note: It’s another magic release. We fixed anot...

releases [...] Hugo van Kemenade·

Note: 3.15.0a4 was accidentally built against from 2025-12-23 instead of 2026-01-13, so this 3.15.0a5 is an extra release correctly built against 2026-01-14...

releases

### Python 3.15.0 alpha 4

Hugo van Kemenade·

Edit: This 3.15.0a4 was accidentally built against \ from 2025-12-23 instead of 2026-01-13, so 3.15.0a5 is an extra release correctly built against 2026-01-1...

releases

### Python 3.15.0 alpha 3

Hugo van Kemenade· [...] Ned Deily·

Python 3.7.2 and 3.6.8 are now available. Python 3.7.2 is the next maintenance release of Python 3.7, the latest feature release of Python. You can find Pyth...

releases

### Python 3.7.2rc1 and 3.6.8rc1 now available for testing

Ned Deily·

Python 3.7.2rc1 and 3.6.8rc1 are now available. 3.7.2rc1 is the release preview of the next maintenance release of Python 3.7, the latest feature release of ...

releases

### Python 3.7.1 and 3.6.7 are now available

Ned Deily·
```

### s2: Python Releases

URL: https://www.python.org/downloads/feed.rss

Publication metadata: `None`. Retrieved: `2026-11-06T16:09:00.455904+00:00`. Role: `unclassified`; official-domain flag: `True`.

```text
Python Releases Python releases from Python.orgen-usSun, 25 Oct 2026 21:02:29 +0000Python 3.11.18 date: 2026-10-25 21:02:29+00:00Sun, 25 Oct 2026 21:02:29 +0000 3.13.18 date: 2026-10-25 19:09:44+00:00Sun, 25 Oct 2026 19:09:44 +0000 3.12.16 date: 2026-10-25 18:35:25+00:00Sun, 25 Oct 2026 18:35:25 +0000 3.14.10 date: 2026-10-25 04:15:45+00:00Sun, 25 Oct 2026 04:15:45 +0000 3.15.2 date: 2026-10-25 04:15:38+00:00Sun, 25 Oct 2026 04:15:38 +0000 3.13.17 date: 2026-10-21 14:22:30+00:00Wed, 21 Oct 2026 [...] 21 Oct 2026 14:22:30 +0000 3.14.9 date: 2026-10-21 13:08:09+00:00Wed, 21 Oct 2026 13:08:09 +0000 3.15.1 date: 2026-10-21 09:59:50+00:00Wed, 21 Oct 2026 09:59:50 +0000 3.16.0a1 date: 2026-10-13 19:02:12+00:00Tue, 13 Oct 2026 19:02:12 +0000 install manager 26.4 date: 2026-10-09 14:58:02+00:00Fri, 09 Oct 2026 14:58:02 +0000
```

### s3: Blog - Page 3 | Python Insider

URL: https://blog.python.org/blog/3

Publication metadata: `Tue, 17 Dec 2024 00:00:00 GMT`. Retrieved: `2026-11-06T16:09:00.455904+00:00`. Role: `unclassified`; official-domain flag: `True`.

```text
releases

### Python 3.12.12, 3.11.14, 3.10.19 and 3.9.24 are now available!

Thomas Wouters·

 is here!

Hugo van Kemenade·

!Two snakes enjoying a pie with 3.14 on the top and π crimping Python 3.14.0 is now available python.org/downloads/release/python-3140/ This is the stable re...

releases

### Python 3.14.0rc3 is go!

Hugo van Kemenade·

It’s 🪄 finally 🪄 the final 3.14 release candidate!  Note: It’s another magic release. We fixed anot...

releases [...] Hugo van Kemenade·

Note: 3.15.0a4 was accidentally built against from 2025-12-23 instead of 2026-01-13, so this 3.15.0a5 is an extra release correctly built against 2026-01-14...

releases

### Python 3.15.0 alpha 4

Hugo van Kemenade·

Edit: This 3.15.0a4 was accidentally built against \ from 2025-12-23 instead of 2026-01-13, so 3.15.0a5 is an extra release correctly built against 2026-01-1...

releases

### Python 3.15.0 alpha 3

Hugo van Kemenade· [...] # All Posts

349 posts · Page 3 of 18

### Python 3.15.0 alpha 7

Hugo van Kemenade·

The penultimate 3.15 alpha is out!

### CPython: 36 Years of Source Code

Stan Ulbrych·

An analysis of the growth of CPython's codebase from its first commits to the present day

history

### Python 3.12.13, 3.11.15 and 3.10.20 are now available!

Thomas Wouters·

Python Releases For Your Security! New security releases for 3.10, 3.11 and 3.12 are now available.

releases
```

### s4: 2025 Posts | Python Insider

URL: https://blog.python.org/blog/year/2025

Publication metadata: `Tue, 16 Dec 2025 00:00:00 GMT`. Retrieved: `2026-11-06T16:09:00.455904+00:00`. Role: `unclassified`; official-domain flag: `True`.

```text
releases

### Python 3.12.12, 3.11.14, 3.10.19 and 3.9.24 are now available!

Thomas Wouters·

 is here!

Hugo van Kemenade·

!Two snakes enjoying a pie with 3.14 on the top and π crimping Python 3.14.0 is now available python.org/downloads/release/python-3140/ This is the stable re...

releases

### Python 3.14.0rc3 is go!

Hugo van Kemenade·

It’s 🪄 finally 🪄 the final 3.14 release candidate!  Note: It’s another magic release. We fixed anot...

releases [...] releases

### Python 3.13.10 is now available, too, you know!

Thomas Wouters·

The latest version of Python 3.13 is now available! Python 3.13.10  This is the tenth maintenance rel...

releases

### Python 3.14.1 is now available!

Hugo van Kemenade·

!Two snakes enjoying a pie with 3.14 on the top and π crimping This is first maintenance release of Python 3.14 Python 3.14.1 is the first maintenance release...

releases

### Python 3.15.0 alpha 2

Hugo van Kemenade· [...] releases

### Python 3.14.0rc2 and 3.13.7 are go!

Hugo van Kemenade·

Not one but two expedited releases! 🎉 🎉 Python 3.14.0rc2 It’s the ~final~ 🪄 penultimate 🪄 3.14 release candidate!

releases

### Python 3.13.6 is now available

Thomas Wouters·

The latest version of Python 3.13 is now available! []( 3.13...

### Python 3.14 release candidate 1 is go!

Hugo van Kemenade·

It’s the first 3.14 release candidate!  This is the first release candidate of Python 3.14 This relea...

releases
```

## Model's retained proposed assessment

```json
{
  "verdict": "outdated",
  "reason": "Evidence shows that Python 3.14.0 was released as a stable version, and maintenance releases for 3.14.1 and 3.13.10 have also been issued by the checked_at date.",
  "citation_ids": [
    "s1",
    "s4"
  ],
  "quotes": [
    {
      "source_id": "s1",
      "text": "Python 3.14.0 is now available python.org/downloads/release/python-3140/ This is the stable re..."
    },
    {
      "source_id": "s4",
      "text": "Python 3.14.1 is the first maintenance release"
    }
  ],
  "correction": "Python 3.14.0 is now available python.org/downloads/release/python-3140/ This is the stable re..."
}
```

## Exact offline diagnostic replay

`tests/fixtures/release_index_live_evidence.json` preserves the selected public evidence and proposed decision; its provenance explicitly labels the inferred conflict field. `work/release-index-offline-audit.json` contains the new diagnostic replay. The measured live run itself is not edited.

The release parser examines original bounded passages, not combined invented statements. New `semantic_validation.release_evidence_checks` records source/quote scope, authority eligibility, examined/accepted passage counts and rejection-code counts. Each passage records its **first failed predicate**; these counts are not independent votes, nor an exhaustive entailment analysis.

- Full s1: 67 candidate passages, zero accepted. Counts: stable/final channel missing 40; entity not matched 20; nonunique version 5; preview/planned/negated/withdrawn 2.
- Full s2: the single-line 828-character RSS snippet contains no passage within the 800-character quote bound. It also mixes versions, previews, an install manager and unlabeled `date:` entries; merely increasing the bound would not supply a clear stable-release/date relation. No parser relaxation is justified.
- Full s3: 79 passages, zero accepted. Counts: stable/final channel missing 37; entity not matched 35; nonunique version 5; preview/planned/negated/withdrawn 2.
- Full s4: 80 passages, zero accepted. Counts: stable/final channel missing 55; entity not matched 11; nonunique version 5; preview/planned/negated/withdrawn 9.
- Quoted s1: one passage, rejected for missing explicit release/effective date.
- Quoted s4: one passage, rejected first for missing explicit stable/final channel. Inspection also confirms it has no date.

## Smallest correction made

No speculative query, ranking, prompt, parser-acceptance, verdict or budget change was made. The observability gap is corrected:

- `freshnessguard/engine.py`: retains a bounded candidate trace for the first eight results, in original result order, with result position, authority/ranking metadata, selected source ID or exclusion reason, content length, truncation flag and hashes. Exclusion reasons distinguish malformed results, invalid URLs/content, duplicate URLs and the four-source selection cap. URL user/password forms are rejected. Invalid URL parsing is safely handled.
- The new trace deliberately omits URL paths/query strings, extra titles/snippets, arbitrary upstream fields, requests, headers, credentials and environment values. URL hashes correlate selected entries with already retained source URLs; hosts and ranking distinguish a preferred index from an excluded candidate. This metadata identifies a selection loss, but cannot recover discarded snippet text. The existing report already contains selected source text and the claim; this change adds no raw request logging.
- `freshnessguard/semantics.py`: emits actual parser failure codes and a clear no-bounded-passage reason; improves the misleading generic error wording. It does not change what qualifies as proof.
- `tests/test_evidence_diagnostics.py` and its fixture: five new offline regressions for the actual rejected verdict, publication-date non-substitution, exact judge source payload, candidate filtering/caps/truncation, and diagnostic privacy/bounds. Existing positive dated-release tests continue to pass.

## Validation and next evidence step

All **105 Python tests** and **8 synthetic benchmark cases** pass; no external API is used. The first restricted test run encountered temporary-file/localhost permissions; rerunning with local test access passed the full suite. No Go files changed, so native Go/gateway tests were not repeated for this diagnostic-only change. Existing security, citation, API failure, privacy and recursion tests remain green.

Reproduce offline:

```powershell
python -m unittest discover -s tests -q
python -m benchmarks.run
```

A single search can establish outdated status if a returned snippet includes an authoritative, explicit dated newer stable-release fact and the model quotes it. It cannot guarantee that evidence: basic search snippets often omit release dates, combine listing entries and truncate channel descriptions. One search also cannot guarantee the exact latest current status. Adding more results to the same truncated evidence format is not proof of an improvement.

Do not spend another paid query merely to repeat this case. Before another live benchmark, a separately bounded evidence-acquisition step could be evaluated using an official artifact link already exposed in search evidence (for example the python-3140 link in s1), if its exact page text can be obtained and safely validated. This is a proposed evidence step, **not executed or implemented**, and must respect fetch/SSRF, size, quote, authority and budget controls. It must not invent stable status or attach archive publication dates to individual releases. No automatic follow-up fetch/search or retries were added.

Remaining limitations: the four discarded results are unrecoverable; ranking changes are not justified; full raw model responses are not saved; the strict English/date passage parser remains bounded; basic snippets may stay insufficient. The candidate trace is intentionally metadata-only and cannot establish the semantics of discarded content. The saved evidence correctly remains uncertain. No credentials were read or changed; nothing was pushed to GitHub.
