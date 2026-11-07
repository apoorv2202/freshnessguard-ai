import { ScanText, Search, ShieldCheck } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Reveal } from '../Reveal'

interface Step {
  n: string
  title: string
  body: string
  icon: LucideIcon
  accent: string
}

const STEPS: Step[] = [
  {
    n: '01',
    title: 'Extract Claims',
    body: 'Break an AI answer into discrete, checkable claims so every statement can be judged on its own.',
    icon: ScanText,
    accent: 'text-teal bg-teal/10 border-teal/25',
  },
  {
    n: '02',
    title: 'Search Current Evidence',
    body: 'Look up up-to-date sources for each claim instead of trusting what a model remembers.',
    icon: Search,
    accent: 'text-blue bg-blue/10 border-blue/25',
  },
  {
    n: '03',
    title: 'Verify & Explain',
    body: 'Return a clear verdict with a short, sourced explanation of what changed and why.',
    icon: ShieldCheck,
    accent: 'text-lavender bg-lavender/10 border-lavender/25',
  },
]

export function HowItWorks() {
  return (
    <section className="mt-28 sm:mt-40" aria-labelledby="how-it-works">
      <Reveal className="mx-auto max-w-2xl text-center">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted">How it works</p>
        <h2
          id="how-it-works"
          className="mt-4 text-balance text-3xl font-semibold tracking-tight sm:text-5xl"
        >
          From confident claim to <span className="text-aurora">checked answer</span>
        </h2>
      </Reveal>

      <div className="mt-14 grid gap-5 md:grid-cols-3">
        {STEPS.map(({ n, title, body, icon: Icon, accent }, i) => (
          <Reveal key={n} delay={i * 120}>
            <article className="glass group relative h-full overflow-hidden rounded-3xl p-7 transition-all duration-500 ease-spring hover:-translate-y-1.5 hover:border-teal/30">
              <div
                aria-hidden="true"
                className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-gradient-to-br from-teal/30 to-lavender/30 opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-100"
              />
              <div className="relative flex items-center justify-between">
                <span
                  className={`grid h-12 w-12 place-items-center rounded-2xl border transition-transform duration-500 ease-spring group-hover:scale-110 group-hover:-rotate-6 ${accent}`}
                >
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <span className="font-mono text-sm text-muted/70">{n}</span>
              </div>
              <h3 className="relative mt-8 text-xl font-semibold tracking-tight">{title}</h3>
              <p className="relative mt-2.5 leading-relaxed text-muted">{body}</p>
            </article>
          </Reveal>
        ))}
      </div>
    </section>
  )
}
