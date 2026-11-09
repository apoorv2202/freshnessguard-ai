# Demo script and pitch

## Two-to-three-minute recording

**0:00–0:20 — Problem.** “An AI answer can be fluent and still describe last year's software. FreshnessGuard adds claim-level evidence at the gateway, so each application does not need to build its own checker.”

**0:20–0:45 — Integration.** Show the architecture diagram and native adapter. “This is a real Bifrost HTTP transport plugin. Developers opt in with `x-freshnessguard: verify`. The original answer and token usage stay intact; a separate report carries the evidence.”

**0:45–1:30 — Claims and sources.** Open **Examples → Offline corrected evidence window**. Identify it as a saved offline replay, then expand the claim and show the dated stable-release quote, official source link, and correction. A prior live run for the same Python 3.11 claim returned `outdated` with one official citation, 100% coverage, freshness 0/100, and 9.66 seconds of elapsed time. That measurement is from an earlier revision.

**Optional live segment.** If provider use is authorized, follow the [Windows startup checklist](../README.md#run-the-browser-demo-on-windows) and submit “The latest stable Python release series is 3.11.” once. Show the actual result. If it times out, abstains or is rate-limited, explain the returned state and switch to the saved replay. Keep terminal credentials and gateway configuration off screen.

**1:30–2:00 — Uncertainty.** Open **Captured uncertain result**, then **Simulated upstream failure**. Identify the first as a captured abstention and the second as an intentional simulation. Explain why both leave freshness unassessed.

**2:00–2:30 — Engineering.** Show Integrations and distinguish the browser paste flow from the native Bifrost hook. The browser flow has a decisive live result. Native hook mechanics and fail-open behavior were tested with gateway fixtures. A decisive browser result does not measure detector accuracy or establish a decisive final-revision native run.

**2:30–3:00 — Score interpretation.** Show the labeled **Synthetic example**. Explain that coverage counts decisive checks among extracted time-sensitive claims, and use **Copy Report** to show that a saved export includes its provenance.

## Concise pitch

FreshnessGuard AI brings evidence-backed freshness checks into the Bifrost LLM gateway. It extracts factual claims, researches time-sensitive statements with Tavily, and attaches cited evidence, source-backed correction excerpts and explicit uncertainty while preserving the original model answer.

The contribution is an opt-in gateway capability backed by an independently usable stale-answer API. Bounded search, recursion prevention and explicit failure states make the integration practical for application developers. Its purpose is to make unsupported freshness claims visible, not to provide an infallible fact-checker. Current live limitations and failed experiments are published alongside tests and measured results.
