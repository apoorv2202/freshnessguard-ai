import { parseLiveReport } from './verificationReport'

const messages: Record<number, string> = {
  401: 'The local verifier rejected authentication. Check the server-side token settings.',
  403: 'Open the local app at its configured 127.0.0.1 address.',
  413: 'The answer is too large to send.',
  429: 'The local verifier is busy. Try again when it is available.',
  503: 'The local verifier is unavailable. Check that the Python service is running.',
  504: 'The verification wait timed out. The verifier may still be working.',
}

export function watchVerificationElapsed(onTick: (seconds: number) => void) {
  const started = performance.now()
  const timer = setInterval(() => onTick(Math.floor((performance.now() - started) / 1000)), 1000)
  return () => clearInterval(timer)
}

export async function verifyLiveAnswer(answer: string, signal: AbortSignal) {
  let response: Response
  try {
    response = await fetch('/api/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer }),
      credentials: 'omit',
      redirect: 'error',
      cache: 'no-store',
      signal,
    })
  } catch {
    throw new Error('Could not reach the local adapter. Check that the development server is running.')
  }
  const payload: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const code = (payload as { error?: { code?: unknown } } | null)?.error?.code
    if (code === 'invalid_response') throw new Error('The verifier did not return a valid live report for this answer.')
    throw new Error(messages[response.status] ?? 'Could not reach the local verifier. Check the Python service.')
  }
  const report = parseLiveReport(payload, answer)
  if (!report) throw new Error('The verifier did not return a valid live report for this answer.')
  return report
}
