import { Fragment, useState } from 'react'
import type { PointerEvent } from 'react'
import { Link } from 'react-router-dom'
import { ArrowDownLeft, ArrowRight, ArrowUpRight, Braces, CircuitBoard, Code2, Cpu, FileSearch, Globe, Network, ShieldCheck, Workflow } from 'lucide-react'
import type { ClaimVerdict } from '../../contract/types'
import { verdicts } from '../components/VerificationResults'

const nodes = {
  app: {
    title: 'AI Application', tag: 'Client', short: 'Opt in with a header', icon: Code2, accent: 'text-teal',
    detail: 'The client sends a chat completion request through Bifrost and opts in with x-freshnessguard: verify. The response includes the original answer and, when available, a separate verification report.',
  },
  gateway: {
    title: 'Bifrost Gateway', tag: 'Gateway', short: 'Routes the model request', icon: Network, accent: 'text-blue',
    detail: 'Bifrost routes the generation request. FreshnessGuard uses the HTTP transport hooks to check eligibility before generation and inspect the final successful completion afterward.',
  },
  plugin: {
    title: 'Native Go Verification Plugin', tag: 'HTTP hooks', short: 'Checks eligibility and attaches reports', icon: Braces, accent: 'text-lavender',
    detail: 'HTTPTransportPreHook checks opted-in request shape. HTTPTransportPostHook sends the final eligible completion to the authenticated Python /annotate route under a deadline, validates the returned report, and merges only the freshnessguard metadata.',
  },
  python: {
    title: 'Python Verification Service', tag: 'Verifier', short: 'Extracts, retrieves and validates', icon: CircuitBoard, accent: 'text-orchid',
    detail: 'The verifier extracts claims, researches time-sensitive ones within a search budget, and checks each proposed verdict against the evidence. Its structured report records claim results, citations, and any unavailable or incomplete checks.',
  },
  gemini: {
    title: 'Gemini via Bifrost', tag: 'Model calls', short: 'Extract claims and propose verdicts', icon: Cpu, accent: 'text-blue',
    detail: 'The model extracts claims from the answer and proposes judgments using the retrieved evidence. Gemini was used in the captured run. The verifier sends these internal calls through Bifrost with an internal header to bypass the verification hook.',
  },
  tavily: {
    title: 'Tavily search', tag: 'Evidence', short: 'Retrieve current snippets', icon: Globe, accent: 'text-teal',
    detail: 'Tavily supplies bounded search snippets for time-sensitive claims. The report records source URLs, retrieval dates, and publication dates when available. A search result needs supporting text before it can ground a verdict.',
  },
  official: {
    title: 'Official-source retrieval', tag: 'Conditional', short: 'Retrieve a release page when needed', icon: FileSearch, accent: 'text-lavender',
    detail: 'For a latest-version claim whose snippets lack sufficient proof, the verifier can retrieve one allowlisted official HTTPS page within its retrieval budget. Failed retrieval is recorded. The available snippets can still be assessed.',
  },
  validation: {
    title: 'Deterministic validation', tag: 'Inside verifier', short: 'Check quotes, dates and scope', icon: ShieldCheck, accent: 'text-orchid',
    detail: 'The verifier checks that cited quotes match the included source text and that corrections come from accepted quotes. Latest-version claims also face date, version and scope checks. Insufficient or rejected evidence leads to uncertainty.',
  },
}

type NodeId = keyof typeof nodes
const requestPath: NodeId[] = ['app', 'gateway', 'plugin', 'python']
const operations: NodeId[] = ['gemini', 'tavily', 'official', 'validation']
const edges: [NodeId, NodeId][] = [
  ['app', 'gateway'], ['gateway', 'plugin'], ['plugin', 'python'],
  ...operations.map((operation): [NodeId, NodeId] => ['python', operation]),
]

