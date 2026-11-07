import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useOutletContext, useSearchParams } from 'react-router-dom'
import { ArrowDownRight, CircleAlert, ClipboardCopy, FileText, FlaskConical, Radar, RotateCcw, ScanLine, ShieldCheck, Trash2 } from 'lucide-react'
import type { FixtureDescriptor, VerificationReport } from '../../contract/types'
import type { LayoutContext } from '../components/Layout'
import type { FreshieMood } from '../components/Freshie'
import { VerificationResults } from '../components/VerificationResults'
import { ANSWER_LIMIT, loadSavedReport, savedDemos } from '../lib/savedReports'
import { verifyLiveAnswer } from '../lib/liveVerification'

const lines = [
  "Teaching AI that confidence isn't a citation.",
  'Politely interrogating the internet.',
  'Somewhere, a cached answer is sweating.',
  'Compiling receipts. The internet never forgets.',
]
type Result = { kind: 'demo'; demo: FixtureDescriptor; report: VerificationReport } | { kind: 'live'; report: VerificationReport }
type Notice = { kind: 'input' | 'unavailable' | 'error' | 'info'; message: string }
const liveEnabled = import.meta.env.DEV && __LIVE_VERIFY_ENABLED__
const unavailable = (report: VerificationReport) => report.status === 'unavailable' || report.status === 'upstream_error'
const labels = { synthetic: 'Scripted fixture', saved_live: 'Captured live report', offline_replay: 'Offline replay' }
const scenarioNames: Record<string, string> = {
  mixed: 'Synthetic example',
  'saved-live': 'Captured uncertain result',
  replay: 'Offline corrected evidence',
  unavailable: 'Simulated upstream failure',
}
const scenarioName = (demo: FixtureDescriptor) => scenarioNames[demo.id] ?? demo.label

function Scanner({ live = false }: { live?: boolean }) {
  const [line, setLine] = useState(0)
  useEffect(() => {
    if (live) return
    const interval = window.setInterval(() => setLine((i) => (i + 1) % lines.length), 3500)
    return () => window.clearInterval(interval)
  }, [live])
  return (
    <div className="glass flex items-center gap-5 rounded-3xl px-5 py-7 sm:px-8" role="status">
      <div className="verify-radar shrink-0" aria-hidden="true"><Radar size={28} /></div>
      <div>
        <p className="font-semibold text-fg">{live ? 'Checking your answer' : 'Opening the saved report'}</p>
        <p className="mt-1 text-sm text-muted">{live ? 'Waiting for the local verifier to return its report.' : lines[line]}</p>
        <p className="mt-2 font-mono text-[11px] text-teal">{live ? 'LIVE VERIFICATION' : 'SAVED DEMO'}</p>
      </div>
    </div>
  )
}

