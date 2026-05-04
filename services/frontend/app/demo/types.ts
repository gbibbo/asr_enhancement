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
  status: "ok" | "degraded";
  mode: "demo";
  db_ok: boolean;
  queue_depth: number;
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

export type DemoResult = {
  source_type?: string;
  provider?: string;
  asr_model_version?: string;
  enhancer_version?: string | null;
  degradation_id?: string | null;
  degradation_version?: string | null;
  raw?: DemoResultRaw;
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
