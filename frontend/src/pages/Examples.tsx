import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Braces, CircleAlert, FlaskConical, History, LibraryBig, Quote, ShieldCheck } from 'lucide-react'
import type { ClaimVerdict, VerificationReport } from '../../contract/types'
import { verdicts } from '../components/VerificationResults'
import { loadSavedReport, savedDemos } from '../lib/savedReports'

const scenarios = [
  {
    id: 'mixed', title: 'Synthetic claim report', category: 'Walkthrough',
    description: 'See how one answer can contain a supported claim, an outdated claim, and a timeless statement.',
    icon: FlaskConical, accent: 'text-teal', surface: 'from-teal/10', width: 'lg:col-span-7',
  },
  {
    id: 'saved-live', title: 'Captured live abstention', category: 'Historical capture',
    description: 'See why a captured run returned Uncertain when the cited quote lacked the date needed to establish the claim.',
    icon: History, accent: 'text-blue', surface: 'from-blue/10', width: 'lg:col-span-5',
  },
  {
    id: 'replay', title: 'Offline corrected evidence window', category: 'Offline replay',
    description: 'See how a complete quote containing the release date changes the assessment of the same saved evidence.',
    icon: Quote, accent: 'text-lavender', surface: 'from-lavender/10', width: 'lg:col-span-5',
  },
  {
    id: 'unavailable', title: 'Simulated upstream failure', category: 'Error handling',
    description: 'An intentional service failure shows how FreshnessGuard reports that verification was unavailable and withholds a verdict.',
    icon: Braces, accent: 'text-orchid', surface: 'from-orchid/10', width: 'lg:col-span-7',
  },
] as const

const verdictGuide: Record<ClaimVerdict, string> = {
  supported: 'The available evidence backs the claim.',
  outdated: 'Accepted evidence shows the claim is stale.',
  uncertain: 'The available evidence does not settle the claim.',
  not_checked: 'The claim did not receive a time-sensitive check.',
}

export default function Examples() {
  const [reports, setReports] = useState<Record<string, VerificationReport | null>>({})
  useEffect(() => {
    let active = true
    for (const { id } of scenarios) {
      const demo = savedDemos.find((item) => item.id === id)
      if (!demo) {
        setReports((current) => ({ ...current, [id]: null }))
        continue
      }
      void loadSavedReport(demo).then((report) => {
        if (active) setReports((current) => ({ ...current, [id]: report }))
      }).catch(() => {
        if (active) setReports((current) => ({ ...current, [id]: null }))
      })
    }
    return () => { active = false }
  }, [])

  return (
    <div className="space-y-10 sm:space-y-14">
      <header className="max-w-4xl">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-teal/25 bg-teal/10 px-3 py-1.5 font-mono text-[11px] font-medium uppercase tracking-widest text-teal">
          <LibraryBig size={14} aria-hidden="true" /> Evidence gallery
        </div>
        <h1 className="text-[clamp(2.25rem,5.8vw,4.5rem)] font-semibold leading-[1.08] tracking-[-0.055em]">
          Don't just trust the answer. <span className="text-aurora">Check the evidence.</span>
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">
          Explore four saved verification demonstrations, from cited claims to an unavailable service. Opening a demo replays an existing report offline.
        </p>
      </header>

      <section aria-label="Saved verification demonstrations" className="grid gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-12">
        {scenarios.map(({ id, title, category, description, icon: Icon, accent, surface, width }) => {
          const report = reports[id]
          const claim = report?.claims[0]
          const quote = claim?.quotes[0]
          const preview = quote?.text ?? claim?.text ?? report?.original_answer
          const outcomes = Array.from(new Set(report?.claims.map((item) => item.verdict)))
          const unavailable = report?.status === 'unavailable' || report?.status === 'upstream_error'
          return (
            <Link key={id} to={`/verify?demo=${id}`} aria-labelledby={`example-${id} explore-${id}`}
              className={`glass group relative flex min-w-0 flex-col overflow-hidden rounded-3xl p-5 transition-[border-color,transform] duration-300 hover:border-teal/40 motion-safe:hover:-translate-y-1 sm:p-6 ${width}`}>
              <div aria-hidden="true" className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${surface} via-transparent to-transparent`} />
              <div className="relative mb-5 flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2.5">
                  <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-fg/10 bg-bg/40 ${accent}`}><Icon size={19} aria-hidden="true" /></span>
                  <span className={`text-xs font-semibold ${accent}`}>{category}</span>
                </div>
                <span className="shrink-0 rounded-full border border-fg/10 bg-bg/40 px-2.5 py-1 text-[11px] font-medium text-muted">Saved Demo</span>
              </div>
              <h2 id={`example-${id}`} className="relative text-2xl font-semibold leading-tight tracking-tight">{title}</h2>
              <p className="relative mt-2 max-w-xl text-sm leading-relaxed text-muted">{description}</p>
              <div className="relative mt-4 flex flex-wrap items-center gap-1.5">
                {outcomes.map((outcome) => {
                  const { label, icon: VerdictIcon, tone } = verdicts[outcome]
                  return <span key={outcome} className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs font-medium ${tone}`}><VerdictIcon size={13} aria-hidden="true" /> {label}</span>
                })}
                {unavailable && <span className="inline-flex items-center gap-1 rounded-full border border-warn/30 bg-warn/10 px-2 py-1 text-xs font-medium text-warn"><CircleAlert size={13} aria-hidden="true" /> Verification unavailable</span>}
                {report === null && <span className="text-xs text-warn">Preview unavailable</span>}
                {report === undefined && <span className="text-xs text-muted">Loading saved preview…</span>}
              </div>
              {preview && <div className="relative mt-4 rounded-xl border border-fg/10 bg-bg/40 px-3 py-2.5">
                <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">{quote ? 'Cited quote' : claim ? 'Claim preview' : 'Sample answer'}</p>
                <p className="line-clamp-3 whitespace-pre-wrap break-words text-xs leading-relaxed text-fg [overflow-wrap:anywhere]">{preview}</p>
              </div>}
              <span id={`explore-${id}`} className={`relative mt-auto inline-flex items-center gap-2 pt-5 text-sm font-semibold ${accent}`}>
                Explore verification <ArrowUpRight size={16} aria-hidden="true" className="transition-transform motion-safe:group-hover:-translate-y-0.5 motion-safe:group-hover:translate-x-0.5" />
              </span>
            </Link>
          )
        })}
      </section>

      <section aria-labelledby="verdict-guide" className="glass rounded-3xl p-5 sm:p-7">
        <h2 id="verdict-guide" className="flex items-center gap-2 text-lg font-semibold"><ShieldCheck size={19} className="text-teal" aria-hidden="true" /> Reading the verdicts</h2>
        <dl className="mt-4 grid gap-x-5 gap-y-4 sm:grid-cols-2 lg:grid-cols-4">
          {(Object.keys(verdictGuide) as ClaimVerdict[]).map((key) => {
            const { label, icon: Icon, tone } = verdicts[key]
            return <div key={key}>
              <dt className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${tone}`}><Icon size={13} aria-hidden="true" /> {label}</dt>
              <dd className="mt-2 text-sm leading-relaxed text-muted">{verdictGuide[key]}</dd>
            </div>
          })}
        </dl>
      </section>
    </div>
  )
}
