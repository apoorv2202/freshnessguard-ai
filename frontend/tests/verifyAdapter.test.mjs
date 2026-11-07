import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { readFile } from 'node:fs/promises'
import { createServer as createHttpServer } from 'node:http'
import { fileURLToPath } from 'node:url'
import { after, before, test } from 'node:test'
import { createServer as createViteServer } from 'vite'

const token = 'synthetic-adapter-test-token'
const sample = JSON.parse(await readFile(new URL('../fixtures/synthetic-mixed.json', import.meta.url), 'utf8'))
const answer = sample.original_answer
let vite
let createVerifyMiddleware

before(async () => {
  vite = await createViteServer({
    configFile: false,
    server: { middlewareMode: true, hmr: false, ws: false, watch: null },
    optimizeDeps: { noDiscovery: true, include: [] },
    appType: 'custom',
  })
  const adapter = await vite.ssrLoadModule('/server/verifyAdapter.mjs')
  createVerifyMiddleware = adapter.createVerifyMiddleware
})
after(async () => { await vite?.close() })

async function withAdapter(fetchImpl, check, timeoutMs) {
  let middleware
  const server = createHttpServer((req, res) => middleware(req, res, () => {
    res.writeHead(404).end()
  }))
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve))
  const origin = 'http://127.0.0.1:' + server.address().port
  middleware = createVerifyMiddleware({ token, origin, fetchImpl, timeoutMs })
  function request(body = JSON.stringify({ answer }), options = {}) {
    const { headers, path = '/api/verify', ...init } = options
    return fetch(origin + path, {
      method: 'POST',
      body,
      ...init,
      headers: { Origin: origin, 'Content-Type': 'application/json', ...headers },
    })
  }
  try {
    await check(request, origin)
  } finally {
    server.closeAllConnections()
    await new Promise((resolve) => server.close(resolve))
  }
}

async function expectError(response, status, code) {
  assert.equal(response.status, status)
  const text = await response.text()
  assert.ok(!text.includes(token))
  assert.equal(JSON.parse(text).error.code, code)
}

test('origin, method, JSON, answer and byte limits are enforced before forwarding', async () => {
  await withAdapter(() => assert.fail('Invalid input reached upstream'), async (request) => {
    await expectError(await request(undefined, { headers: { Origin: 'http://untrusted.test' } }), 403, 'wrong_origin')
    await expectError(await request(null, { method: 'GET' }), 405, 'invalid_method')
    await expectError(await request(undefined, { headers: { 'Content-Type': 'text/plain' } }), 415, 'invalid_content_type')
    await expectError(await request('{'), 400, 'invalid_json')
    await expectError(await request(JSON.stringify({ answer: '  ' })), 400, 'invalid_answer')
    await expectError(await request(JSON.stringify({ answer: '🚀'.repeat(16001) })), 400, 'invalid_answer')
    await expectError(await request('x'.repeat(256001)), 413, 'body_too_large')
    const body = new ReadableStream({ start(controller) {
      controller.enqueue(new Uint8Array(130_000))
      controller.enqueue(new Uint8Array(130_000))
      controller.close()
    } })
    await expectError(await request(body, { duplex: 'half' }), 413, 'body_too_large')
    assert.equal((await request(undefined, { path: '/api/verify?target=other' })).status, 404)
  })
})

test('the adapter sends only the answer and server credentials to the fixed upstream', async () => {
  let calls = 0
  await withAdapter(async (url, options) => {
    calls++
    assert.equal(url, 'http://127.0.0.1:8765/verify')
    assert.equal(options.redirect, 'error')
    assert.deepEqual(options.headers, { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token })
    assert.deepEqual(JSON.parse(options.body), { answer })
    return Response.json({ ...sample, mode: 'live' }, { headers: { 'x-private': token } })
  }, async (request) => {
    const response = await request(JSON.stringify({ answer, url: 'http://elsewhere.invalid' }), {
      headers: { Authorization: 'Browser value', 'X-Untrusted': 'ignored' },
    })
    assert.equal(response.status, 200)
    assert.equal(response.headers.get('x-private'), null)
    assert.ok(!(await response.text()).includes(token))
  })
  assert.equal(calls, 1)
})

