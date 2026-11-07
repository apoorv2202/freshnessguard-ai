import type { Claim, VerificationReport } from '../../contract/types'

export const ANSWER_LIMIT = 16_000

const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)
const string = (value: unknown): value is string => typeof value === 'string'
const date = (value: unknown) => string(value) && Number.isFinite(Date.parse(value))
const numberIn = (value: unknown, max: number) =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= max
const every = (value: unknown, check: (item: unknown) => boolean) => Array.isArray(value) && value.every(check)
const oneOf = (value: unknown, options: string[]) => string(value) && options.includes(value)
const diagnostic = (value: unknown) => record(value) && string(value.stage) && string(value.code)
  && oneOf(value.category, ['upstream_error', 'unavailable'])
  && (value.http_status == null || Number.isInteger(value.http_status) && numberIn(value.http_status, 599))
const witness = (value: unknown) => record(value) && string(value.source_id) && string(value.version)
  && date(value.date) && oneOf(value.date_kind, ['release_date', 'effective_date', 'as_of'])
const nonnegative = (value: unknown) => numberIn(value, Number.MAX_VALUE)
const validMetrics = (value: unknown) => record(value)
  && ['search_calls', 'llm_calls', 'tavily_credits', 'latency_ms'].every((key) => nonnegative(value[key]))
  && typeof value.credit_usage_complete === 'boolean'
const validExtraction = (value: unknown) => record(value)
  && oneOf(value.status, ['pending', 'ok', 'failed', 'skipped'])
  && (value.error === null || diagnostic(value.error))
  && (value.claim_count === undefined || Number.isSafeInteger(value.claim_count) && nonnegative(value.claim_count))

function validClaim(value: unknown): value is Claim {
  if (!record(value) || !string(value.text) || !string(value.subject) || !string(value.reason)
    || !date(value.checked_at) || typeof value.time_sensitive !== 'boolean'
    || !oneOf(value.verdict, ['supported', 'outdated', 'uncertain', 'not_checked'])
    || !(value.correction === null || string(value.correction))
    || !Array.isArray(value.sources) || !Array.isArray(value.citation_ids) || !Array.isArray(value.quotes)) return false

  const sources = new Map<string, string>()
  for (const source of value.sources) {
    if (!record(source) || !string(source.id) || sources.has(source.id) || !string(source.url)
      || !string(source.title) || !string(source.content) || !date(source.retrieved_at)
      || !(source.published_date === null || date(source.published_date))
      || typeof source.primary_source !== 'boolean' || typeof source.future_dated !== 'boolean') return false
    sources.set(source.id, source.content)
  }
  const cited = new Set(value.citation_ids)
  if (!value.citation_ids.every((id: unknown) => string(id) && sources.has(id))) return false
  const quoted = new Set<string>()
  let correctionMatches = false
  for (const quote of value.quotes) {
    if (!record(quote) || !string(quote.source_id) || !string(quote.text) || !quote.text.trim()
      || !cited.has(quote.source_id) || !sources.get(quote.source_id)?.includes(quote.text)) return false
    quoted.add(quote.source_id)
    if (string(value.correction) && quote.text.includes(value.correction)) correctionMatches = true
  }
  if ((value.verdict === 'supported' || value.verdict === 'outdated') && (!cited.size || quoted.size !== cited.size)) return false
  if (value.correction !== null && (!value.correction.trim() || !correctionMatches)) return false
  if (value.verdict === 'outdated' && value.correction === null) return false
  const semantic = value.semantic_validation
  return semantic === undefined || (record(semantic) && oneOf(semantic.status, ['passed', 'rejected'])
    && every(semantic.reasons, string)
    && (semantic.release_witnesses === undefined || every(semantic.release_witnesses, witness))
    && (semantic.observed_release_witnesses === undefined || every(semantic.observed_release_witnesses, witness)))
}

export function isVerificationReport(value: unknown): value is VerificationReport {
  return record(value) && value.schema_version === '1' && string(value.mode) && date(value.checked_at)
    && (value.original_answer === null || string(value.original_answer))
    && numberIn(value.coverage, 1) && (value.freshness_score === null || numberIn(value.freshness_score, 100))
    && oneOf(value.status, ['supported', 'review_required', 'upstream_error', 'unavailable',
      'no_claims_extracted', 'no_time_sensitive_claims', 'incomplete'])
    && every(value.claims, validClaim) && every(value.warnings, string) && every(value.errors, diagnostic)
    && validMetrics(value.metrics) && validExtraction(value.extraction)
}

export function parseLiveReport(value: unknown, answer: string): VerificationReport | null {
  if (!record(value) || value.mode !== 'live' || value.original_answer !== answer || !Array.isArray(value.claims)) return null
  const claims = value.claims.map((claim: unknown) => {
    if (!record(claim) || !Array.isArray(claim.sources)) return claim
    return {
      ...claim,
      sources: claim.sources.map((source: unknown) =>
        record(source) && !date(source.published_date) ? { ...source, published_date: null } : source),
    }
  })
  const normalized = { ...value, claims }
  return isVerificationReport(normalized) && normalized.claims.every((claim) => answer.includes(claim.text))
    ? normalized : null
}
