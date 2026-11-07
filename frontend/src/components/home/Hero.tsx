import { Link } from 'react-router-dom'
import { ArrowRight, Sparkles } from 'lucide-react'
import type { CSSProperties } from 'react'

const delay = (ms: number): CSSProperties => ({ animationDelay: `${ms}ms` })

export function Hero() {
  return (
    <section className="relative pt-6 text-center sm:pt-14">
      {/* Soft spotlight behind the headline */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[420px] w-[min(900px,100%)] -translate-x-1/2 rounded-full opacity-60 blur-3xl"
        style={{
          background:
            'radial-gradient(closest-side, rgb(var(--teal) / 0.18), rgb(var(--lavender) / 0.14) 60%, transparent)',
        }}
      />

      <div
        className="glass mx-auto inline-flex animate-fade-up items-center gap-2.5 rounded-full px-4 py-1.5"
        style={delay(0)}
      >
        <span
          aria-hidden="true"
          className="h-1.5 w-1.5 rounded-full bg-teal"
          style={{ animation: 'pulse-ring 2s ease-out infinite' }}
        />
        <span className="font-mono text-[11px] font-medium uppercase tracking-[0.22em] text-muted">
          The trust layer for AI
        </span>
      </div>

      <h1 className="mx-auto mt-8 max-w-5xl text-balance text-[2.75rem] font-semibold leading-[1.04] tracking-[-0.035em] sm:text-7xl lg:text-[5.5rem]">
        <span className="block animate-fade-up" style={delay(100)}>
          Your AI sounds confident.
        </span>
        <span className="block animate-fade-up" style={delay(220)}>
          <span className="text-aurora-animated">But is it current?</span>
        </span>
      </h1>

      <p
        className="mx-auto mt-7 max-w-2xl animate-fade-up text-pretty text-base leading-relaxed text-muted sm:text-xl"
        style={delay(340)}
      >
        Verify AI-generated claims against current evidence. Catch outdated information before it
        becomes misinformation.
      </p>

      <div
        className="mt-10 flex animate-fade-up flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center"
        style={delay(460)}
      >
        <Link to="/verify" className="btn-primary group">
          Verify an Answer
          <ArrowRight className="h-4 w-4 transition-transform duration-300 ease-spring group-hover:translate-x-1" />
        </Link>
        <Link to="/examples" className="btn-glass group">
          <Sparkles className="h-4 w-4 text-lavender transition-transform duration-500 ease-spring group-hover:rotate-12 group-hover:scale-110" />
          Try an Example
        </Link>
      </div>

      <p
        className="mt-8 animate-fade-up font-mono text-xs tracking-wide text-muted/80"
        style={delay(580)}
      >
        Claims <span className="mx-1.5 text-teal">→</span> Evidence{' '}
        <span className="mx-1.5 text-lavender">→</span> Verdict
      </p>
    </section>
  )
}
