// Frozen backend schema v1 bindings. Runtime validation is still required at
// network/file boundaries. No credential belongs in this module or browser state.
export type ClaimVerdict = "supported" | "outdated" | "uncertain" | "not_checked";
export type ReportStatus = "supported" | "review_required" | "upstream_error" |
  "unavailable" | "no_claims_extracted" | "no_time_sensitive_claims" | "incomplete";
export interface Diagnostic {
  stage: string; category: "upstream_error" | "unavailable";
  code: string; http_status?: number | null; retryable?: boolean;
}
export interface EvidenceQuote { source_id: string; text: string }
export interface Source {
  id: string; url: string; title: string; content: string;
  published_date: string | null; retrieved_at: string;
  primary_source: boolean; source_role?: string; future_dated: boolean;
  acquisition?: {
    method: string; url: string; parent_source_id: string;
    discovery: string; original_reference: string;
    body_sha256?: string; text_sha256?: string; bytes?: number;
    text_truncated?: boolean; content_type?: string;
  };
}
export interface ReleaseWitness {
  source_id: string; version: string; date: string;
  date_kind: "release_date" | "effective_date" | "as_of";
}
export interface Claim {
  text: string; subject: string; time_sensitive: boolean; checked_at: string;
  verdict: ClaimVerdict; reason: string; sources: Source[];
  citation_ids: string[]; quotes: EvidenceQuote[]; correction: string | null;
  error?: Diagnostic; verification_error?: string; verification_skipped?: string;
  proposed_verdict?: "supported" | "outdated" | "uncertain";
  proposed_assessment?: {
    verdict: "supported" | "outdated"; reason: string;
    citation_ids: string[]; quotes: EvidenceQuote[]; correction: string | null;
  };
  quote_windows?: Array<{
    source_id: string; method: "adjacent_dated_release_span_v1";
    // Offsets are Unicode code points in original source.content, not UTF-16.
    original_quote: string; selected_quote: string; start: number; end: number;
  }>;
  semantic_validation?: {
    status: "passed" | "rejected"; reasons: string[];
    proof_kind?: string; release_witnesses?: ReleaseWitness[];
    observed_release_witnesses?: ReleaseWitness[];
    release_evidence_checks?: Array<Record<string, unknown>>;
  };
  source_retrieval?: {
    status: "skipped" | "attempted" | "ok" | "failed"; reason: string;
    url?: string; source_id?: string; parent_source_id?: string; error?: Diagnostic;
  };
}
export interface Metrics {
  search_calls: number; llm_calls: number; tavily_credits: number;
  credit_usage_complete: boolean; latency_ms: number;
  source_retrieval_calls?: number;
  timings_ms?: Record<"extraction" | "search" | "source_retrieval" |
    "judgment" | "semantic_validation" | "total", number>;
  model_tokens?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  model_token_usage_available?: boolean;
}
export interface VerificationReport {
  schema_version: "1"; mode: string; checked_at: string;
  original_answer: string | null; claims: Claim[]; warnings: string[];
  errors: Diagnostic[]; status: ReportStatus;
  coverage: number; // Fraction 0..1, not percent.
  freshness_score: number | null; // Percent 0..100; null means unassessed.
  metrics: Metrics; model?: string | null;
  extraction: { status: "pending" | "ok" | "failed" | "skipped"; claim_count?: number; error: Diagnostic | null };
  scope?: string;
}
export interface GatewayAnnotation {
  status: "checked" | "no_text_to_check" | "unavailable";
  reports: Array<{ choice_index: number; report: VerificationReport }>;
  error?: Diagnostic; reason?: string;
}
export interface VerifyInput { answer: string }
export interface FixtureDescriptor {
  id: string; label: string;
  kind: "synthetic" | "saved_live" | "offline_replay";
  report_file: string; note: string;
}
// Same-origin frontend adapter error body.
export interface UIError { error: { code: string; message: string } }