test('Python fixture HTTP responses exercise authentication, live shape and date normalization', async () => {
  // The second mode is an explicit test double for the live wire contract.
  // Both modes use the offline fixture engine and loopback HTTP server.
  const script = `
import os
from freshnessguard.fixtures import demo_verifier
from freshnessguard.server import make_server
def factory():
    verifier = demo_verifier()
    def verify(answer):
        report = original(answer)
        if answer != "Use synthetic mode.":
            report["mode"] = "live"
        for claim in report["claims"]:
            for source in claim["sources"]:
                source["published_date"] = "unknown"
        return report
    original = verifier.verify
    verifier.verify = verify
    return verifier
server = make_server(factory, os.environ["FG_TEST_TOKEN"], port=0)
print(server.server_port, flush=True)
server.serve_forever()
`
  const child = spawn('python', ['-B', '-c', script], {
    cwd: fileURLToPath(new URL('../../', import.meta.url)),
    env: { ...process.env, FG_TEST_TOKEN: token },
    stdio: ['ignore', 'pipe', 'ignore'],
    windowsHide: true,
  })
  try {
    const port = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('Python fixture did not start')), 10000)
      child.once('error', (error) => { clearTimeout(timer); reject(error) })
      child.once('exit', () => { clearTimeout(timer); reject(new Error('Python fixture exited')) })
      child.stdout.once('data', (chunk) => { clearTimeout(timer); resolve(Number(String(chunk).trim())) })
    })
    let wrongToken = false
    await withAdapter((_url, options) => fetch('http://127.0.0.1:' + port + '/verify', {
      ...options, headers: wrongToken ? { ...options.headers, Authorization: 'Bearer incorrect' } : options.headers,
    }), async (request) => {
      const response = await request()
      assert.equal(response.status, 200)
      const report = await response.json()
      assert.equal(report.original_answer, answer)
      assert.equal(report.claims[0].sources[0].published_date, null)
      assert.deepEqual(report.claims[0].quotes, sample.claims[0].quotes)
      const arbitrary = await (await request(JSON.stringify({ answer: '🚀'.repeat(16000) }))).json()
      assert.equal(arbitrary.status, 'no_claims_extracted')
      assert.equal(arbitrary.freshness_score, null)
      await expectError(await request(JSON.stringify({ answer: 'Use synthetic mode.' })), 502, 'invalid_response')
      wrongToken = true
      await expectError(await request(), 401, 'verifier_auth')
    })
  } finally {
    child.kill()
  }
})

test('errors and malformed, mismatched or secret-bearing reports are sanitized', async () => {
  const changedQuote = structuredClone(sample)
  changedQuote.claims[0].quotes[0].text = 'invented quote'
  const responses = [
    [Response.json({ error: token }, { status: 429 }), 429, 'verifier_busy'],
    [Response.json({ error: token }, { status: 503 }), 503, 'verifier_unavailable'],
    [new Response('{', { headers: { 'content-type': 'application/json' } }), 502, 'invalid_response'],
    [Response.json({ ...sample, mode: 'live', original_answer: 'Wrong answer' }), 502, 'invalid_response'],
    [Response.json({ ...changedQuote, mode: 'live' }), 502, 'invalid_response'],
    [Response.json({ ...sample, mode: 'live', warnings: [token] }), 502, 'invalid_response'],
  ]
  await withAdapter(() => responses.shift()[0], async (request) => {
    while (responses.length) {
      const [, status, code] = responses[0]
      await expectError(await request(), status, code)
    }
  })
  await withAdapter(() => { throw new Error(token) }, async (request) => {
    await expectError(await request(), 502, 'verifier_connection')
  })
})

test('an upstream redirect is refused before its target receives a request', async () => {
  let targetHits = 0
  const upstream = createHttpServer((req, res) => {
    if (req.url === '/redirect') res.writeHead(307, { Location: '/target' }).end()
    else {
      targetHits++
      res.writeHead(500).end()
    }
  })
  await new Promise((resolve) => upstream.listen(0, '127.0.0.1', resolve))
  try {
    await withAdapter((_url, options) => fetch('http://127.0.0.1:' + upstream.address().port + '/redirect', options),
      async (request) => expectError(await request(), 502, 'verifier_connection'))
    assert.equal(targetHits, 0)
  } finally {
    upstream.closeAllConnections()
    await new Promise((resolve) => upstream.close(resolve))
  }
})

test('timeout and browser disconnect abort the upstream connection without a retry', async () => {
  let calls = 0
  const waitForAbort = (_url, { signal }) => {
    calls++
    return new Promise((_, reject) => signal.addEventListener('abort', () => reject(new Error('aborted')), { once: true }))
  }
  await withAdapter(waitForAbort, async (request) => {
    await expectError(await request(), 504, 'verifier_timeout')
  }, 30)
  assert.equal(calls, 1)
  const browser = new AbortController()
  let start
  let stopped
  const started = new Promise((resolve) => { start = resolve })
  const finished = new Promise((resolve) => { stopped = resolve })
  await withAdapter((url, options) => {
    start()
    return waitForAbort(url, options).finally(stopped)
  }, async (request) => {
    const response = request(undefined, { signal: browser.signal })
    await started
    browser.abort()
    await assert.rejects(response, { name: 'AbortError' })
    await finished
  }, 3000)
  assert.equal(calls, 2)
})
