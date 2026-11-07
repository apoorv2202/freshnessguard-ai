import { ANSWER_LIMIT, parseLiveReport } from '../src/lib/verificationReport.ts'

const UPSTREAM = 'http://127.0.0.1:8765/verify'
const PATH = '/api/verify'
const BODY_LIMIT = 256_000
const REPORT_LIMIT = 1_000_000
const UPSTREAM_TIMEOUT_MS = 120_000

function reply(res, status, body) {
  if (res.destroyed || res.writableEnded) return
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
  })
  res.end(JSON.stringify(body))
}

function reject(res, status, code, message) {
  reply(res, status, { error: { code, message } })
}

function isJson(value) {
  return typeof value === 'string' && value.split(';', 1)[0].trim().toLowerCase() === 'application/json'
}

async function readJson(stream, limit) {
  const chunks = []
  let size = 0
  for await (const chunk of stream) {
    size += chunk.length
    if (size > limit) return { oversized: true }
    chunks.push(chunk)
  }
  try {
    return { data: JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks))) }
  } catch {
    return {}
  }
}

const upstreamErrors = {
  401: ['verifier_auth', 'The local verifier rejected authentication. Check the server-side token settings.'],
  429: ['verifier_busy', 'The local verifier is busy. Try again when it is available.'],
  503: ['verifier_unavailable', 'The local verifier is unavailable. Check that the Python service is running.'],
}

// fetchImpl and timeoutMs are injectable for offline tests. The request never
// controls the destination, credentials, or deadline.
export function createVerifyMiddleware({ token, origin, fetchImpl = fetch, timeoutMs = UPSTREAM_TIMEOUT_MS }) {
  const host = new URL(origin).host
  const tokenInJson = JSON.stringify(token).slice(1, -1)
  return async function verify(req, res, next) {
    if (req.url !== PATH) return next()
    if (req.headers.host !== host || req.headers.origin !== origin) {
      return reject(res, 403, 'wrong_origin', 'This route accepts requests from the local app origin only.')
    }
    if (req.method !== 'POST') {
      res.setHeader('Allow', 'POST')
      return reject(res, 405, 'invalid_method', 'Use POST to request verification.')
    }
    if (!isJson(req.headers['content-type'])) return reject(res, 415, 'invalid_content_type', 'Send an application/json body.')
    if (Number(req.headers['content-length']) > BODY_LIMIT) {
      req.resume()
      return reject(res, 413, 'body_too_large', 'The request exceeds 256 KB.')
    }

    const controller = new AbortController()
    const disconnect = () => controller.abort()
    res.once('close', disconnect)
    let timer
    let timedOut = false
    try {
      const { data, oversized } = await readJson(req.iterator({ destroyOnReturn: false }), BODY_LIMIT)
      if (oversized) {
        req.resume()
        return reject(res, 413, 'body_too_large', 'The request exceeds 256 KB.')
      }
      if (!data || typeof data !== 'object' || Array.isArray(data)) {
        return reject(res, 400, 'invalid_json', 'Send a valid JSON object.')
      }
      const answer = data.answer
      if (typeof answer !== 'string' || !answer.trim() || Array.from(answer).length > ANSWER_LIMIT) {
        return reject(res, 400, 'invalid_answer', 'Send a JSON object with a nonblank answer of at most 16,000 characters.')
      }
      if (controller.signal.aborted) return
      timer = setTimeout(() => {
        timedOut = true
        controller.abort()
      }, timeoutMs)
      const upstream = await fetchImpl(UPSTREAM, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
        body: JSON.stringify({ answer }),
        signal: controller.signal,
        redirect: 'error',
      })
      if (upstream.status !== 200 || !isJson(upstream.headers.get('content-type'))) {
        await upstream.body?.cancel()
        const error = upstreamErrors[upstream.status]
        return error ? reject(res, upstream.status, ...error)
          : reject(res, 502, 'invalid_response', 'The verifier returned an unexpected response.')
      }
      const { data: raw } = await readJson(upstream.body, REPORT_LIMIT)
      const report = parseLiveReport(raw, answer)
      if (!report || JSON.stringify(report).includes(tokenInJson)) {
        return reject(res, 502, 'invalid_response', 'The verifier did not return a valid live report for this answer.')
      }
      reply(res, 200, report)
    } catch {
      if (timedOut) reject(res, 504, 'verifier_timeout', 'The verification wait timed out. The verifier may still be working.')
      else if (!controller.signal.aborted) reject(res, 502, 'verifier_connection', 'Could not reach the local verifier. Check the Python service.')
    } finally {
      clearTimeout(timer)
      res.removeListener('close', disconnect)
    }
  }
}

export function verifyAdapterPlugin() {
  let enabled = false
  let token = ''
  return {
    name: 'freshnessguard-local-verifier',
    config(_config, { command, isPreview }) {
      enabled = command === 'serve' && !isPreview && process.env.FRESHNESSGUARD_ENABLE_LIVE === '1'
      if (enabled) {
        token = process.env.FRESHNESSGUARD_TOKEN ?? ''
        if (!/^[\x21-\x7e]{24,}$/.test(token)) throw new Error('Set a valid server-side FRESHNESSGUARD_TOKEN before enabling live verification.')
      }
      return { define: { __LIVE_VERIFY_ENABLED__: JSON.stringify(enabled) } }
    },
    configureServer(server) {
      const { host, port, strictPort, https } = server.config.server
      if (host !== '127.0.0.1') throw new Error('FreshnessGuard development server must bind to 127.0.0.1.')
      if (!enabled) return
      if (!strictPort || !port || https) throw new Error('Live verification requires a fixed HTTP loopback development port.')
      server.middlewares.use(createVerifyMiddleware({ token, origin: 'http://127.0.0.1:' + port }))
    },
  }
}
