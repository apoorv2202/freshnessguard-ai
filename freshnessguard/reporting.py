"""Portable report rendering; model content is escaped and links are constrained."""
import html
from urllib.parse import urlsplit


def esc(value):
    return html.escape(str(value), quote=True)


STYLE = '''
:root{color-scheme:dark;--bg:#0b1422;--card:#132237;--line:#29405b;--muted:#b3c3d6;--ink:#f0f5fc}
*{box-sizing:border-box}body{font:16px/1.65 system-ui;background:var(--bg);color:var(--ink);margin:0}
main{max-width:1040px;margin:auto;padding:48px 24px}header{border-bottom:1px solid var(--line);padding-bottom:28px}
.label{font-size:12px;letter-spacing:2px;color:#8ddacb;font-weight:700}h1{font-size:clamp(34px,6vw,58px);line-height:1.12;letter-spacing:-2px;margin:18px 0}h2{font-size:22px;line-height:1.4}
.notice{padding:18px;border:1px solid #827248;background:#28271e;border-radius:12px;color:#f3dfaa;margin:24px 0}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:28px 0}.metric{background:var(--card);padding:20px;border:1px solid var(--line);border-radius:12px}.metric strong{display:block;font-size:29px}
small,.muted{color:var(--muted)}article{border:1px solid var(--line);background:var(--card);padding:26px;margin:18px 0;border-radius:14px}
.badge{font-size:11px;letter-spacing:1.5px;padding:6px 9px;border-radius:6px;background:#293b51}.outdated{background:#4e2c2b;color:#ffc1ae}.supported{background:#173f39;color:#9ce5cb}.uncertain{background:#453c24;color:#f5dc9b}
.original{white-space:pre-wrap;background:#101d2e;padding:22px;border-left:3px solid #668eae;border-radius:4px}.evidence{border-top:1px solid var(--line);margin-top:20px;padding-top:18px}
a{color:#9fc8ff;overflow-wrap:anywhere}blockquote{margin:12px 0;padding:10px 18px;border-left:2px solid #78baac;color:#d2e4ef}footer{padding:28px 0;color:var(--muted);font-size:13px}
@media(max-width:650px){.metrics{grid-template-columns:1fr 1fr}main{padding:24px 16px}article{padding:20px}}
@media print{:root{color-scheme:light;--bg:white;--card:#f5f7fa;--ink:#162235;--muted:#48596b;--line:#ccd5df}article{break-inside:avoid}.original{background:#f4f6f8}}
'''


def render_report(report):
    live = report.get("mode") == "live"
    mode = "LIVE API RUN" if live else "SYNTHETIC FIXTURE"
    notice = ("Measured API run. Evidence and abstentions are recorded; this does not establish overall detector accuracy."
              if live else "Synthetic demonstration. Model decisions and search evidence are scripted; these are not live measurements.")
    cards = []
    for claim in report["claims"]:
        verdict = claim["verdict"] if claim["verdict"] in ("outdated", "supported", "uncertain", "not_checked") else "uncertain"
        sources = {s["id"]:s for s in claim["sources"]}
        evidence = []
        for quote in claim.get("quotes", []):
            source = sources.get(quote["source_id"])
            if not source:
                continue
            url = source["url"]
            try:
                safe = urlsplit(url).scheme == "https" and not urlsplit(url).username
            except ValueError:
                safe = False
            title = f'<a href="{esc(url)}" rel="noopener noreferrer">{esc(source["title"] or url)}</a>' if safe else esc(source["title"])
            badge = "OFFICIAL DOMAIN" if source.get("primary_source") else "UNASSESSED AUTHORITY"
            evidence.append(f'<div class="evidence"><small>{badge} / {esc(source["id"])}</small><p>{title}</p><blockquote>{esc(quote["text"][:350])}{"..." if len(quote["text"]) > 350 else ""}</blockquote><small>Publication metadata: {esc(source.get("published_date") or "not supplied")}<br>Retrieved: {esc(source.get("retrieved_at", "unknown"))}</small></div>')
        correction = f'<p class="label">SOURCE-BACKED CORRECTION EXCERPT</p><p>{esc(claim["correction"])}</p>' if claim.get("correction") else ""
        cards.append(f'<article><span class="badge {verdict}">{verdict.replace("_", " ").upper()}</span><h2>{esc(claim["text"])}</h2><p>{esc(claim["reason"])}</p>{correction}{"".join(evidence)}</article>')
    warnings = "".join(f'<li>{esc(w)}</li>' for w in report.get("warnings", []))
    for item in report.get("input_citations", []):
        if item["assessment"] == "not_official_for_detected_entity":
            warnings += f'<li>Input citation is not official for the detected entity; its content has not been authenticated: {esc(item["url"])}</li>'
    notes = f'<aside class="notice"><strong>Review notes</strong><ul>{warnings}</ul></aside>' if warnings else ""
    if report.get("run_note"):
        notes += f'<aside class="notice">{esc(report["run_note"])}</aside>'
    score, metrics = report.get("freshness_score"), report["metrics"]
    values = [("Freshness score", str(score) + "/100" if score is not None else "Unscored"),
              ("Extracted-claim coverage", str(round(100 * report.get("coverage", 0))) + "%"),
              ("Tavily calls", metrics.get("search_calls", 0)),
              ("Live processing" if live else "Fixture processing", str(round(metrics.get("latency_ms", 0) / 1000, 2)) + "s")]
    tiles = "".join(f'<div class="metric"><small>{esc(label)}</small><strong>{esc(value)}</strong></div>' for label,value in values)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FreshnessGuard AI | Evidence report</title><style>' + STYLE + '</style></head><body><main>'
        f'<header><div class="label">FRESHNESSGUARD AI / BIFROST + TAVILY</div><h1>Answers change.<br>Evidence matters.</h1><p>Advisory verification / Original response preserved</p><small>{mode} / {esc(report.get("checked_at"))} / {esc(report.get("model") or "scripted model")}</small></header>'
        f'<aside class="notice"><strong>{mode}</strong><br>{notice}</aside><div class="metrics">{tiles}</div>'
        '<p class="muted">The score counts supported versus outdated decisive claims. Uncertain claims are excluded: read coverage alongside the score. Official domains and quote provenance do not prove semantic correctness.</p>'
        f'{notes}<p class="label">ORIGINAL ANSWER / UNCHANGED</p><div class="original">{esc(report["original_answer"])}</div><p class="label" style="margin-top:34px">CLAIM-LEVEL EVIDENCE</p>'
        + ("".join(cards) or '<p class="muted">No claims extracted. Read warnings; this is not an all-clear.</p>')
        + f'<footer>Status: {esc(report["status"])} / Model calls: {metrics.get("llm_calls", 0)} / Reported Tavily credits: {metrics.get("tavily_credits", 0)} / Credit usage complete: {esc(metrics.get("credit_usage_complete"))}<br>{esc(report.get("scope", ""))}<br>Advisory research output. No silent rewriting, no calibrated confidence probability, no guarantee of completeness.</footer></main></body></html>')
