import { Link } from 'react-router-dom'
import { ArrowRight, Globe, Waypoints } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { LogoMark } from '../Logo'
import { Reveal } from '../Reveal'

function Node({
  icon: Icon,
  name,
  role,
  accent,
}: {
  icon: LucideIcon
  name: string
  role: string
  accent: string
}) {
  return (
    <div className="glass group flex w-full items-center gap-4 rounded-2xl p-4 transition-all duration-500 ease-spring hover:-translate-y-1 hover:border-teal/30 md:flex-col md:gap-3 md:px-6 md:py-7 md:text-center">
      <span
        className={`grid h-12 w-12 shrink-0 place-items-center rounded-2xl border transition-transform duration-500 ease-spring group-hover:scale-110 ${accent}`}
      >
        <Icon className="h-5 w-5" aria-hidden="true" />
      </span>
      <div>
        <p className="font-semibold tracking-tight">{name}</p>
        <p className="text-sm text-muted">{role}</p>
      </div>
    </div>
  )
}

function Connector() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 80 24"
      className="hidden h-6 w-20 shrink-0 text-teal/70 md:block"
      fill="none"
    >
      <path
        d="M2 12h76"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeDasharray="6 6"
        style={{ animation: 'dash-flow 1.4s linear infinite' }}
      />
    </svg>
  )
}

export function IntegrationsTeaser() {
  return (
    <Reveal as="section" className="mt-28 sm:mt-40">
      <div
        className="rounded-[2rem] p-px"
        style={{
          background:
            'linear-gradient(160deg, rgb(var(--blue) / 0.45), rgb(var(--fg) / 0.07) 40%, rgb(var(--fg) / 0.07) 60%, rgb(var(--orchid) / 0.4))',
        }}
      >
        <div className="glass relative overflow-hidden rounded-[calc(2rem-1px)] !border-transparent px-6 py-14 text-center sm:px-12 sm:py-20">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute left-1/2 top-0 h-64 w-[70%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-r from-teal/30 via-lavender/30 to-orchid/30 blur-3xl"
          />

          <p className="relative font-mono text-xs uppercase tracking-[0.22em] text-muted">Integrations</p>
          <h2 className="relative mx-auto mt-4 max-w-2xl text-balance text-3xl font-semibold tracking-tight sm:text-5xl">
            Connects to the tools <span className="text-aurora">you already use</span>
          </h2>
          <p className="relative mx-auto mt-5 max-w-xl text-pretty leading-relaxed text-muted sm:text-lg">
            Route model calls through Bifrost and ground every verdict in current search results from
            Tavily.
          </p>

          <div className="relative mx-auto mt-12 flex max-w-3xl flex-col items-stretch gap-3 md:flex-row md:items-center md:gap-0">
            <Node
              icon={Waypoints}
              name="Bifrost"
              role="Model gateway"
              accent="border-blue/25 bg-blue/10 text-blue"
            />
            <Connector />
            <div className="glass flex w-full items-center gap-4 rounded-2xl border-teal/30 p-4 md:flex-col md:gap-3 md:px-6 md:py-7 md:text-center">
              <LogoMark className="h-12 w-12 shrink-0" />
              <div>
                <p className="font-semibold tracking-tight">FreshnessGuard AI</p>
                <p className="text-sm text-muted">Verification layer</p>
              </div>
            </div>
            <Connector />
            <Node
              icon={Globe}
              name="Tavily"
              role="Current evidence search"
              accent="border-teal/25 bg-teal/10 text-teal"
            />
          </div>

          <div className="relative mt-12">
            <Link to="/integrations" className="btn-glass group">
              Explore Integrations
              <ArrowRight className="h-4 w-4 transition-transform duration-300 ease-spring group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </div>
    </Reveal>
  )
}
