# ASR demo frontend

Minimal Next.js 14 (App Router, TypeScript) scaffold for the public demo.

## Scope (Tasks 7.1 + 7.2)

Implemented:

- Single page at `/`.
- Upload form with file input, mode selector, preset selector, and submit button.
- Polling of `GET /v1/jobs/{job_id}` after submit.
- Status display (queued / running / completed / failed / polling timed out).
- Selected mode and preset display.
- Transcript display (sourced from `GET /v1/jobs/{job_id}/result` after completion,
  with fallback to the snapshot's `transcript_text`).
- Audio artifact availability for original and enhanced audio.
- Audio players appear only when the artifact URL is browser-playable
  (`http://`, `https://`, `data:`, `blob:`, or `/`-prefixed). Current backend
  artifact URIs use the `s3://` scheme, so the UI shows availability text and
  no `<audio>` element until a browser-playable URL is available.
- Simple timing summary (Created / Started / Completed plus non-negative derived
  durations) when timestamps are present.
- All UI text English.
- Submits and polls through a same-origin Next.js route handler proxy at
  `services/frontend/app/api/[...path]/route.ts` so no backend CORS is needed.

Deferred to later tasks:

- File size, extension, and rate limits (Task 7.3).
- Frontend Docker Compose service and Dockerfile (later demo task).

## Environment

`BACKEND_API_BASE_URL` (server-side only, **not** `NEXT_PUBLIC_*`) configures where the
route-handler proxy forwards requests. Default: `http://localhost:8000`.

The browser only ever calls relative paths under `/api/`; it never reads any env var.

Copy `.env.example` to `.env.local` to override:

```bash
cp .env.example .env.local
```

## Local development

Requires Node `>=18.18.0` and npm.

```bash
npm install
npm run lint
npm run typecheck
npm run build
npm run dev
```

The dev server listens on `http://localhost:3000`. Start the backend stack first
(`docker compose -f infra/compose/docker-compose.yml up -d`) and wait for
`http://localhost:8000/ready` to return 200.
