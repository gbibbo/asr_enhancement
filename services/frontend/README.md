# ASR demo frontend

Minimal Next.js 14 (App Router, TypeScript) scaffold for the public demo. Task 7.1 only.

## Scope

- Single page at `/`.
- Upload form with file input, mode selector, preset selector, and submit button.
- All UI text English.
- Submits to the backend through a same-origin Next.js route handler proxy at
  `services/frontend/app/api/[...path]/route.ts` so no backend CORS is needed.

Deferred to later tasks:

- Polling, status display, transcript view, audio players, timing summary (Task 7.2).
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
