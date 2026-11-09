import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { after, before, test } from 'node:test'
import { createServer } from 'vite'

let vite
let live
before(async () => {
  vite = await createServer({
    configFile: false,
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
    optimizeDeps: { noDiscovery: true, include: [] },
    appType: 'custom',
  })
  live = await vite.ssrLoadModule('/src/lib/liveVerification.ts')
})
after(async () => { await vite?.close() })

test('elapsed time follows the clock and stops its timer on cleanup', (t) => {
  let now = 500
  let tick
  const elapsed = []
  t.mock.method(performance, 'now', () => now)
  t.mock.method(globalThis, 'setInterval', (callback, interval) => {
    assert.equal(interval, 1000)
    tick = callback
    return 17
  })
  const clear = t.mock.method(globalThis, 'clearInterval', () => {})
  const stop = live.watchVerificationElapsed((seconds) => elapsed.push(seconds))
  now = 1500
  tick()
  now = 4125
  tick()
  stop()
  assert.deepEqual(elapsed, [1, 3])
  assert.deepEqual(clear.mock.calls.map(({ arguments: args }) => args), [[17]])
})

test('stopping the browser request aborts the one fetch without retry', async (t) => {
  const controller = new AbortController()
  const fetch = t.mock.method(globalThis, 'fetch', (url, options) => {
    assert.equal(url, '/api/verify')
    assert.equal(options.signal, controller.signal)
    return new Promise((_, reject) => {
      options.signal.addEventListener('abort', () => reject(options.signal.reason), { once: true })
    })
  })
  const waiting = live.verifyLiveAnswer('Example answer', controller.signal)
  controller.abort()
  await assert.rejects(waiting)
  assert.equal(fetch.mock.callCount(), 1)
})

test('adapter failure and deadline have distinct, safe user messages', async (t) => {
  let status = 503
  const fetch = t.mock.method(globalThis, 'fetch', async () => new Response('{}', { status }))
  const controller = new AbortController()
  await assert.rejects(live.verifyLiveAnswer('Example answer', controller.signal),
    { message: 'The local verifier is unavailable. Check that the Python service is running.' })
  status = 504
  await assert.rejects(live.verifyLiveAnswer('Example answer', controller.signal),
    { message: 'The verification wait timed out. The verifier may still be working.' })
  assert.equal(fetch.mock.callCount(), 2)
})

test('provider rate-limit report retains the answer and a safe retry delay', async (t) => {
  const fixture = JSON.parse(await readFile(new URL('../fixtures/synthetic-unavailable.json', import.meta.url), 'utf8'))
  const error = { stage: 'extraction', category: 'upstream_error', code: 'http_error', http_status: 429,
    retryable: true, retry_after_seconds: 60 }
  const report = { ...fixture, mode: 'live', status: 'upstream_error', errors: [error],
    extraction: { ...fixture.extraction, error } }
  const fetch = t.mock.method(globalThis, 'fetch', async () => Response.json(report))
  const signal = new AbortController().signal
  assert.equal((await live.verifyLiveAnswer(report.original_answer, signal)).errors[0].retry_after_seconds, 60)
  report.errors[0].retry_after_seconds = 'not-a-number'
  await assert.rejects(live.verifyLiveAnswer(report.original_answer, signal), /valid live report/)
  assert.equal(fetch.mock.callCount(), 2)
})
