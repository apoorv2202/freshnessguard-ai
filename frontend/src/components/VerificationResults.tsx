import { useState } from 'react'
import { BookOpen, ChevronDown, CircleAlert, CircleCheck, CircleHelp, ExternalLink, MinusCircle } from 'lucide-react'
import type { Claim, Source, VerificationReport } from '../../contract/types'
import { citationUrl } from '../lib/savedReports'

export const verdicts = {
  supported: { label: 'Supported', icon: CircleCheck, tone: 'border-teal/30 bg-teal/10 text-teal' },
  outdated: { label: 'Outdated', icon: CircleAlert, tone: 'border-orchid/30 bg-orchid/10 text-orchid' },
  uncertain: { label: 'Uncertain', icon: CircleHelp, tone: 'border-warn/30 bg-warn/10 text-warn' },
  not_checked: { label: 'Not checked', icon: MinusCircle, tone: 'border-fg/15 bg-fg/5 text-muted' },
}
const timeLabel = (value: string) => /^\d{4}-\d{2}-\d{2}$/.test(value) ? value
  : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
const dateKind = { release_date: 'Release date', as_of: 'As of', effective_date: 'Effective date' }

function Evidence({ claim }: { claim: Claim }) {
  const cited = new Set(claim.citation_ids)
  const acceptedSources = claim.sources.filter((source) => cited.has(source.id))
  const contextSources = claim.sources.filter((source) => !cited.has(source.id))
  const witnesses = claim.semantic_validation?.release_witnesses ?? []
  const observed = claim.semantic_validation?.observed_release_witnesses ?? []
  function sourceCard(source: Source) {
    const url = citationUrl(source.url)
    const accepted = cited.has(source.id)
    const quotes = claim.quotes.filter((quote) => quote.source_id === source.id)
    const dates = (accepted ? witnesses : observed).filter((item) => item.source_id === source.id)
    return (
      <article key={source.id} className={`min-w-0 rounded-2xl border p-4 sm:p-5 ${accepted ? 'border-teal/45 bg-teal/10' : 'border-fg/10 bg-bg/35'}`}>
        <div className="mb-2 flex flex-wrap items-center gap-2 font-mono text-[10px] uppercase tracking-wider">
          <span className="rounded-md bg-fg/10 px-1.5 py-0.5 text-fg">{source.id}</span>
          <span className={accepted ? 'text-teal' : 'text-muted'}>{accepted ? 'Cited evidence' : 'Retained context'}</span>
          {source.primary_source && <span className="text-muted">· Primary source</span>}
        </div>
        {url ? <a className="inline-flex max-w-full items-start gap-1.5 break-words text-sm font-semibold text-fg underline decoration-fg/30 underline-offset-4 hover:text-teal"
          href={url} target="_blank" rel="noopener noreferrer"><span className="min-w-0 [overflow-wrap:anywhere]">{source.title || url}</span><ExternalLink size={13} className="mt-0.5 shrink-0" aria-hidden="true" /></a>
          : <p className="break-words text-sm font-semibold">{source.title || 'Source'} <span className="font-normal text-muted">· Link unavailable</span></p>}
        <dl className="mt-2 space-y-1 text-xs text-muted">
          {source.published_date && <div><dt className="inline">Published: </dt><dd className="inline">{timeLabel(source.published_date)}</dd></div>}
          <div><dt className="inline">Retrieved: </dt><dd className="inline">{timeLabel(source.retrieved_at)}</dd></div>
          {dates.map((item, index) => <div key={index}><dt className="inline">{accepted ? '' : 'Observed, not accepted · '}{dateKind[item.date_kind]}: </dt><dd className="inline">{item.date} · {item.version}</dd></div>)}
        </dl>
        {quotes.map((quote, index) => <blockquote key={index} className="mt-3 whitespace-pre-wrap break-words rounded-r-lg border-l-2 border-teal/65 bg-bg/45 py-2.5 pl-3 pr-2 text-sm leading-relaxed text-fg [overflow-wrap:anywhere]">{quote.text}</blockquote>)}
        <details className="mt-3 text-xs text-muted">
          <summary className="cursor-pointer py-1 font-medium hover:text-fg">Included source text</summary>
          <p className="mt-2 max-h-72 overflow-y-auto whitespace-pre-wrap break-words leading-relaxed [overflow-wrap:anywhere]">{source.content}</p>
        </details>
      </article>
    )
  }

  return (
    <>
      {!cited.size && <p className="mb-4 rounded-xl border border-fg/10 bg-bg/40 p-3 text-sm text-muted">No accepted citations for this claim. Retained sources are provided for context.</p>}
      {!claim.sources.length && <p className="text-sm text-muted">No source material was recorded for this claim.</p>}
      <div className="space-y-3">{acceptedSources.map(sourceCard)}</div>
      {contextSources.length > 0 && (
        <details className="mt-4 rounded-xl border border-fg/10 bg-bg/25 px-3 py-2">
          <summary className="cursor-pointer rounded-md py-1.5 text-sm font-medium text-muted hover:text-fg">Retained context ({contextSources.length})</summary>
          <div className="space-y-3 pb-1 pt-2">{contextSources.map(sourceCard)}</div>
        </details>
      )}
    </>
  )
}

