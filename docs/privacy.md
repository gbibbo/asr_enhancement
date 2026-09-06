# Privacy — ASR Enhancement Demo

This demo is designed to hold onto as little user data as possible.

## Uploaded audio

- Uploads are limited to **30 seconds** and **5 MB**, English speech.
- Uploaded audio is stored only transiently to run the transcription job, under
  the runtime uploads directory, and is removed by a scheduled cleanup job.
- Cleanup deletes old uploads and per-job artifacts; it never deletes the
  curated-example cache, the usage ledger, aggregate stats, or operational logs.

## Manual ground truth (uploads)

- For an upload you may optionally paste **ground truth** text to see Word
  Accuracy.
- This text is used **only in your browser** to compute the score. It is:
  - never sent to the backend in any request body, form field, or header,
  - never written to browser storage (localStorage / sessionStorage / cookies /
    IndexedDB),
  - never logged, never stored, and never used for training.

The exact in-product wording is: *"Optional ground truth is used only to
calculate accuracy for this session. It is not stored."*

## Language

The demo targets English speech. If the local model detects a non-English
language above a threshold, it shows a warning and asks you to confirm before
continuing, because results on non-English audio are unreliable.

## Logs and secrets

- Structured JSON logs are scrubbed of sensitive fields (transcripts, ground
  truth, session identifiers, file paths, tunnel/credential material) before
  serialization.
- Secrets (recruiter and admin credentials, any AssemblyAI key, tunnel tokens)
  live only in the host `.env.demo` / host environment and are never committed to
  the repository, printed in logs, or shown in screenshots.

## Access

Public access is gated by an HTTP Basic **recruiter** credential enforced by the
application on every `/demo/*` route and on the UI itself. Operational stats at
`/admin/stats` sit behind a separate admin credential. The application gate does
not trust network origin — it is the sole authority regardless of how the request
arrives.