function FlowArrow({ active, vertical = false }: { active: boolean; vertical?: boolean }) {
  return (
    <svg viewBox="0 0 48 16" fill="none" aria-hidden="true" data-active={active}
      className={`pointer-events-none shrink-0 ${vertical ? 'h-7 w-8 rotate-90' : 'mx-auto h-8 w-8 rotate-90 lg:mx-0 lg:h-4 lg:w-9 lg:rotate-0'} ${active ? 'text-teal' : 'text-muted/50'}`}>
      <path d="M2 8h42" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 4"
        style={active ? { animation: 'dash-flow 1.5s linear infinite' } : undefined} />
      <path d="m38 3 6 5-6 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function trackPointer(event: PointerEvent<HTMLButtonElement>) {
  if (event.pointerType === 'touch') return
  const button = event.currentTarget
  const bounds = button.getBoundingClientRect()
  button.style.setProperty('--node-x', `${event.clientX - bounds.left}px`)
  button.style.setProperty('--node-y', `${event.clientY - bounds.top}px`)
}

function ArchitectureNode({ id, selected, connected, onSelect }: {
  id: NodeId
  selected: boolean
  connected: boolean
  onSelect: (id: NodeId) => void
}) {
  const { icon: Icon, title, short, tag, accent } = nodes[id]
  return (
    <button type="button" aria-label={title} aria-pressed={selected} data-connected={connected}
      onClick={() => onSelect(id)} onPointerMove={trackPointer}
      className={`glass group relative h-full w-full min-w-0 overflow-hidden rounded-2xl p-3.5 text-left transition-[border-color,box-shadow] duration-300 hover:border-teal/45 sm:p-4 ${selected ? '!border-teal/60 ring-1 ring-teal/30' : connected ? '!border-blue/40' : ''}`}>
      <span aria-hidden="true" className="pointer-events-none absolute inset-0 opacity-0 transition-opacity group-hover:opacity-100 motion-reduce:hidden"
        style={{ background: 'radial-gradient(125px circle at var(--node-x, 50%) var(--node-y, 50%), rgb(var(--teal) / .15), transparent 75%)' }} />
      <span className="relative mb-2.5 flex items-center gap-2">
        <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-fg/10 bg-bg/40 ${accent}`}><Icon size={17} aria-hidden="true" /></span>
        <span className={`font-mono text-[10px] uppercase tracking-wider ${accent}`}>{tag}</span>
      </span>
      <span className="relative block text-sm font-semibold leading-tight">{title}</span>
      <span className="relative mt-1 block text-xs leading-snug text-muted">{short}</span>
    </button>
  )
}

function NodeInfo({ id, connected }: { id: NodeId; connected: NodeId[] }) {
  const { title, detail, accent } = nodes[id]
  return (
    <div className="rounded-2xl border border-fg/10 bg-bg/45 p-4 motion-safe:animate-fade-up sm:p-5">
      <p className={`font-mono text-[10px] uppercase tracking-widest ${accent}`}>Selected component</p>
      <h3 className="mt-2 text-base font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted">{detail}</p>
      <p className="mt-3 text-xs leading-relaxed text-muted"><span className="font-medium text-fg">Connected to </span>{connected.map((node) => nodes[node].title).join(' · ')}</p>
    </div>
  )
}

const lifecycle = [
  ['Opt in', 'Send x-freshnessguard: verify with an eligible non-streaming HTTP chat completion request for one choice.'],
  ['Inspect the completion', 'The post-hook runs on a successful response. The service marks truncated or filtered answers incomplete and skips research for them.'],
  ['Extract and check', 'The model extracts claims. Search and conditional page retrieval supply evidence for time-sensitive claims, and deterministic checks validate the proposed judgments.'],
  ['Return the answer', 'Bifrost returns the original answer with separate report metadata. On verifier failure, fail-open behavior preserves the answer and marks verification unavailable.'],
]

const verdictNotes: Record<ClaimVerdict, string> = {
  supported: 'Available evidence backs the claim.',
  outdated: 'Accepted evidence shows the claim is stale.',
  uncertain: 'The evidence is insufficient for a decisive verdict.',
  not_checked: 'The claim was classified as timeless and skipped.',
}

export default function Integrations() {
  const [selected, setSelected] = useState<NodeId>('python')
  const connected = edges.flatMap(([from, to]) => from === selected ? [to] : to === selected ? [from] : [])
  const isOperation = operations.includes(selected)
  const node = (id: NodeId) => <ArchitectureNode id={id} selected={id === selected} connected={connected.includes(id)} onSelect={setSelected} />

  return (
    <div className="space-y-8 sm:space-y-10">
      <header className="max-w-4xl">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-teal/25 bg-teal/10 px-3 py-1.5 font-mono text-[11px] font-medium uppercase tracking-widest text-teal">
          <Workflow size={14} aria-hidden="true" /> Architecture tour
        </div>
        <h1 className="text-[clamp(2.2rem,5.8vw,4.25rem)] font-semibold leading-[1.08] tracking-[-0.055em]">
          Follow the answer. <span className="text-aurora">See what checks it.</span>
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">
          An opt-in Bifrost plugin hands the completed response to a verifier and attaches a claim report alongside the original answer.
        </p>
      </header>

      <section aria-labelledby="flow-title" className="glass rounded-3xl p-4 sm:p-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 id="flow-title" className="text-xl font-semibold tracking-tight">Verification flow</h2>
            <p className="mt-1 text-sm text-muted">Select a component to see what it does and where it connects.</p>
          </div>
          <span className="rounded-full border border-teal/20 bg-teal/10 px-2.5 py-1 text-xs font-medium text-teal">Implemented backend</span>
        </div>
        <div className="flex flex-col items-stretch lg:flex-row lg:items-center">
          {requestPath.map((id, index) => (
            <Fragment key={id}>
              {index > 0 && <FlowArrow active={selected === id || selected === requestPath[index - 1]} />}
              <div className="min-w-0 lg:flex-1 lg:self-stretch">
                {node(id)}
                {selected === id && <div className="mt-2 lg:hidden"><NodeInfo id={selected} connected={connected} /></div>}
              </div>
            </Fragment>
          ))}
        </div>

        <div className="mt-4 grid items-start gap-4 border-t border-fg/10 pt-4 lg:grid-cols-[minmax(0,1.65fr)_minmax(0,1fr)]">
          <div>
            <div className="mb-3 flex items-center gap-1.5">
              <FlowArrow active={selected === 'python' || isOperation} vertical />
              <h3 className="text-sm font-semibold">Python service operations</h3>
            </div>
            <div className="grid gap-2.5 min-[380px]:grid-cols-2">
              {operations.map((id) => (
                <Fragment key={id}>
                  {node(id)}
                  {selected === id && <div className="min-[380px]:col-span-2 lg:hidden"><NodeInfo id={selected} connected={connected} /></div>}
                </Fragment>
              ))}
            </div>
          </div>
          <div className="hidden lg:block"><NodeInfo key={selected} id={selected} connected={connected} /></div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-xl border border-blue/20 bg-blue/10 px-3 py-2.5 text-sm">
          <ArrowDownLeft size={16} className="shrink-0 text-blue" aria-hidden="true" />
          <span className="font-semibold">Back to the application</span>
          <span className="text-muted">Original completion + <code className="font-mono text-xs text-blue">freshnessguard</code> report metadata</span>
        </div>
      </section>

      <section aria-labelledby="lifecycle-title">
        <h2 id="lifecycle-title" className="mb-4 text-2xl font-semibold tracking-tight">From request to report</h2>
        <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {lifecycle.map(([title, description], index) => (
            <li key={title} className="glass rounded-2xl p-4 sm:p-5">
              <span className="font-mono text-xs text-teal">0{index + 1}</span>
              <h3 className="mt-2 text-sm font-semibold">{title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted">{description}</p>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="report-guide" className="glass rounded-3xl p-5 sm:p-6">
        <h2 id="report-guide" className="text-xl font-semibold tracking-tight">What the report tells you</h2>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted">
          Citation IDs tie exact quotes to included source text. Source URLs and recorded dates let readers trace the evidence.
          Uncertain describes a claim that could not be resolved. Unavailable describes a verification failure.
        </p>
        <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(Object.keys(verdictNotes) as ClaimVerdict[]).map((id) => {
            const { label, icon: Icon, tone } = verdicts[id]
            return <div key={id} className="rounded-xl border border-fg/10 bg-bg/30 p-3">
              <dt className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs font-semibold ${tone}`}><Icon size={13} aria-hidden="true" />{label}</dt>
              <dd className="mt-2 text-sm text-muted">{verdictNotes[id]}</dd>
            </div>
          })}
        </dl>
      </section>

      <section aria-labelledby="availability-title">
        <h2 id="availability-title" className="mb-4 text-2xl font-semibold tracking-tight">What you can try</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <article className="glass rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-teal">Implemented backend</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">The native plugin and verifier implement opt-in checks and response annotation.</p>
          </article>
          <article className="glass rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-lavender">Saved frontend demonstrations</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">Examples and Verify open saved reports with their original evidence and outcomes.</p>
            <Link to="/examples" className="mt-3 inline-flex items-center gap-1.5 rounded text-sm font-medium text-lavender">Explore saved demos <ArrowUpRight size={14} aria-hidden="true" /></Link>
          </article>
          <article className="glass rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-blue">Live browser integration</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">Verify can use the opt-in local development adapter when configured. Saved demos remain available offline.</p>
            <Link to="/verify" className="mt-3 inline-flex items-center gap-1.5 rounded text-sm font-medium text-blue">Open Verify <ArrowRight size={14} aria-hidden="true" /></Link>
          </article>
        </div>
      </section>
    </div>
  )
}
