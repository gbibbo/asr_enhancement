"use client";

import { useEffect, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";

type Mode = "transcribe_only" | "enhance_and_transcribe";
type Preset = "bypass" | "light_clean" | "denoise" | "denoise_dereverb";

const UNREACHABLE_MSG =
  "Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.";

const PRESETS: Preset[] = ["bypass", "light_clean", "denoise", "denoise_dereverb"];

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<Mode>("transcribe_only");
  const [preset, setPreset] = useState<Preset>("bypass");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  useEffect(() => {
    if (mode === "transcribe_only") {
      setPreset("bypass");
    }
  }, [mode]);

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
        <p className="queued">Job queued. job_id: {jobId}</p>
      )}
    </main>
  );
}
