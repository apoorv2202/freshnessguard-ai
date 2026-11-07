import { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

export type FreshieMood = 'idle' | 'demo' | 'loading' | 'supported' | 'outdated' | 'uncertain' | 'error' | 'unconnected' | 'live_ready'

const idleLines = ['Awaiting a claim. My circuits are doing stretches.', 'I alphabetized my receipts for this.']

const moods: Record<FreshieMood, { label: string; accent: string; mouth: string }> = {
  idle: { label: idleLines[0], accent: 'text-teal', mouth: 'M24 34q4 5 8 0' },
  demo: { label: 'Demo ready!', accent: 'text-lavender', mouth: 'M23 33q5 8 10 0' },
  live_ready: { label: 'Ready when you are.', accent: 'text-teal', mouth: 'M24 34q4 5 8 0' },
  loading: { label: 'Checking the receipts...', accent: 'text-blue', mouth: 'M25 35h6' },
  supported: { label: 'The evidence backs this up!', accent: 'text-teal', mouth: 'M23 33q5 8 10 0' },
  outdated: { label: 'Stale claim found!', accent: 'text-orchid', mouth: 'M23 37q5-6 10 0' },
  uncertain: { label: "The evidence isn't conclusive yet.", accent: 'text-warn', mouth: 'M24 36l8-2' },
  error: { label: "Couldn't verify this one.", accent: 'text-warn', mouth: 'M23 37q5-5 10 0' },
  unconnected: { label: "Live checking isn't connected yet.", accent: 'text-muted', mouth: 'M25 35h6' },
}

export function Freshie({ mood }: { mood: FreshieMood }) {
  const [minimized, setMinimized] = useState(false)
  const [idleLine, setIdleLine] = useState(0)
  const { label, accent, mouth } = moods[mood]
  useEffect(() => {
    if (mood !== 'idle' || minimized) return
    const timer = window.setInterval(() => setIdleLine((line) => (line + 1) % idleLines.length), 10000)
    return () => window.clearInterval(timer)
  }, [mood, minimized])

  return (
    <aside aria-label="Freshie" className="shrink-0 border-t border-fg/10 bg-card/65 px-3 py-1.5 backdrop-blur-md sm:px-5">
      <div className="mx-auto flex max-w-6xl items-center justify-end gap-2">
        <p id="freshie-message" hidden={minimized} aria-live={mood === 'idle' ? 'off' : 'polite'} className="min-w-0 rounded-2xl border border-fg/10 bg-bg/45 px-3 py-2 text-xs leading-snug text-fg sm:text-sm">
          <span className="mr-1.5 font-semibold text-muted">Freshie</span> {mood === 'idle' ? idleLines[idleLine] : label}
        </p>
        <button type="button" aria-label={minimized ? 'Restore Freshie' : 'Minimize Freshie'}
          aria-expanded={!minimized} aria-controls="freshie-message" onClick={() => setMinimized((value) => !value)}
          className={`glass inline-flex min-h-11 shrink-0 items-center gap-0.5 rounded-xl px-1.5 hover:bg-fg/10 ${accent}`}>
        <svg aria-hidden="true" viewBox="0 0 56 56" className={`h-8 w-8 ${mood === 'loading' ? 'animate-pulse' : ''}`} fill="none">
          <path d="M28 10v6M8 26v8m40-8v8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          <circle cx="28" cy="8" r="3" fill="currentColor" />
          <rect x="11" y="16" width="34" height="28" rx="10" fill="currentColor" fillOpacity=".1" stroke="currentColor" strokeWidth="1.8" />
          <rect x="16" y="21" width="24" height="18" rx="6" fill="rgb(var(--bg))" />
          <path d={mood === 'error' ? 'm20 25 4 4m0-4-4 4m12-4 4 4m0-4-4 4' : 'M22 26v2m12-2v2'} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
          <path d={mouth} stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
          {minimized ? <ChevronUp size={13} aria-hidden="true" /> : <ChevronDown size={13} aria-hidden="true" />}
        </button>
      </div>
    </aside>
  )
}