export default function Verify() {
  const { setFreshieMood } = useOutletContext<LayoutContext>()
  const [params] = useSearchParams()
  const demoId = params.get('demo')
  const [answer, setAnswer] = useState('')
  const [sample, setSample] = useState<{ demo: FixtureDescriptor; answer: string } | null>(null)
  const [result, setResult] = useState<Result | null>(null)
  const [mode, setMode] = useState<'demo' | 'live'>('demo')
  const [pending, setPending] = useState<'sample' | 'report' | 'live' | null>(null)
  const [notice, setNotice] = useState<Notice | null>(null)
  const [copied, setCopied] = useState('')
  const [manualCopy, setManualCopy] = useState('')
  const editor = useRef<HTMLTextAreaElement>(null)
  const resultTitle = useRef<HTMLHeadingElement>(null)
  const liveRequest = useRef<AbortController | null>(null)
  const count = Array.from(answer).length
  const matchesSample = sample !== null && answer === sample.answer
  const invalid = count > ANSWER_LIMIT || notice?.kind === 'input'

  useEffect(() => {
    if (demoId === null) {
      if (!liveRequest.current) setPending(null)
      return
    }
    let active = true
    liveRequest.current?.abort()
    liveRequest.current = null
    setMode('demo')
    setAnswer('')
    setSample(null)
    setResult(null)
    setNotice(null)
    setCopied('')
    setManualCopy('')
    const demo = savedDemos.find((item) => item.id === demoId)
    if (!demo) {
      setPending(null)
      setNotice({ kind: 'error', message: 'This saved demo does not exist. Choose an available sample.' })
      return
    }
    setPending('report')
    void loadSavedReport(demo).then((report) => {
      if (!active || report.original_answer === null) return
      setAnswer(report.original_answer)
      setSample({ demo, answer: report.original_answer })
      setResult({ kind: 'demo', demo, report })
    }).catch(() => {
      if (active) setNotice({ kind: 'error', message: 'This saved report could not be opened. Try another demo.' })
    }).finally(() => {
      if (active) setPending(null)
    })
    return () => { active = false }
  }, [demoId])

  useEffect(() => () => {
    liveRequest.current?.abort()
    liveRequest.current = null
  }, [])

  useLayoutEffect(() => {
    let mood: FreshieMood = 'idle'
    if (pending) mood = 'loading'
    else if (notice?.kind === 'error' || (result && unavailable(result.report))) mood = 'error'
    else if (result) {
      const verdicts = result.report.claims.map((claim) => claim.verdict)
      if (verdicts.includes('outdated')) mood = 'outdated'
      else if (verdicts.includes('uncertain')) mood = 'uncertain'
      else mood = verdicts.includes('supported') ? 'supported' : 'uncertain'
    } else if (mode === 'live' && answer.trim()) mood = 'live_ready'
    else if (matchesSample) mood = 'demo'
    else if (answer.trim() && !liveEnabled) mood = 'unconnected'
    setFreshieMood(mood)
  }, [pending, notice, result, matchesSample, answer, mode, setFreshieMood])
  useLayoutEffect(() => () => setFreshieMood('idle'), [setFreshieMood])

  useEffect(() => {
    if (result && resultTitle.current) {
      resultTitle.current.focus({ preventScroll: true })
      resultTitle.current.closest('section')?.scrollIntoView({ block: 'start', behavior: 'auto' })
    }
  }, [result])

  function resetResult() {
    setResult(null)
    setNotice(null)
    setCopied('')
    setManualCopy('')
  }

  async function choose(demo: FixtureDescriptor) {
    if (pending) return
    setMode('demo')
    resetResult()
    setPending('sample')
    try {
      const report = await loadSavedReport(demo)
      const text = report.original_answer!
      setSample({ demo, answer: text })
      setAnswer(text)
      editor.current?.focus()
    } catch {
      setNotice({ kind: 'error', message: 'This saved sample could not be opened. Try another demo.' })
    } finally {
      setPending(null)
    }
  }

  async function verify(event: FormEvent) {
    event.preventDefault()
    if (pending || liveRequest.current) return
    resetResult()
    if (!answer.trim() || count > ANSWER_LIMIT) {
      setNotice({ kind: 'input', message: !answer.trim() ? 'Enter an AI answer or load a saved sample.' : 'Shorten the answer to 16,000 characters or fewer.' })
      editor.current?.focus()
      return
    }
    if (mode === 'live' && liveEnabled) {
      const controller = new AbortController()
      liveRequest.current = controller
      setPending('live')
      try {
        const report = await verifyLiveAnswer(answer, controller.signal)
        if (liveRequest.current === controller) setResult({ kind: 'live', report })
      } catch (error) {
        if (liveRequest.current === controller) setNotice({
          kind: 'error',
          message: error instanceof Error ? error.message : 'Verification could not be completed.',
        })
      } finally {
        if (liveRequest.current === controller) {
          liveRequest.current = null
          setPending(null)
        }
      }
      return
    }
    if (!sample || !matchesSample) {
      setNotice({ kind: 'unavailable', message: liveEnabled
        ? 'Choose Live Verification to check your own text, or load a saved sample.'
        : 'Live verification is disabled. Load a saved sample to explore a report.' })
      return
    }
    setPending('report')
    try {
      // Give the opening state a paint before reading the cached local module.
      // No artificial wait or simulated verification stages.
      await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())))
      const report = await loadSavedReport(sample.demo, answer)
      setResult({ kind: 'demo', demo: sample.demo, report })
    } catch {
      setNotice({ kind: 'error', message: 'This saved report could not be opened or did not match the answer. Try another demo.' })
    } finally {
      setPending(null)
    }
  }

  function cancelLive() {
    liveRequest.current?.abort()
    liveRequest.current = null
    setPending(null)
    setNotice({ kind: 'info', message: 'Stopped waiting in this browser. The verifier may still be working.' })
  }

  async function copy() {
    if (!result) return
    const payload = JSON.stringify(result.kind === 'demo' ? { saved_demo: result.demo, report: result.report } : result.report, null, 2)
    try {
      await navigator.clipboard.writeText(payload)
      setManualCopy('')
      setCopied('Report copied.')
    } catch {
      setManualCopy(payload)
      setCopied('Clipboard access is unavailable. Select and copy the report below.')
    }
  }

  return (
    <div className="verify-page space-y-8 sm:space-y-10">
      <header className="max-w-3xl">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-teal/25 bg-teal/10 px-3 py-1.5 font-mono text-[11px] font-medium uppercase tracking-widest text-teal">
          <ScanLine size={14} aria-hidden="true" /> Verification workspace
        </div>
        <h1 className="text-4xl font-semibold leading-tight tracking-[-0.055em] sm:text-5xl lg:text-6xl">
          Check the answer.<br className="hidden sm:block" /> <span className="text-aurora">Keep the receipts.</span>
        </h1>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-muted sm:text-lg">
          Inspect individual claims, see the exact evidence, and spot what needs a second look.
        </p>
      </header>

      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <form onSubmit={verify} noValidate className="glass verify-editor min-w-0 overflow-hidden rounded-3xl">
          <div role="group" aria-label="Verification mode" className="flex flex-wrap gap-2 border-b border-fg/10 px-5 py-3 sm:px-7">
            {(['demo', 'live'] as const).map((option) => (
              <button key={option} type="button" disabled={!!pending || option === 'live' && !liveEnabled}
                aria-pressed={mode === option}
                onClick={() => { setMode(option); resetResult() }}
                className="rounded-full border border-fg/10 px-3 py-1.5 text-xs font-semibold text-muted hover:bg-fg/5 aria-pressed:border-teal/40 aria-pressed:bg-teal/10 aria-pressed:text-teal disabled:opacity-50">
                {option === 'demo' ? 'Saved Demo' : 'Live Verification'}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 px-5 pb-4 pt-5 sm:px-7">
            <label htmlFor="ai-answer" className="flex items-center gap-2.5 text-sm font-semibold"><FileText size={17} className="text-teal" aria-hidden="true" /> AI-generated answer</label>
            <button type="button" disabled={!answer || !!pending}
              onClick={() => { setAnswer(''); setSample(null); resetResult(); editor.current?.focus() }}
              className="inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-xs text-muted transition-colors hover:bg-fg/5 hover:text-fg disabled:opacity-40">
              <Trash2 size={14} aria-hidden="true" /> Clear
            </button>
          </div>
          <div className="px-5 sm:px-7">
            <textarea id="ai-answer" ref={editor} value={answer} readOnly={!!pending} spellCheck={false}
              aria-invalid={invalid || undefined} aria-describedby={notice ? 'answer-hint answer-notice' : 'answer-hint'}
              onChange={(e) => { setAnswer(e.target.value); setSample(null); resetResult() }}
              placeholder="Paste an AI-generated answer here, or load a saved sample to try the demo…"
              className="verify-textarea min-h-56 w-full resize-y rounded-2xl border border-fg/10 bg-bg/50 px-4 py-4 text-base leading-relaxed text-fg placeholder:text-muted/80 focus:border-teal/55 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal/35 sm:px-5" />
            <div id="answer-hint" className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted">
              <span>{mode === 'live' ? 'Verify Answer sends this text to the local verifier.' : matchesSample ? 'Saved sample ready' : 'Pasted text stays in this tab in demo mode.'}</span>
              <span className={`font-mono tabular-nums ${count > ANSWER_LIMIT ? 'text-warn' : ''}`}>{count.toLocaleString()} / 16,000 characters</span>
            </div>
            {notice && <div id="answer-notice" role={notice.kind === 'info' ? 'status' : 'alert'} className="mt-4 flex items-start gap-2 rounded-xl border border-warn/25 bg-warn/10 p-3 text-sm">
              <CircleAlert size={17} className="mt-0.5 shrink-0 text-warn" aria-hidden="true" /> {notice.message}
            </div>}
          </div>
          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-fg/10 px-5 py-4 sm:px-7">
            <span className="flex items-center gap-2 text-xs font-medium text-muted"><ShieldCheck size={15} className="text-teal" aria-hidden="true" /> {mode === 'live' ? 'Live mode · uses configured providers' : liveEnabled ? 'Saved demo mode' : 'Saved demo mode · live checking off'}</span>
            {pending === 'live' && <button type="button" className="btn-glass !px-4 !py-2 !text-sm" onClick={cancelLive}>Stop waiting</button>}
            <button type="submit" disabled={!!pending} className="btn-primary w-full disabled:pointer-events-none disabled:opacity-50 sm:w-auto">
              <ScanLine size={17} aria-hidden="true" /> {pending === 'report' ? 'Opening report…' : pending === 'live' ? 'Checking answer…' : 'Verify Answer'}
            </button>
          </div>
        </form>

        <aside aria-labelledby="demo-title" className="glass rounded-3xl p-5">
          <div className="flex items-center gap-2.5"><FlaskConical size={19} className="text-lavender" aria-hidden="true" /><h2 id="demo-title" className="font-semibold">Saved demos</h2></div>
          <p className="mt-2 text-sm leading-relaxed text-muted">These samples open existing reports offline. {liveEnabled ? 'Selecting one switches to Saved Demo.' : 'Live verification is disabled.'}</p>
          <div className="mt-4 space-y-2">
            {savedDemos.map((demo) => <button key={demo.id} type="button" onClick={() => void choose(demo)} disabled={!!pending}
              aria-pressed={matchesSample && sample.demo.id === demo.id}
              className="group flex w-full items-center justify-between gap-3 rounded-xl border border-fg/10 bg-bg/30 px-3 py-3 text-left transition-colors hover:border-lavender/55 hover:bg-lavender/10 aria-pressed:border-teal/50 aria-pressed:bg-teal/10 disabled:opacity-60">
              <span className="min-w-0">
                <span className="block text-sm font-medium">{scenarioName(demo)}</span>
                <span className="mt-0.5 block text-xs text-muted">{demo.id === 'unavailable' ? 'Intentional simulation of an unavailable service' : labels[demo.kind]}</span>
              </span>
              <ArrowDownRight size={16} aria-hidden="true" className="shrink-0 text-lavender transition-transform group-hover:translate-x-0.5" />
            </button>)}
            {!savedDemos.length && <p role="status" className="text-sm text-warn">Saved demos are unavailable.</p>}
          </div>
          {pending === 'sample' && <p role="status" className="mt-3 text-sm text-muted">Loading sample…</p>}
        </aside>
      </div>

      {pending === 'report' && <Scanner />}
      {pending === 'live' && <Scanner live />}
      {!pending && !result && !notice && <div className="flex items-center gap-3 rounded-2xl border border-dashed border-fg/15 px-5 py-4 text-sm text-muted">
        <ScanLine size={17} className="shrink-0 text-lavender" aria-hidden="true" /> Your claim report will appear here.
      </div>}
      {result && <section className="space-y-6 border-t border-fg/10 pt-6 sm:space-y-7" aria-labelledby="report-title">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="mb-2 font-mono text-[11px] uppercase tracking-widest text-teal">{result.kind === 'live' ? 'Live Verification' : `Saved Demo · ${labels[result.demo.kind]}`}</div>
            <h2 id="report-title" tabIndex={-1} ref={resultTitle} className="text-3xl font-semibold tracking-tight">Verification report</h2>
            {result.kind === 'demo' && <>
              <p className="mt-2 text-sm font-semibold text-fg">{scenarioName(result.demo)}</p>
              <p className="mt-1 max-w-xl text-sm leading-relaxed text-muted">{result.demo.note}</p>
              {result.demo.id === 'unavailable' && <p className="mt-2 text-sm text-warn">This scenario intentionally simulates a service failure to demonstrate the unavailable state.</p>}
            </>}
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn-glass !px-4 !py-2 !text-sm" onClick={() => void copy()}><ClipboardCopy size={15} aria-hidden="true" /> Copy Report</button>
            <button type="button" className="btn-glass !px-4 !py-2 !text-sm" onClick={() => { resetResult(); editor.current?.focus() }}><RotateCcw size={15} aria-hidden="true" /> Verify Again</button>
          </div>
        </div>
        <p role="status" className={copied ? 'text-sm text-muted' : 'sr-only'}>{copied}</p>
        {manualCopy && <textarea aria-label="Report JSON for manual copy" readOnly rows={5}
          onFocus={(event) => event.currentTarget.select()} value={manualCopy}
          className="glass w-full rounded-xl p-3 font-mono text-xs text-fg" />}
        <VerificationResults report={result.report} />
      </section>}
    </div>
  )
}
