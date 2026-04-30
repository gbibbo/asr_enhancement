"use client";

import { useEffect, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";

type Mode = "transcribe_only" | "enhance_and_transcribe";
type Preset = "bypass" | "light_clean" | "denoise" | "denoise_dereverb";
type JobStatus = "queued" | "running" | "completed" | "failed";

type JobSnapshot = {
  job_id: string;
  status: JobStatus;
  mode?: string | null;
  provider?: string | null;
  preset?: string | null;
  raw_audio_uri?: string | null;
  enhanced_audio_uri?: string | null;
  transcript_uri?: string | null;
  transcript_text?: string | null;
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
};

type JobResult = {
  job_id: string;
  status: "completed";
  transcript_text: string;
  transcript_uri: string;
  completed_at: string | null;
};

const UNREACHABLE_MSG =
  "Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.";

const PRESETS: Preset[] = ["bypass", "light_clean", "denoise", "denoise_dereverb"];

const POLL_INTERVAL_MS = 2000;
const POLL_MAX_ATTEMPTS = 60;

function isPlayableUrl(uri: string | null | undefined): boolean {
  if (!uri) return false;
  return (
    uri.startsWith("http://") ||
    uri.startsWith("https://") ||
    uri.startsWith("data:") ||
    uri.startsWith("blob:") ||
    uri.startsWith("/")
  );
}

function parseIso(value: string | null | undefined): number | null {
  if (!value) return null;
  const t = Date.parse(value);
  return Number.isFinite(t) ? t : null;
}

function formatDuration(ms: number): string {
  return (Math.max(0, ms) / 1000).toFixed(1) + " s";
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<Mode>("transcribe_only");
  const [preset, setPreset] = useState<Preset>("bypass");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const [jobSnapshot, setJobSnapshot] = useState<JobSnapshot | null>(null);
  const [result, setResult] = useState<JobResult | null>(null);
  const [polling, setPolling] = useState(false);
  const [pollError, setPollError] = useState<string | null>(null);
  const [pollTimedOut, setPollTimedOut] = useState(false);
  const [resultError, setResultError] = useState<string | null>(null);

  useEffect(() => {
    if (mode === "transcribe_only") {
      setPreset("bypass");
    }
  }, [mode]);

  useEffect(() => {
    if (jobId === null) {
      return;
    }

    setJobSnapshot(null);
    setResult(null);
    setPollError(null);
    setPollTimedOut(false);
    setResultError(null);
    setPolling(true);

    let cancelled = false;
    let attempts = 0;
    let timeoutHandle: ReturnType<typeof setTimeout> | null = null;
    const controller = new AbortController();

    async function fetchResult(id: string): Promise<void> {
      let res: Response;
      try {
        res = await fetch(`/api/v1/jobs/${id}/result`, { signal: controller.signal });
      } catch {
        if (cancelled) return;
        setResultError("Cannot reach backend API while loading the result.");
        return;
      }
      if (cancelled) return;
      let body: unknown = null;
      try {
        body = await res.json();
      } catch {
        if (res.status === 200) {
          setResultError("Cannot reach backend API while loading the result.");
          return;
        }
      }
      if (cancelled) return;
      if (res.status === 200) {
        const b = body as Partial<JobResult> | null;
        if (b && b.status === "completed" && typeof b.transcript_text === "string") {
          setResult({
            job_id: id,
            status: "completed",
            transcript_text: b.transcript_text,
            transcript_uri: typeof b.transcript_uri === "string" ? b.transcript_uri : "",
            completed_at:
              typeof b.completed_at === "string" || b.completed_at === null
                ? b.completed_at
                : null,
          });
          return;
        }
        if (b && (b as { status?: string }).status === "failed") {
          const msg = (b as { error_message?: string | null }).error_message;
          setResultError(
            "Job result reports failed: " + (msg && msg.length > 0 ? msg : "no error message recorded.")
          );
          return;
        }
        setResultError("Result endpoint returned 200 but payload was not a completed result.");
        return;
      }
      if (res.status === 202) {
        setResultError("Job result is not yet available.");
        return;
      }
      if (res.status === 404) {
        setResultError("Job result is not available.");
        return;
      }
      if (res.status === 500) {
        const b = body as { error?: string } | null;
        if (b && b.error === "transcript_missing") {
          setResultError("Job completed but transcript is not available.");
          return;
        }
        setResultError("Result endpoint returned 500.");
        return;
      }
      setResultError(`Result endpoint returned ${res.status}.`);
    }

    async function tick(): Promise<void> {
      attempts += 1;
      let res: Response;
      try {
        res = await fetch(`/api/v1/jobs/${jobId}`, { signal: controller.signal });
      } catch {
        if (cancelled) return;
        setPollError(UNREACHABLE_MSG);
        setPolling(false);
        return;
      }
      if (cancelled) return;

      if (res.status === 503) {
        let detail: string | null = null;
        try {
          const j = await res.json();
          if (j && typeof j.detail === "string") {
            detail = j.detail;
          }
        } catch {
          // body not JSON — fall through
        }
        if (cancelled) return;
        setPollError(detail === UNREACHABLE_MSG ? UNREACHABLE_MSG : `Backend returned ${res.status}`);
        setPolling(false);
        return;
      }

      if (res.status === 404) {
        setPollError("Job not found.");
        setPolling(false);
        return;
      }

      if (!res.ok) {
        setPollError(`Backend returned ${res.status}`);
        setPolling(false);
        return;
      }

      let body: unknown;
      try {
        body = await res.json();
      } catch {
        setPollError("Unexpected response from backend.");
        setPolling(false);
        return;
      }
      if (cancelled) return;

      const snap = body as Partial<JobSnapshot> | null;
      if (
        !snap ||
        typeof snap.status !== "string" ||
        !["queued", "running", "completed", "failed"].includes(snap.status)
      ) {
        setPollError("Unexpected response from backend.");
        setPolling(false);
        return;
      }

      const normalized: JobSnapshot = {
        job_id: typeof snap.job_id === "string" ? snap.job_id : (jobId as string),
        status: snap.status as JobStatus,
        mode: snap.mode ?? null,
        provider: snap.provider ?? null,
        preset: snap.preset ?? null,
        raw_audio_uri: snap.raw_audio_uri ?? null,
        enhanced_audio_uri: snap.enhanced_audio_uri ?? null,
        transcript_uri: snap.transcript_uri ?? null,
        transcript_text: snap.transcript_text ?? null,
        error_message: snap.error_message ?? null,
        created_at: snap.created_at ?? null,
        updated_at: snap.updated_at ?? null,
        started_at: snap.started_at ?? null,
        completed_at: snap.completed_at ?? null,
      };
      setJobSnapshot(normalized);

      if (normalized.status === "completed") {
        await fetchResult(normalized.job_id);
        if (cancelled) return;
        setPolling(false);
        return;
      }

      if (normalized.status === "failed") {
        setPolling(false);
        return;
      }

      // queued or running
      if (attempts >= POLL_MAX_ATTEMPTS) {
        setPollTimedOut(true);
        setPolling(false);
        return;
      }
      timeoutHandle = setTimeout(() => {
        if (!cancelled) {
          void tick();
        }
      }, POLL_INTERVAL_MS);
    }

    void tick();

    return () => {
      cancelled = true;
      controller.abort();
      if (timeoutHandle !== null) {
        clearTimeout(timeoutHandle);
      }
    };
  }, [jobId]);

  function onFileChange(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) {
      return;
    }
    setError(null);
    setJobId(null);
    setSubmitting(true);
    try {
      const url =
        mode === "transcribe_only"
          ? "/api/v1/transcribe"
          : "/api/v1/enhance-and-transcribe";
      const fd = new FormData();
      fd.append("file", file);
      if (mode === "enhance_and_transcribe") {
        fd.append("preset", preset);
      }
      const res = await fetch(url, { method: "POST", body: fd });
      if (!res.ok) {
        let detail: string | null = null;
        try {
          const j = await res.json();
          if (j && typeof j.detail === "string") {
            detail = j.detail;
          }
        } catch {
          // body not JSON — fall through to status-based message
        }
        if (res.status === 503 && detail === UNREACHABLE_MSG) {
          setError(UNREACHABLE_MSG);
        } else if (detail) {
          setError(detail);
        } else {
          setError(`Backend returned ${res.status}`);
        }
        return;
      }
      const data = await res.json();
      if (data && typeof data.job_id === "string") {
        setJobId(data.job_id);
      } else {
        setError("Backend returned an unexpected response.");
      }
    } catch {
      setError(UNREACHABLE_MSG);
    } finally {
      setSubmitting(false);
    }
  }

  const presetDisabled = mode === "transcribe_only";

  const displayMode = jobSnapshot?.mode ?? (jobId !== null ? mode : null);
  const displayPreset = jobSnapshot?.preset ?? (jobId !== null ? preset : null);
  const displayStatus: string | null = pollTimedOut
    ? "polling timed out"
    : jobSnapshot?.status ?? (polling ? "polling" : null);

  const transcriptText: string | null =
    (result && result.transcript_text.length > 0 ? result.transcript_text : null) ??
    (jobSnapshot?.transcript_text && jobSnapshot.transcript_text.length > 0
      ? jobSnapshot.transcript_text
      : null);

  const createdMs = parseIso(jobSnapshot?.created_at);
  const startedMs = parseIso(jobSnapshot?.started_at);
  const completedMs = parseIso(jobSnapshot?.completed_at);
  const hasAnyTimestamp =
    jobSnapshot?.created_at != null ||
    jobSnapshot?.started_at != null ||
    jobSnapshot?.completed_at != null;

  const showEnhancedAudio =
    jobSnapshot?.enhanced_audio_uri != null && jobSnapshot.enhanced_audio_uri.length > 0;
  const showOriginalAudio =
    jobSnapshot?.raw_audio_uri != null && jobSnapshot.raw_audio_uri.length > 0;

  return (
    <main>
      <h1>ASR Demo</h1>
      <form onSubmit={onSubmit}>
        <label>
          Audio file
          <input
            type="file"
            accept="audio/*"
            required
            onChange={onFileChange}
          />
        </label>

        <label>
          Mode
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as Mode)}
          >
            <option value="transcribe_only">transcribe_only</option>
            <option value="enhance_and_transcribe">enhance_and_transcribe</option>
          </select>
        </label>

        <label>
          Preset
          <select
            value={preset}
            disabled={presetDisabled}
            onChange={(e) => setPreset(e.target.value as Preset)}
          >
            {PRESETS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>

        <button type="submit" disabled={submitting || !file}>
          {submitting ? "Submitting..." : "Submit"}
        </button>
      </form>

      {error !== null && (
        <p role="alert" className="error">
          {error}
        </p>
      )}

      {jobId !== null && (
        <section className="status">
          <h2>Job</h2>
          <p className="field">
            <span className="field-label">job_id:</span> {jobId}
          </p>
          {displayStatus !== null && (
            <p className="field">
              <span className="field-label">Status:</span> {displayStatus}
            </p>
          )}
          {displayMode !== null && (
            <p className="field">
              <span className="field-label">Mode:</span> {displayMode}
            </p>
          )}
          {displayMode === "enhance_and_transcribe" && displayPreset !== null && (
            <p className="field">
              <span className="field-label">Preset:</span> {displayPreset}
            </p>
          )}

          {pollError !== null && (
            <p role="alert" className="error">
              {pollError}
            </p>
          )}

          {jobSnapshot?.status === "queued" && (
            <p>Job is queued. Waiting for the worker to pick it up.</p>
          )}
          {jobSnapshot?.status === "running" && (
            <p>Job is running. Waiting for completion.</p>
          )}
          {jobSnapshot?.status === "failed" && (
            <p role="alert" className="error">
              {jobSnapshot.error_message && jobSnapshot.error_message.length > 0
                ? jobSnapshot.error_message
                : "Job failed. No error message was recorded."}
            </p>
          )}
          {pollTimedOut && (
            <p role="alert" className="error">
              Polling timed out. The job may still be running. Last status:{" "}
              {jobSnapshot?.status ?? "unknown"}.
            </p>
          )}

          {jobSnapshot?.status === "completed" && (
            <div className="result">
              <h3>Transcript</h3>
              {resultError !== null && (
                <p role="alert" className="error">
                  {resultError}
                </p>
              )}
              <pre className="transcript">
                {transcriptText ?? "Transcript text is not available."}
              </pre>
            </div>
          )}

          {showOriginalAudio && (
            <div className="audio">
              <p className="field">
                <span className="field-label">Original audio:</span> stored at{" "}
                {jobSnapshot!.raw_audio_uri}
              </p>
              {isPlayableUrl(jobSnapshot!.raw_audio_uri) && (
                <audio controls src={jobSnapshot!.raw_audio_uri ?? undefined}>
                  Your browser does not support the audio element.
                </audio>
              )}
            </div>
          )}

          {showEnhancedAudio && (
            <div className="audio">
              <p className="field">
                <span className="field-label">Enhanced audio:</span> stored at{" "}
                {jobSnapshot!.enhanced_audio_uri}
              </p>
              {isPlayableUrl(jobSnapshot!.enhanced_audio_uri) && (
                <audio controls src={jobSnapshot!.enhanced_audio_uri ?? undefined}>
                  Your browser does not support the audio element.
                </audio>
              )}
            </div>
          )}

          {hasAnyTimestamp && (
            <div className="timing">
              <h3>Timing</h3>
              {jobSnapshot?.created_at && (
                <p className="field">
                  <span className="field-label">Created:</span> {jobSnapshot.created_at}
                </p>
              )}
              {jobSnapshot?.started_at && (
                <p className="field">
                  <span className="field-label">Started:</span> {jobSnapshot.started_at}
                </p>
              )}
              {jobSnapshot?.completed_at && (
                <p className="field">
                  <span className="field-label">Completed:</span> {jobSnapshot.completed_at}
                </p>
              )}
              {createdMs !== null && startedMs !== null && (
                <p className="field">
                  <span className="field-label">Time in queue:</span>{" "}
                  {formatDuration(startedMs - createdMs)}
                </p>
              )}
              {startedMs !== null && completedMs !== null && (
                <p className="field">
                  <span className="field-label">Processing time:</span>{" "}
                  {formatDuration(completedMs - startedMs)}
                </p>
              )}
              {createdMs !== null && completedMs !== null && (
                <p className="field">
                  <span className="field-label">Total time:</span>{" "}
                  {formatDuration(completedMs - createdMs)}
                </p>
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}