export function VerificationResults({ report }: { report: VerificationReport }) {
  const [selected, setSelected] = useState(0)
  const [expanded, setExpanded] = useState(true)
  const claim = report.claims[selected]
  const unavailable = report.status === 'unavailable' || report.status === 'upstream_error'
  const count = report.claims.length

  return (
    <>
      <div className="glass grid grid-cols-2 gap-2 rounded-3xl p-2 sm:grid-cols-4 sm:gap-3 sm:p-3">
        <div className="rounded-2xl bg-teal/10 p-3 sm:p-4"><p className="text-xs font-medium uppercase tracking-wider text-teal">Freshness</p>
          <p className="mt-1 text-2xl font-semibold tracking-tight">{report.freshness_score == null ? <span className="text-base text-muted">Not assessed</span> : `${report.freshness_score}%`}</p></div>
        <div className="rounded-2xl bg-lavender/10 p-3 sm:p-4"><p className="text-xs font-medium uppercase tracking-wider text-lavender">Coverage</p>
          <p className="mt-1 text-2xl font-semibold tracking-tight">{report.coverage == null ? <span className="text-base text-muted">Not assessed</span> : `${Math.round(report.coverage * 100)}%`}</p></div>
        <div className="rounded-2xl bg-bg/35 p-3 sm:p-4"><p className="text-xs font-medium uppercase tracking-wider text-muted">Claims</p><p className="mt-1 text-2xl font-semibold tracking-tight">{count}</p></div>
        <div className="rounded-2xl bg-bg/35 p-3 sm:p-4"><p className="text-xs font-medium uppercase tracking-wider text-muted">Report checked</p><p className="mt-2 text-sm font-medium">{timeLabel(report.checked_at)}</p></div>
      </div>
      {unavailable && <div role="status" className="glass rounded-2xl p-5">
        <h3 className="flex items-center gap-2 font-semibold text-warn"><CircleAlert size={18} aria-hidden="true" /> Verification unavailable</h3>
        <p className="mt-2 text-sm text-muted">{report.errors.some((error) => error.code === 'timeout')
          ? 'An upstream verification step timed out.'
          : report.status === 'upstream_error' ? 'An upstream service returned an error during verification.'
            : 'The verifier could not complete the check.'} Review any claim results and diagnostics below.</p>
        {report.errors.map((error, index) => <p key={index} className="mt-2 break-words font-mono text-xs text-muted">{error.stage} · {error.code}{error.http_status == null ? '' : ` · HTTP ${error.http_status}`}</p>)}
      </div>}
      {report.warnings.length > 0 && <ul className="space-y-1 rounded-2xl border border-warn/20 bg-warn/5 p-4 text-sm text-muted">
        {report.warnings.map((warning, index) => <li key={index}>{warning}</li>)}
      </ul>}
      {report.status === 'no_claims_extracted' && <p className="glass rounded-2xl p-5 text-sm text-muted">The verifier did not extract any claims from this answer.</p>}
      {report.status === 'no_time_sensitive_claims' && <p className="glass rounded-2xl p-5 text-sm text-muted">The extracted claims did not require a time-sensitive check.</p>}
      {report.status === 'review_required' && <p className="glass rounded-2xl p-5 text-sm text-muted">Review the outdated or unresolved claims below.</p>}
      {claim && <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
        <div className="min-w-0 space-y-3">
          <h3 className="mb-4 text-lg font-semibold">Claims</h3>
          {report.claims.map((item, index) => {
            const active = index === selected
            const open = active && expanded
            const { label, icon: Icon, tone } = verdicts[item.verdict]
            return (
              <article key={index} className={`glass min-w-0 rounded-2xl transition-colors ${active ? 'border-teal/50 ring-1 ring-teal/20' : ''}`}>
                <button type="button" aria-expanded={open} aria-controls={`claim-detail-${index}`}
                  onClick={() => { setExpanded(!open); setSelected(index) }}
                  className="group flex w-full items-start gap-3 rounded-2xl px-4 py-4 text-left hover:bg-fg/5 sm:px-5">
                  <div className="min-w-0 flex-1">
                    <span className="mb-2 flex flex-wrap items-center gap-2">
                      <span className="font-mono text-[11px] text-muted">Claim {String(index + 1).padStart(2, '0')}</span>
                      <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${tone}`}><Icon size={14} aria-hidden="true" /> {label}</span>
                    </span>
                    <span className="block break-words text-sm font-medium leading-relaxed [overflow-wrap:anywhere] sm:text-base">{item.text}</span>
                  </div>
                  <ChevronDown size={17} aria-hidden="true" className={`mt-1 shrink-0 text-muted transition-transform ${open ? 'rotate-180' : ''}`} />
                </button>
                <div id={`claim-detail-${index}`} hidden={!open} className="space-y-3 border-t border-fg/10 px-4 py-4 text-sm sm:px-5">
                  <p className="break-words leading-relaxed text-muted">{item.reason}</p>
                  {item.correction !== null && <div className="rounded-xl border border-teal/20 bg-teal/10 p-3">
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-teal">Evidence-backed correction</p>
                    <p className="whitespace-pre-wrap break-words [overflow-wrap:anywhere]">{item.correction}</p>
                  </div>}
                  <a href="#claim-evidence" className="inline-block text-xs font-medium text-teal underline underline-offset-4 lg:hidden">See related evidence</a>
                </div>
              </article>
            )
          })}
        </div>
        <aside id="claim-evidence" aria-labelledby="evidence-title" className="glass min-w-0 rounded-3xl p-4 sm:p-6">
          <h3 id="evidence-title" className="flex items-center gap-2 text-lg font-semibold"><BookOpen size={18} className="text-teal" aria-hidden="true" /> Related evidence</h3>
          <p className="mb-4 mt-1 text-sm text-muted" aria-live="polite">Claim {selected + 1} of {count} · {claim.citation_ids.length} cited sources</p>
          <Evidence key={selected} claim={claim} />
        </aside>
      </div>}
    </>
  )
}
