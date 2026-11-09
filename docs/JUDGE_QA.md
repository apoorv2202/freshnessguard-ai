# Judge Q&A

## What does FreshnessGuard add to a web-enabled chatbot?

It checks an existing answer claim by claim and attaches a report without rewriting the answer. Bifrost routes the model work and provides the opt-in gateway extension point. Tavily supplies search evidence independently of the answer. FreshnessGuard retains exact source excerpts, applies deterministic version checks for covered release claims, and surfaces uncertainty when proof is missing. The project demonstrates that verification contract and its gateway delivery. It does not establish superior accuracy to other web-enabled systems. [Architecture and code path](INTEGRATION_PROOF.md)

## Why did similar Python claims receive different verdicts?

“3.11 is the latest stable series” can be disproved by one dated, qualifying newer stable release. Proving a specific series **is** latest requires a current dated assertion in the right scope. An old release announcement can supply the first kind of proof and still be insufficient for the second. In the saved abstention, the model quoted the stable-release line and omitted the date. The same source supports an outdated verdict when the complete passage is cited. Mixed answers also share bounded request budgets, and each claim can receive different evidence. [Captured and replayed example](INTEGRATION_PROOF.md#sanitized-example-from-the-saved-record)

## What do coverage and freshness mean?

**Evidence coverage** divides evidence-backed decisive claims by all extracted time-sensitive claims. Uncertain claims lower coverage. Historical and other `not_checked` claims are excluded. **Freshness** divides supported claims by the evidence-backed supported and outdated claims. It displays **Not assessed** when there are none. For example, one outdated claim and one uncertain claim give 50% coverage and 0% freshness. Coverage is scoped to extracted claims, so a missed claim can still escape the report. [Field semantics](FRONTEND_CONTRACT.md#field-semantics)

## Can the model hallucinate a citation?

It can propose one. FreshnessGuard rejects unknown source IDs, quote text absent from the cited source, and corrections that are not cited excerpts. A valid URL and a matching quote establish provenance. Covered version claims also need evidence that passes the separate release rules. The 25-case suite rejected a fabricated quote, an unknown ID and an unsupported correction. A separate captured 9 November quote mismatch still abstains under offline validation. General semantic entailment remains an open limitation. [Benchmark findings](BENCHMARK_REPORT.md) · [Captured mismatch](../tests/fixtures/nov09_live_citation_mismatch.json)

## How do quotas and timeouts affect a demo?

The verifier handles HTTP 429 explicitly and can surface a bounded retry delay when the upstream provides a usable value. It does not automatically retry. After an upstream rate limit or judgment timeout, it skips remaining paid claim checks for that answer. By default it processes up to five time-sensitive claims, with at most six logical model calls, five searches and two official-page fetches per answer. Optional evidence reuse is scoped to the current request. For a demo interruption, switch to **Saved Demo → Offline corrected evidence** and say it is an offline replay of captured evidence. [Limits and failure behavior](../README.md#limits-and-failure-behavior) · [Demo script](DEMO_SCRIPT.md)

## How fast is it?

One earlier decisive browser run took **9.66 seconds** end to end. A different captured abstention took **11.92 seconds**, with about **4.02 seconds for extraction**, **2.74 seconds for search**, **0.28 seconds for the official fetch** and **4.81 seconds for judgment**. These are individual observations. Multi-claim requests can exceed the browser adapter's 120-second deadline, and a user who stops waiting may leave bounded backend work in progress. Fixture timings describe local processing. [Live measurements](LIVE_RESULTS.md) · [Captured stage timings](TARGETED_LIVE_DIAGNOSIS_AND_FREEZE.md#seven-answers)

## Does 25/25 mean the system is 100% accurate?

It means every case in a fixed synthetic regression suite matched its expected outcomes. The real verifier processed scripted extraction, search, judgment and retrieval responses. This checks how it handles known evidence and failure modes. An independent live dataset would be needed to estimate search quality, model behavior, error rates and real latency. The decisive browser smoke, captured abstention, offline replay and native gateway fixture are separate results. [Benchmark methodology](BENCHMARK_REPORT.md)

## What is proven about the native integration?

The real Bifrost gateway loaded the Go plugin and returned annotations in the scripted-provider smoke test. It preserved the original answer and produced explicit unavailable metadata on failure. The earlier real-provider native transport run failed semantic review. The decisive real-provider result came through the browser path, which uses Bifrost for verification model calls. [Native proof and boundary](INTEGRATION_PROOF.md#native-proof-and-its-boundary)

## Where should judges expect uncertainty?

Missing or contradictory evidence, publication timestamps without release proof, preview versus stable/LTS ambiguity, and claims outside the deterministic release rules can all lead to abstention. General claim interpretation still depends on model judgment and available evidence. Extraction can omit claims, search results can be incomplete, and public source text can contain misleading content. Historical facts are `not_checked` in this freshness workflow. An `unavailable` report indicates a dependency or processing failure. [Evidence and report semantics](FRONTEND_CONTRACT.md#field-semantics)
