# Submission preparation — personal target 10 November 2026

## Project pitch

FreshnessGuard AI adds an opt-in evidence report to Bifrost chat completions. It extracts factual claims, spends Tavily calls on time-sensitive statements and returns citations, proposed corrections and explicit uncertainty without rewriting the model's answer. Developers enable the feature with one request header. The same verification service checks pasted or saved answers independently.

Target mapping: Bifrost 04 — missing gateway capability, implemented as a native transport plugin. Tavily 01 — stale-answer detection with live search and claim-level freshness scoring. This mapping follows the user's supplied problem descriptions. Exact official problem attachments, judging criteria, portal and cutoff time still require confirmation; the referenced chat contained no downloadable problem attachments. November 10 is the user's own stated submission target.

## Two-minute demonstration

Use the [browser demo script](DEMO_SCRIPT.md) and [Windows startup checklist](../README.md#run-the-browser-demo-on-windows). Show the single live Python claim and its actual result, or switch to the labeled offline replay if the providers are unavailable. Use Integrations and the gateway fixture results to explain the separate native hook. Keep keys and gateway credential screens out of the recording.

## Required completion checks

- [x] Local repository and focused implementation.
- [x] Real Bifrost native plugin adapter using inspected extension interfaces.
- [x] Standalone verification API and offline report demo.
- [x] Bounded claim extraction, Tavily client, grounding validation and uncertainty.
- [x] Python and native Go tests and reproducible benchmark commands.
- [x] Full dynamically linked Bifrost HTTP gateway smoke test with a local scripted provider, including extraction/judging through Bifrost, report serialization, recursion prevention and explicit fail-open behavior.
- [x] Live Tavily/Gemini connectivity and bounded measured smoke runs, including published unsuccessful outcomes.
- [x] Decisive live browser verification through Vite with an accepted official citation and exact quote.
- [x] Native live transport roundtrip through real Gemini and Tavily, reviewed and recorded as a semantic failure.
- [x] Grounded-subject and truncated-answer regression fix; 10 real gateway fixture checks and 6 native tests with race checking.
- [ ] Repeat the native live run on the final revision with a complete controlled answer and relevant, human-reviewed evidence after Gemini quota recovers.
- [ ] Complete the interrupted multi-category live set; demonstrate outdated, supported and uncertain outcomes on the final revision.
- [ ] Independent labelled quality benchmark with dated sources and measured enabled latency/cost.
- [ ] Confirm exact official track requirements and submission deadline/time.
- [ ] Push the repository, verify a clean-clone build, record a short demo and submit the links.

The local browser demo is ready with a saved fallback. The measured decisive run covered one claim. Earlier runs showed provider latency and evidence-related abstention. A decisive final-revision native run and a broader labeled evaluation remain open. Publishing and submission require the user's approval.

Suggested solo schedule: Nov 5 establish the native loader/service path; Nov 6 live provider integration and error handling; Nov 7 independent benchmark and evidence review; Nov 8 demo stability and clean-clone rehearsal; Nov 9 record and prepare submission; Nov 10 submit before the confirmed cutoff. Avoid adding multi-user dashboards, billing or streaming before the core live path is proven.
