// Public API contracts consumed by the /demo page. Mirrors what the backend
// exposes through the same-origin Next.js proxy at /api/demo/*. Keep this file
// limited to the public projection — do not add types for any internal-only
// backend field (per-browser hashes, ledger rows, monetary fields, etc.).

export type Provider = "whisper" | "assemblyai";

export type ProviderState =
  | "available"
  | "daily_quota_reached"
  | "quota_exhausted"
  | "disabled";

export type CapState =
  | "below"
  | "warning_reached"
  | "soft_reached"
  | "hard_reached";

export type ProviderStateResponse = {
  assemblyai: {
    state: ProviderState;
    cap_state: CapState;
  };
};

export type DemoExample = {
  example_id: string;
  title: string;
  description: string;
  duration_seconds: number;
  degradation_ids: string[];
  ground_truth: string;
  audio_available: boolean;
  clean_audio_path: string | null;
  degraded_audio_paths: Record<string, string>;
};

export type DemoExamplesResponse = {
  examples: DemoExample[];
  total: number;
  note: string | null;
};

export type DemoHealthResponse = {
  status: "ok";
};

export type LatencyMs = {
  backend: number;
  server: number;
  end_to_end: number;
};

export type RouterDecisionView = {
  selected_backend: string;
  router_kind: string;
  router_version: string;
  routing_profile: string;
  allow_third_party: boolean;
  third_party_provider: string | null;
  cost_policy: string;
  estimated_cost_usd: number;
  predicted_confidence: number;
  predicted_ask_repeat: number;
  routing_explanation: string;
  router_latency_ms: number;
};

export type AssembledResponseView = {
  transcript_text: string;
  selected_backend: string;
  router_kind: string;
  router_version: string;
  routing_profile: string;
  allow_third_party: boolean;
  third_party_provider: string | null;
  estimated_cost_usd: number;
  cost_usd: number;
  backend_confidence: number;
  ask_repeat: number;
  latency_ms: LatencyMs;
  routing_explanation: string;
};

export type DemoWarning = {
  code: string;
  message: string;
  detected_language?: string;
  language_probability?: number;
};

export type DemoResultRaw = {
  transcript: string;
  language: string | null;
  language_probability: number | null;
  latency_seconds: number;
};

// B11.1c: enhanced block emitted by libs/demo/processing.py for upload jobs.
// For the bypass enhancer raw and enhanced are byte-identical; for non-bypass
// (future) the block carries the post-enhancement transcript and latency.
export type DemoResultEnhanced = {
  transcript: string;
  latency_seconds: number;
  preset_applied?: string | null;
  enhanced_flag?: boolean;
  enhancement_fallback?: boolean;
};

// Public projection consumed by /demo. The TS type is deliberately a subset
// of the wire format — forbidden fields (cache_key, session_id_hash, ledger_id,
// audio_sha256, source_report, *_audio_path filesystem paths, key_configured,
// spend, caps, raw provider payload) are intentionally absent so accidental
// access at the call site fails typecheck.
export type DemoResult = {
  source_type?: string;
  provider?: string;
  asr_model_version?: string;
  enhancer_version?: string | null;
  degradation_id?: string | null;
  degradation_version?: string | null;
  degradation_applied?: boolean;
  raw?: DemoResultRaw;
  enhanced?: DemoResultEnhanced | null;
  enhanced_error?: string | null;
  // Cached (B6.5.1 baseline) result_json shape — top-level fields used by the
  // B11.1c comparison panel to bridge cached vs upload payload shapes.
  hypothesis?: string;
  wer?: number | null;
  word_accuracy?: number | null;
  latency_seconds?: number | null;
  warnings?: DemoWarning[];
};

export type RunCachedRequest = {
  example_id: string;
  degradation_id: string;
  provider: Provider;
};

export type RunCachedResponse =
  | { status: "cache_hit"; result: DemoResult; cache_key: string }
  | { status: "cache_miss"; detail: string };

export type DemoJobStatus = "queued" | "running" | "completed" | "failed";

export type DemoJobView = {
  job_id: string;
  status: DemoJobStatus;
  created_at?: string | null;
  updated_at?: string | null;
  provider?: string | null;
  degradation_id?: string | null;
  enhancer_version?: string | null;
  input_artifact_path?: string | null;
  degraded_artifact_path?: string | null;
  enhanced_artifact_path?: string | null;
  result_json?: string | null;
  error_message?: string | null;
  expires_at?: string | null;
};

export type DemoJobResultResponse =
  | { job_id: string; status: "queued" | "running" }
  | { job_id: string; status: "completed"; result: DemoResult }
  | { job_id: string; status: "failed"; error: string | null };

export type UploadAcceptedResponse = {
  job_id: string;
  status: "queued";
};

export type BackendDetail = { detail?: string };
