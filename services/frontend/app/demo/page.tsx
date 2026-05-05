"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";

import { DEGRADATION_IDS, DEGRADATION_LABELS } from "./degradations";
import { computeMetrics, type MetricsResult } from "./scoring";
import { getOrCreateDemoSessionId } from "./session";
import type {
  BackendDetail,
  CapState,
  DemoExample,
  DemoExamplesResponse,
  DemoHealthResponse,
  DemoJobResultResponse,
  DemoJobView,
  DemoResult,
  Provider,
  ProviderState,
  ProviderStateResponse,
  RunCachedResponse,
  UploadAcceptedResponse,
} from "./types";
import { DEGRADATION_VERSION, METRICS_VERSION } from "./versions";

type Mode = "cached_example" | "upload";

const UNREACHABLE_MSG =
  "Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.";

const ALLOWED_EXTENSIONS = [".wav", ".mp3", ".m4a", ".flac"];
const MAX_UPLOAD_BYTES = 5 * 1024 * 1024; // 5 MB (CLAUDE.md §16)
const MAX_UPLOAD_MB = 5;
const MAX_UPLOAD_DURATION_SECONDS = 30;
const POLL_INTERVAL_MS = 2000;
const POLL_MAX_ATTEMPTS = 60; // ~120 s

const NONE_DEGRADATION = "__none__";

type ProviderUiState = {
  state: ProviderState;
  cap_state: CapState;
};

function isAssemblyAISelectable(view: ProviderUiState | null): boolean {
  if (view === null) return false;
  if (view.state !== "available") return false;
  if (view.cap_state === "soft_reached" || view.cap_state === "hard_reached") {
    return false;
  }
  return true;
}

function assemblyaiBadge(view: ProviderUiState | null): string | null {
  if (view === null) return "AssemblyAI: status unknown";
  if (view.state === "disabled") return "AssemblyAI: disabled";
  if (view.state === "daily_quota_reached") {
    return "AssemblyAI: daily quota reached. Try Whisper local.";
  }
  if (view.state === "quota_exhausted") {
    return "AssemblyAI: quota exhausted. Use Whisper local.";
  }
  if (view.state === "available") {
    if (view.cap_state === "soft_reached" || view.cap_state === "hard_reached") {
      return "AssemblyAI: temporarily unavailable. Use Whisper local.";
    }
  }
  return null;
}

function assemblyaiWarningBanner(view: ProviderUiState | null): string | null {
  if (view === null) return null;
  if (view.state !== "available") return null;
  if (view.cap_state === "warning_reached") {
    return "AssemblyAI usage is approaching today's cap. Whisper local is always available.";
  }
  return null;
}

async function readAudioDurationSeconds(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    try {
      const url = URL.createObjectURL(file);
      const audio = document.createElement("audio");
      audio.preload = "metadata";
      const cleanup = () => URL.revokeObjectURL(url);
      audio.onloadedmetadata = () => {
        const d = Number.isFinite(audio.duration) ? audio.duration : null;
        cleanup();
        resolve(d);
      };
      audio.onerror = () => {
        cleanup();
        resolve(null);
      };
      audio.src = url;
    } catch {
      resolve(null);
    }
  });
}

