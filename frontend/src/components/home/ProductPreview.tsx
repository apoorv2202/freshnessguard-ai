import { AlertTriangle, Check, Clock3, FlaskConical, Link2, Quote, ShieldCheck } from 'lucide-react'
import { Reveal } from '../Reveal'

const STEPS = ['Extracted', 'Searched', 'Verified']
const FRESHNESS_SEGMENTS = 5
const FRESHNESS_FILLED = 4

export function ProductPreview() {
  return (
    <Reveal as="section" className="relative mt-20 sm:mt-28" delay={80}>
      <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 -inset-y-10 -z-10 sm:-inset-x-6">
        <div
          className="mx-auto h-full max-w-4xl rounded-[3rem] opacity-40 blur-3xl"
          style={{
            background:
              'linear-gradient(120deg, rgb(var(--teal) / 0.5), rgb(var(--lavender) / 0.45) 60%, rgb(var(--orchid) / 0.4))',
          }}
        />
      </div>

      {/* Gradient hairline frame */}
      <div
        className="rounded-[2rem] p-px"
        style={{
          background:
            'linear-gradient(140deg, rgb(var(--teal) / 0.6), rgb(var(--fg) / 0.08) 35%, rgb(var(--fg) / 0.08) 65%, rgb(var(--orchid) / 0.55))',
        }}
      >
        <div className="glass rounded-[calc(2rem-1px)] !border-transparent p-3 sm:p-4">
          {/* Window chrome */}
          <div className="flex items-center justify-between gap-3 px-2 pb-3 pt-1 sm:px-3">
            <div className="flex items-center gap-4">
              <div className="flex gap-1.5" aria-hidden="true">
                <span className="h-2.5 w-2.5 rounded-full bg-fg/15" />
                <span className="h-2.5 w-2.5 rounded-full bg-fg/15" />
                <span className="h-2.5 w-2.5 rounded-full bg-fg/15" />
              </div>
              <span className="hidden font-mono text-xs text-muted sm:inline">verification / result</span>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-lavender/35 bg-lavender/10 px-3 py-1 font-mono text-[11px] font-medium uppercase tracking-wider text-lavender">
              <FlaskConical className="h-3 w-3" aria-hidden="true" />
              Illustrative Preview
            </span>
          </div>

          <div className="rounded-3xl border border-fg/[0.07] bg-bg/50 p-4 sm:p-6">
            {/* Pipeline progress */}
            <ol className="flex flex-wrap items-center gap-2" aria-label="Verification steps">
              {STEPS.map((step, i) => (
                <li key={step} className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-fg/10 bg-fg/[0.04] px-3 py-1 text-xs font-medium text-muted">
                    <Check className="h-3 w-3 text-teal" aria-hidden="true" />
                    {step}
                  </span>
                  {i < STEPS.length - 1 && <span aria-hidden="true" className="h-px w-4 bg-fg/15 sm:w-8" />}
                </li>
              ))}
            </ol>

            <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
              {/* Left column: claim + correction */}
              <div className="flex flex-col gap-4">
                <div className="rounded-2xl border border-fg/[0.08] bg-card/70 p-5 sm:p-6">
                  <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
                    <Quote className="h-3.5 w-3.5 text-blue" aria-hidden="true" />
                    AI-generated claim
                  </div>
                  <p className="mt-3 text-xl font-medium leading-snug tracking-tight sm:text-2xl">
                    “The latest stable version of [Product X] is 2.0.”
                  </p>
                  <p className="mt-3 text-sm text-muted">Stated with confidence, no date or source given.</p>
                </div>

                <div className="relative overflow-hidden rounded-2xl border border-teal/25 bg-teal/[0.06] p-5 sm:p-6">
                  <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.18em] text-teal">
                    <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                    Correction (example)
                  </div>
                  <p className="mt-3 leading-relaxed text-fg/90">
                    Current release notes list a newer version than 2.0. The claim may have been accurate
                    once, but it no longer reflects the latest release.
                  </p>
                </div>
              </div>

              {/* Right column: verdict + source */}
              <div className="flex flex-col gap-4">
                <div className="rounded-2xl border border-fg/[0.08] bg-card/70 p-5 sm:p-6">
                  <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">Verdict</div>
                  <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-warn/40 bg-warn/10 px-3.5 py-1.5 text-sm font-semibold tracking-wide text-warn">
                    <AlertTriangle className="h-4 w-4" aria-hidden="true" />
                    OUTDATED
                  </div>

                  <div className="mt-6">
                    <div className="flex items-center justify-between text-xs text-muted">
                      <span className="inline-flex items-center gap-1.5">
                        <Clock3 className="h-3.5 w-3.5" aria-hidden="true" />
                        Evidence freshness
                      </span>
                      <span className="font-mono text-fg/80">Recent</span>
                    </div>
                    <div
                      className="mt-2.5 flex gap-1.5"
                      role="img"
                      aria-label={`Freshness indicator: ${FRESHNESS_FILLED} of ${FRESHNESS_SEGMENTS}`}
                    >
                      {Array.from({ length: FRESHNESS_SEGMENTS }).map((_, i) => (
                        <span
                          key={i}
                          className={`h-1.5 flex-1 rounded-full ${
                            i < FRESHNESS_FILLED ? 'bg-gradient-to-r from-teal to-blue' : 'bg-fg/10'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-fg/[0.08] bg-card/70 p-5">
                  <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">Source</div>
                  <div className="mt-3 flex items-start gap-3">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-fg/10 bg-fg/[0.04]">
                      <Link2 className="h-4 w-4 text-blue" aria-hidden="true" />
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">Release notes — [Product X]</p>
                      <p className="truncate font-mono text-xs text-muted">example.com/release-notes</p>
                      <p className="mt-1 text-[11px] text-muted/80">Placeholder citation, not a real source.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Reveal>
  )
}
