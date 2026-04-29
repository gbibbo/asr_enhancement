# ASR Enhancement Platform

End-to-end platform for pre-recorded speech enhancement optimized for automatic speech recognition (ASR).

## Purpose

Compare two transcription paths on the same audio file:

1. Raw transcription — upload and transcribe without modification
2. Enhanced transcription — apply a speech enhancement preset before transcribing

Results, artifacts, and job state are fully inspectable through the API.

## Status

Bootstrapping — Cut A (backend vertical slice) in progress.

See [plan.md](plan.md) for the full implementation plan and task breakdown.

## Requirements

- Docker and Docker Compose
- Python 3.11+
- Copy `.env.example` to `.env` and fill in required values before running

## Quick start

```bash
cp .env.example .env
# edit .env as needed
docker compose -f infra/compose/docker-compose.yml up
```

See `plan.md` for the current implementation status and `docs/claude_task_progress.yaml` for task progress.