async function readJson<T>(res: Response): Promise<T | null> {
  try {
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

function backendDetail(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const d = (body as BackendDetail).detail;
    if (typeof d === "string" && d.length > 0) return d;
  }
  return fallback;
}

export default function DemoPage() {
  const [mode, setMode] = useState<Mode>("cached_example");

  const [healthOk, setHealthOk] = useState<boolean | null>(null);
  const [providerView, setProviderView] = useState<ProviderUiState | null>(null);

  // Cached-example mode state
  const [examples, setExamples] = useState<DemoExample[]>([]);
  const [examplesNote, setExamplesNote] = useState<string | null>(null);
  const [examplesError, setExamplesError] = useState<string | null>(null);
  const [selectedExampleId, setSelectedExampleId] = useState<string>("");
  const [selectedDegradationCached, setSelectedDegradationCached] = useState<string>("");
  const [cachedSubmitting, setCachedSubmitting] = useState(false);
  const [cachedError, setCachedError] = useState<string | null>(null);
  const [cachedOrigin, setCachedOrigin] = useState<"cache_hit" | "cache_miss" | null>(null);
  const [cachedResult, setCachedResult] = useState<DemoResult | null>(null);
  const [cachedMissDetail, setCachedMissDetail] = useState<string | null>(null);

  // Upload mode state
  const [uploadProvider, setUploadProvider] = useState<Provider>("whisper");
  const [uploadDegradation, setUploadDegradation] = useState<string>(NONE_DEGRADATION);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadSubmitting, setUploadSubmitting] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobSnapshot, setJobSnapshot] = useState<DemoJobView | null>(null);
  const [jobResult, setJobResult] = useState<DemoResult | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [pollTimedOut, setPollTimedOut] = useState(false);
  const [polling, setPolling] = useState(false);

  // B11.1b: original-upload object URL and optional frontend-only manual GT.
  // The object URL is created when uploadFile is non-null and revoked only on
  // file change, on explicit reset, or on unmount — never on submit success or
  // job completion, so the user can still play the original audio after seeing
  // the transcript. Manual GT is held only in component state and never sent
  // to the backend, never persisted, never logged. Word Accuracy / WER are
  // deferred to B11.1c.
  const [uploadObjectUrl, setUploadObjectUrl] = useState<string | null>(null);
  const [manualGt, setManualGt] = useState<string>("");

  const pollControllerRef = useRef<AbortController | null>(null);

  // ---- Backend health + provider state -----------------------------------

  const refreshProviderState = useCallback(async () => {
    try {
      const res = await fetch("/api/demo/providers/assemblyai/status", {
        cache: "no-store",
      });
      if (!res.ok) {
        setProviderView(null);
        return;
      }
      const body = await readJson<ProviderStateResponse>(res);
      if (body && body.assemblyai) {
        setProviderView({
          state: body.assemblyai.state,
          cap_state: body.assemblyai.cap_state,
        });
      } else {
        setProviderView(null);
      }
    } catch {
      setProviderView(null);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/demo/health", { cache: "no-store" });
        if (cancelled) return;
        if (!res.ok) {
          setHealthOk(false);
          return;
        }
        const body = await readJson<DemoHealthResponse>(res);
        setHealthOk(body !== null && body.status === "ok");
      } catch {
        if (!cancelled) setHealthOk(false);
      }
    })();
    void refreshProviderState();
    return () => {
      cancelled = true;
    };
  }, [refreshProviderState]);

  // ---- Examples loader ---------------------------------------------------

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/demo/examples", { cache: "no-store" });
        if (cancelled) return;
        if (!res.ok) {
          setExamplesError(`Backend returned ${res.status} for /demo/examples.`);
          return;
        }
        const body = await readJson<DemoExamplesResponse>(res);
        if (cancelled) return;
        if (body === null) {
          setExamplesError("Unexpected response from /demo/examples.");
          return;
        }
        setExamples(body.examples);
        setExamplesNote(body.note);
        if (body.examples.length > 0) {
          setSelectedExampleId(body.examples[0].example_id);
          if (body.examples[0].degradation_ids.length > 0) {
            setSelectedDegradationCached(body.examples[0].degradation_ids[0]);
          }
        }
      } catch {
        if (!cancelled) setExamplesError(UNREACHABLE_MSG);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Keep degradation selection consistent with the chosen example.
  const selectedExample: DemoExample | undefined = useMemo(
    () => examples.find((e) => e.example_id === selectedExampleId),
    [examples, selectedExampleId],
  );

  useEffect(() => {
    if (!selectedExample) return;
    if (
      !selectedExample.degradation_ids.includes(selectedDegradationCached) &&
      selectedExample.degradation_ids.length > 0
    ) {
      setSelectedDegradationCached(selectedExample.degradation_ids[0]);
    }
  }, [selectedExample, selectedDegradationCached]);

  // If provider becomes unavailable while user has it selected, fall back.
  useEffect(() => {
    if (uploadProvider === "assemblyai" && !isAssemblyAISelectable(providerView)) {
      setUploadProvider("whisper");
    }
  }, [providerView, uploadProvider]);

  // ---- Cached-mode submit ------------------------------------------------

  const submitCached = useCallback(
    async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      if (!selectedExampleId || !selectedDegradationCached) return;
      setCachedSubmitting(true);
      setCachedError(null);
      setCachedOrigin(null);
      setCachedResult(null);
      setCachedMissDetail(null);
      try {
        const res = await fetch("/api/demo/run-cached", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            example_id: selectedExampleId,
            degradation_id: selectedDegradationCached,
            provider: "whisper",
          }),
        });
        const body = await readJson<RunCachedResponse>(res);
        if (!res.ok || body === null) {
          const detail = backendDetail(body, `Backend returned ${res.status}.`);
          setCachedError(detail);
          return;
        }
        if (body.status === "cache_hit") {
          setCachedOrigin("cache_hit");
          setCachedResult(body.result);
        } else {
          setCachedOrigin("cache_miss");
          setCachedMissDetail(
            "This example/degradation combination is not pre-cached. Try another combination or use Upload mode.",
          );
        }
      } catch {
        setCachedError(UNREACHABLE_MSG);
      } finally {
        setCachedSubmitting(false);
      }
    },
    [selectedExampleId, selectedDegradationCached],
  );

  // ---- Upload-mode submit ------------------------------------------------

  const onFileChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setUploadFile(f);
    setUploadError(null);
    // Per B11.1b: clear manual GT only when the user picks a different file.
    setManualGt("");
  }, []);

  // Object URL lifecycle. Cleanup runs when uploadFile changes (revoking the
  // previous URL before the next one is created) and on unmount.
  useEffect(() => {
    if (uploadFile === null) {
      setUploadObjectUrl(null);
      return;
    }
    const url = URL.createObjectURL(uploadFile);
    setUploadObjectUrl(url);
    return () => {
      URL.revokeObjectURL(url);
    };
  }, [uploadFile]);

  const submitUpload = useCallback(
    async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      if (!uploadFile) return;
      setUploadError(null);
      setJobId(null);
      setJobSnapshot(null);
      setJobResult(null);
      setPollError(null);
      setPollTimedOut(false);

      const lower = uploadFile.name.toLowerCase();
      const extOk = ALLOWED_EXTENSIONS.some((ext) => lower.endsWith(ext));
      if (!extOk) {
        setUploadError(
          `File type not allowed. Allowed types: ${ALLOWED_EXTENSIONS.join(", ")}.`,
        );
        return;
      }
      if (uploadFile.size > MAX_UPLOAD_BYTES) {
        setUploadError(`File is too large. Maximum allowed size is ${MAX_UPLOAD_MB} MB.`);
        return;
      }
      const duration = await readAudioDurationSeconds(uploadFile);
      if (duration !== null && duration > MAX_UPLOAD_DURATION_SECONDS) {
        setUploadError(
          `Audio is longer than ${MAX_UPLOAD_DURATION_SECONDS} seconds. Trim and try again.`,
        );
        return;
      }

      if (uploadProvider === "assemblyai" && !isAssemblyAISelectable(providerView)) {
        setUploadError("AssemblyAI is not available right now. Use Whisper local.");
        return;
      }

      setUploadSubmitting(true);
      try {
        const fd = new FormData();
        fd.append("file", uploadFile);
        fd.append("provider", uploadProvider);
        if (uploadDegradation !== NONE_DEGRADATION) {
          fd.append("degradation_id", uploadDegradation);
        }
        const headers: Record<string, string> = {};
        if (uploadProvider === "assemblyai") {
          headers["X-Demo-Session-Id"] = getOrCreateDemoSessionId();
        }
        const res = await fetch("/api/demo/upload", {
          method: "POST",
          body: fd,
          headers,
        });
        const body = await readJson<UploadAcceptedResponse | BackendDetail>(res);
        if (res.status === 202 && body && "job_id" in body && typeof body.job_id === "string") {
          setJobId(body.job_id);
        } else {
          setUploadError(backendDetail(body, `Backend returned ${res.status}.`));
        }
      } catch {
        setUploadError(UNREACHABLE_MSG);
      } finally {
        setUploadSubmitting(false);
        // Refresh provider state in case the upload changed quota/state.
        void refreshProviderState();
      }
    },
    [
      uploadFile,
      uploadProvider,
      uploadDegradation,
      providerView,
      refreshProviderState,
    ],
  );

  // ---- Job polling -------------------------------------------------------

  useEffect(() => {
    if (jobId === null) return;
    if (pollControllerRef.current) {
      pollControllerRef.current.abort();
    }
    const controller = new AbortController();
    pollControllerRef.current = controller;

    let cancelled = false;
    let attempts = 0;
    let timeoutHandle: ReturnType<typeof setTimeout> | null = null;
    setPolling(true);

    async function fetchTerminalResult(id: string): Promise<void> {
      try {
        const res = await fetch(`/api/demo/jobs/${id}/result`, {
          signal: controller.signal,
          cache: "no-store",
        });
        if (cancelled) return;
        const body = await readJson<DemoJobResultResponse>(res);
        if (cancelled) return;
        if (body === null) {
          setPollError("Unexpected result payload from backend.");
          return;
        }
        if (body.status === "completed") {
          setJobResult(body.result);
        } else if (body.status === "failed") {
          // error_message rendering is handled via jobSnapshot.error_message,
          // which is populated by the polling tick. The /result body's `error`
          // field is also captured here in case the snapshot lags.
          setJobSnapshot((prev) =>
            prev
              ? { ...prev, status: "failed", error_message: body.error ?? prev.error_message }
              : { job_id: id, status: "failed", error_message: body.error ?? null },
          );
        }
      } catch (err) {
        if (cancelled) return;
        if ((err as DOMException)?.name === "AbortError") return;
        setPollError("Cannot reach backend API while loading the result.");
      }
    }

    async function tick(): Promise<void> {
      attempts += 1;
      try {
        const res = await fetch(`/api/demo/jobs/${jobId}`, {
          signal: controller.signal,
          cache: "no-store",
        });
        if (cancelled) return;
        if (res.status === 404) {
          setPollError("Job not found.");
          setPolling(false);
          return;
        }
        if (!res.ok) {
          setPollError(`Backend returned ${res.status}.`);
          setPolling(false);
          return;
        }
        const body = await readJson<DemoJobView>(res);
        if (cancelled) return;
        if (body === null || typeof body.status !== "string") {
          setPollError("Unexpected response from backend.");
          setPolling(false);
          return;
        }
        setJobSnapshot(body);
        if (body.status === "completed") {
          await fetchTerminalResult(body.job_id);
          if (!cancelled) setPolling(false);
          return;
        }
        if (body.status === "failed") {
          setPolling(false);
          return;
        }
        if (attempts >= POLL_MAX_ATTEMPTS) {
          setPollTimedOut(true);
          setPolling(false);
          return;
        }
        timeoutHandle = setTimeout(() => {
          if (!cancelled) void tick();
        }, POLL_INTERVAL_MS);
      } catch (err) {
        if (cancelled) return;
        if ((err as DOMException)?.name === "AbortError") return;
        setPollError(UNREACHABLE_MSG);
        setPolling(false);
      }
    }

    void tick();

    return () => {
      cancelled = true;
      controller.abort();
      if (timeoutHandle !== null) clearTimeout(timeoutHandle);
    };
  }, [jobId]);

  // ---- Render helpers ----------------------------------------------------

  const banner = assemblyaiWarningBanner(providerView);
  const aaBadge = assemblyaiBadge(providerView);
  const aaSelectable = isAssemblyAISelectable(providerView);

  const cachedDegradationOptions = selectedExample?.degradation_ids ?? [];

  const cachedCleanAudioReady =
    selectedExample !== undefined &&
    selectedExample.audio_available === true &&
    selectedExample.clean_audio_path !== null &&
    selectedExample.clean_audio_path.length > 0;
  const cachedDegradedAudioReady =
    selectedExample !== undefined &&
    selectedExample.audio_available === true &&
    selectedDegradationCached.length > 0 &&
    typeof selectedExample.degraded_audio_paths?.[selectedDegradationCached] === "string" &&
    selectedExample.degraded_audio_paths[selectedDegradationCached].length > 0;

  return (
    <main className="demo-main">
      <header className="demo-header">
        <h1>ASR Enhancement — Public Demo</h1>
        <p className="demo-subtle">
          Backend:{" "}
          <span
            className={
              healthOk === null
                ? "dot dot-unknown"
                : healthOk
                  ? "dot dot-ok"
                  : "dot dot-bad"
            }
            aria-label={
              healthOk === null
                ? "backend status unknown"
                : healthOk
                  ? "backend ok"
                  : "backend unavailable"
            }
          />
          {healthOk === null ? " checking…" : healthOk ? " ok" : " unavailable"}
        </p>
      </header>

      {banner !== null && (
        <p className="demo-banner demo-banner-warn" role="status">
          {banner}
        </p>
      )}

      <nav className="demo-tabs" aria-label="Demo mode">
        <button
          type="button"
          className={mode === "cached_example" ? "demo-tab demo-tab-active" : "demo-tab"}
          onClick={() => setMode("cached_example")}
        >
          Curated examples
        </button>
        <button
          type="button"
          className={mode === "upload" ? "demo-tab demo-tab-active" : "demo-tab"}
          onClick={() => setMode("upload")}
        >
          Upload audio
        </button>
      </nav>

      {mode === "cached_example" && (
        <section className="demo-section" aria-labelledby="cached-heading">
          <h2 id="cached-heading">Curated examples (cached)</h2>
          {examplesError !== null && (
            <p role="alert" className="error">
              {examplesError}
            </p>
          )}
          {examplesNote !== null && (
            <p className="demo-subtle">{examplesNote}</p>
          )}
          <form onSubmit={submitCached} className="demo-form">
            <label>
              Example
              <select
                value={selectedExampleId}
                onChange={(e) => setSelectedExampleId(e.target.value)}
                disabled={examples.length === 0}
              >
                {examples.map((ex) => (
                  <option key={ex.example_id} value={ex.example_id}>
                    {ex.title || ex.example_id}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Degradation
              <select
                value={selectedDegradationCached}
                onChange={(e) => setSelectedDegradationCached(e.target.value)}
                disabled={cachedDegradationOptions.length === 0}
              >
                {cachedDegradationOptions.map((d) => (
                  <option key={d} value={d}>
                    {DEGRADATION_LABELS[d as keyof typeof DEGRADATION_LABELS] ?? d}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Provider
              <select value="whisper" disabled aria-label="Provider locked to whisper">
                <option value="whisper">whisper (cached only)</option>
              </select>
            </label>

            <button
              type="submit"
              disabled={
                cachedSubmitting ||
                examples.length === 0 ||
                !selectedExampleId ||
                !selectedDegradationCached
              }
            >
              {cachedSubmitting ? "Running…" : "Run cached example"}
            </button>
          </form>

          {selectedExample !== undefined && (
            <div className="demo-audio-row" aria-label="Original audio">
              <p className="demo-audio-label">Original audio (clean)</p>
              {cachedCleanAudioReady ? (
                <audio
                  controls
                  preload="metadata"
                  src={`/api/demo/examples/${encodeURIComponent(
                    selectedExample.example_id,
                  )}/audio/clean`}
                />
              ) : (
                <p className="demo-subtle">Audio unavailable for this example.</p>
              )}
            </div>
          )}

          {selectedExample !== undefined && selectedDegradationCached.length > 0 && (
            <div className="demo-audio-row" aria-label="Degraded audio">
              <p className="demo-audio-label">
                Degraded audio (
                {DEGRADATION_LABELS[
                  selectedDegradationCached as keyof typeof DEGRADATION_LABELS
                ] ?? selectedDegradationCached}
                )
              </p>
              {cachedDegradedAudioReady ? (
                <audio
                  controls
                  preload="metadata"
                  src={`/api/demo/examples/${encodeURIComponent(
                    selectedExample.example_id,
                  )}/audio/degraded/${encodeURIComponent(selectedDegradationCached)}`}
                />
              ) : (
                <p className="demo-subtle">
                  Audio unavailable for this example/degradation.
                </p>
              )}
            </div>
          )}

          {selectedExample !== undefined &&
            typeof selectedExample.ground_truth === "string" &&
            selectedExample.ground_truth.length > 0 && (
              <div className="demo-gt" aria-label="Ground truth (verified)">
                <p className="demo-audio-label">Ground truth (verified)</p>
                <pre className="demo-transcript">{selectedExample.ground_truth}</pre>
              </div>
            )}

          {cachedError !== null && (
            <p role="alert" className="error">
              {cachedError}
            </p>
          )}

          {cachedOrigin === "cache_miss" && cachedMissDetail !== null && (
            <p role="status" className="demo-banner demo-banner-info">
              {cachedMissDetail}
            </p>
          )}

          {cachedOrigin === "cache_hit" && cachedResult !== null && (
            <ResultPanel
              origin="cache_hit"
              result={cachedResult}
              reference={
                selectedExample !== undefined &&
                typeof selectedExample.ground_truth === "string" &&
                selectedExample.ground_truth.trim().length > 0
                  ? selectedExample.ground_truth
                  : null
              }
              jobId={null}
              errorMessage={null}
            />
          )}
        </section>
      )}

      {mode === "upload" && (
        <section className="demo-section" aria-labelledby="upload-heading">
          <h2 id="upload-heading">Upload audio</h2>
          <p className="demo-subtle">
            English speech, up to {MAX_UPLOAD_DURATION_SECONDS}&nbsp;seconds and {MAX_UPLOAD_MB}&nbsp;MB. Allowed:{" "}
            {ALLOWED_EXTENSIONS.join(", ")}.
          </p>

          {aaBadge !== null && (
            <p className="demo-badge" role="status">
              {aaBadge}
            </p>
          )}

          <form onSubmit={submitUpload} className="demo-form">
            <label>
              Audio file
              <input
                type="file"
                accept=".wav,.mp3,.m4a,.flac,audio/*"
                required
                onChange={onFileChange}
              />
            </label>

            <label>
              Provider
              <select
                value={uploadProvider}
                onChange={(e) => setUploadProvider(e.target.value as Provider)}
              >
                <option value="whisper">whisper (local)</option>
                <option value="assemblyai" disabled={!aaSelectable}>
                  assemblyai{aaSelectable ? "" : " (unavailable)"}
                </option>
              </select>
            </label>

            <label>
              Degradation
              <select
                value={uploadDegradation}
                onChange={(e) => setUploadDegradation(e.target.value)}
              >
                <option value={NONE_DEGRADATION}>none</option>
                {DEGRADATION_IDS.map((d) => (
                  <option key={d} value={d}>
                    {DEGRADATION_LABELS[d]}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Optional ground truth
              <textarea
                className="demo-textarea"
                value={manualGt}
                onChange={(e) => setManualGt(e.target.value)}
                rows={3}
                placeholder="Type the spoken text if you want to compare later."
              />
            </label>
            <p className="demo-gt-privacy demo-subtle">
              Optional ground truth is used only to calculate accuracy for this session. It is not stored.
            </p>

            <button type="submit" disabled={uploadSubmitting || !uploadFile}>
              {uploadSubmitting ? "Submitting…" : "Submit upload"}
            </button>
          </form>

          {uploadObjectUrl !== null && (
            <div className="demo-audio-row" aria-label="Uploaded audio">
              <p className="demo-audio-label">Original audio (your upload)</p>
              <audio controls preload="metadata" src={uploadObjectUrl} />
            </div>
          )}

          {uploadError !== null && (
            <p role="alert" className="error">
              {uploadError}
            </p>
          )}

          {jobId !== null && (
            <>
              {(() => {
                const externalStatus = pollTimedOut
                  ? "polling timed out"
                  : (jobSnapshot?.status ?? (polling ? "polling" : null));
                return externalStatus !== null ? (
                  <p className="demo-subtle" role="status">
                    Job status: {externalStatus}
                  </p>
                ) : null;
              })()}
              <ResultPanel
                origin={
                  (jobResult?.provider ?? jobSnapshot?.provider) === "assemblyai"
                    ? "computed_assemblyai"
                    : "computed_whisper"
                }
                result={jobResult}
                reference={manualGt.trim().length > 0 ? manualGt.trim() : null}
                jobId={jobId}
                errorMessage={
                  jobSnapshot?.status === "failed"
                    ? jobSnapshot.error_message ?? "Job failed."
                    : null
                }
              />
            </>
          )}

          {pollError !== null && (
            <p role="alert" className="error">
              {pollError}
            </p>
          )}
        </section>
      )}
    </main>
  );
}

type ResultPanelProps = {
  origin: "cache_hit" | "computed_whisper" | "computed_assemblyai";
  result: DemoResult | null;
  reference: string | null;
  jobId: string | null;
  errorMessage: string | null;
};

function formatPercent(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

function formatWer(v: number): string {
  return v.toFixed(2);
}

function MetricLine({ metrics }: { metrics: MetricsResult | null }) {
  if (
    metrics === null ||
    !metrics.available ||
    metrics.wer === null ||
    metrics.wordAccuracy === null
  ) {
    return null;
  }
  return (
    <p className="demo-metric-line demo-subtle">
      Word Accuracy: {formatPercent(metrics.wordAccuracy)} • WER:{" "}
      {formatWer(metrics.wer)}
    </p>
  );
}

function ResultPanel(props: ResultPanelProps) {
  const { origin, result, reference, jobId, errorMessage } = props;

  const originLabel =
    origin === "cache_hit"
      ? "Loaded from cache"
      : origin === "computed_assemblyai"
        ? "computed (assemblyai)"
        : "computed (whisper)";

  const provider = result?.provider ?? null;
  const asrModelVersion = result?.asr_model_version ?? null;
  const enhancerVersion = result?.enhancer_version ?? null;
  const degradationId = result?.degradation_id ?? null;
  const degradationVersion = result?.degradation_version ?? DEGRADATION_VERSION;
  const degradationApplied = result?.degradation_applied;
  const warnings = result?.warnings;
  const enhancedError = result?.enhanced_error ?? null;
  const isBypass = enhancerVersion === "bypass";

  // Bridge cached vs upload payload shapes:
  //   cached prewarm payload:  top-level `hypothesis` + `latency_seconds`
  //   upload result_json:      `raw.transcript` / `enhanced.transcript` /
  //                            `raw.latency_seconds`
  const rawTranscript: string | null =
    result?.raw?.transcript ?? result?.hypothesis ?? null;
  const enhancedTranscript: string | null =
    result?.enhanced?.transcript ?? result?.hypothesis ?? null;
  const latency: number | null =
    result?.raw?.latency_seconds ?? result?.latency_seconds ?? null;

  const rawMetrics =
    rawTranscript !== null ? computeMetrics(rawTranscript, reference) : null;
  const enhancedMetrics =
    enhancedTranscript !== null
      ? computeMetrics(enhancedTranscript, reference)
      : null;

  const noTranscriptYet =
    rawTranscript === null && enhancedTranscript === null && errorMessage === null;

  return (
    <div className="demo-result">
      <h3>Result</h3>

      {warnings !== undefined && warnings.length > 0 && (
        <ul className="demo-warnings">
          {warnings.map((w, idx) => (
            <li key={`${w.code}-${idx}`} className="demo-banner demo-banner-warn">
              {w.message}
            </li>
          ))}
        </ul>
      )}

      {errorMessage !== null && (
        <p role="alert" className="error">
          {errorMessage}
        </p>
      )}

      <section className="demo-compare" aria-label="Raw and enhanced comparison">
        {rawTranscript !== null && (
          <div className="demo-compare-block">
            <p className="demo-compare-label">Raw transcript</p>
            <pre className="demo-transcript">{rawTranscript}</pre>
            <MetricLine metrics={rawMetrics} />
          </div>
        )}

        {enhancedTranscript !== null && (
          <div className="demo-compare-block">
            <p className="demo-compare-label">Enhanced transcript</p>
            {enhancedError !== null && (
              <p className="demo-banner demo-banner-warn">{enhancedError}</p>
            )}
            <pre className="demo-transcript">{enhancedTranscript}</pre>
            <MetricLine metrics={enhancedMetrics} />
          </div>
        )}

        {noTranscriptYet && (
          <p className="demo-subtle">Transcript is not available yet.</p>
        )}

        {isBypass && rawTranscript !== null && enhancedTranscript !== null && (
          <p className="demo-bypass-note demo-subtle">
            Enhancer is bypass — audio is not enhanced. Raw and enhanced
            transcripts are identical.
          </p>
        )}
      </section>

      <details className="demo-pipeline-details">
        <summary>Pipeline details</summary>
        <dl className="demo-meta">
          {jobId !== null && (
            <>
              <dt>job_id</dt>
              <dd className="demo-mono">{jobId}</dd>
            </>
          )}
          <dt>cache status</dt>
          <dd>{originLabel}</dd>
          {provider !== null && provider.length > 0 && (
            <>
              <dt>provider</dt>
              <dd>{provider}</dd>
            </>
          )}
          {asrModelVersion !== null && asrModelVersion.length > 0 && (
            <>
              <dt>asr_model_version</dt>
              <dd>{asrModelVersion}</dd>
            </>
          )}
          {enhancerVersion !== null && enhancerVersion.length > 0 && (
            <>
              <dt>enhancer_version</dt>
              <dd>{enhancerVersion}</dd>
            </>
          )}
          {degradationId !== null && degradationId.length > 0 && (
            <>
              <dt>degradation_id</dt>
              <dd>{degradationId}</dd>
            </>
          )}
          <dt>degradation_version</dt>
          <dd>{degradationVersion}</dd>
          {degradationApplied !== undefined && (
            <>
              <dt>degradation_applied</dt>
              <dd>{degradationApplied ? "true" : "false"}</dd>
            </>
          )}
          <dt>metrics_version</dt>
          <dd>{METRICS_VERSION}</dd>
          {latency !== null && (
            <>
              <dt>latency_seconds</dt>
              <dd>{latency.toFixed(3)}</dd>
            </>
          )}
        </dl>
      </details>
    </div>
  );
}
