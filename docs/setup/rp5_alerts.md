# RP5 Alert Setup (B12.2)

## Overview

B12.2 adds two operator alert scripts for the public demo runtime on the
Raspberry Pi 5. Alerts fire when:

1. Disk usage exceeds 80% (configurable threshold).
2. The `/demo/health` endpoint returns 3 consecutive failures (configurable threshold).

Both scripts are run by cron inside a one-off Compose container. Alerts are
sent by email via SMTP. When SMTP credentials are not configured, each script
runs in dry-run mode: a structured log line is emitted and the script exits 0.
No live SMTP traffic occurs by default.

---

## Configuration

All settings are supplied via environment variables. Real credentials live only
in the host `.env.demo` file — they are never committed to the repository.

The `.env.demo.example` file contains a template with empty placeholders.
Copy it to `.env.demo` and fill in the values:

```bash
cp .env.demo.example .env.demo
# Edit .env.demo with real values; this file is gitignored.
```

### Required variables for real email sends

| Variable | Description |
| -------- | ----------- |
| `DEMO_ALERT_EMAIL_ENABLED` | Set to `true` to enable real sends. Default: `false`. |
| `DEMO_ALERT_EMAIL_TO` | Recipient address. Set to the maintainer address. Not committed. |
| `DEMO_ALERT_EMAIL_FROM` | Sender address (must match the SMTP account). |
| `DEMO_ALERT_SMTP_HOST` | SMTP server hostname (e.g. `smtp.gmail.com`). |
| `DEMO_ALERT_SMTP_PORT` | SMTP port. Default: `587`. |
| `DEMO_ALERT_SMTP_USERNAME` | SMTP login username. |
| `DEMO_ALERT_SMTP_PASSWORD` | SMTP password or app password. Never committed. |

If any of these five SMTP fields or the recipient is missing, the scripts fall
back to dry-run mode automatically.

### Optional tuning variables

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `DEMO_ALERT_SMTP_USE_STARTTLS` | `true` | Use STARTTLS on the SMTP connection. |
| `DEMO_ALERT_SMTP_TIMEOUT_SECONDS` | `10` | SMTP connection timeout in seconds. |
| `DEMO_ALERT_DISK_THRESHOLD_PERCENT` | `80.0` | Disk usage percent that triggers an alert. |
| `DEMO_ALERT_DISK_COOLDOWN_HOURS` | `6` | Minimum hours between repeated disk alerts. |
| `DEMO_ALERT_HEALTH_CONSECUTIVE_FAILURES` | `3` | Number of consecutive failures before alerting. |
| `DEMO_ALERT_HEALTH_COOLDOWN_MINUTES` | `30` | Minimum minutes between repeated health alerts. |
| `DEMO_ALERT_HEALTH_URL` | `http://localhost:8001/demo/health` | Health check URL. See Host vs. Compose URL below. |
| `DEMO_ALERT_HEALTH_STATE_FILE` | `<runtime_root>/state/health_check.json` | Path to the JSON state file tracking consecutive failures. |

### App-password / SMTP credentials

If using Gmail or another provider that requires an app password, generate the
app password in your email provider's security settings and supply it as
`DEMO_ALERT_SMTP_PASSWORD` in the host `.env.demo`. The app password is never
committed to the repository.

---

## Host vs. Compose URL

The `DEMO_ALERT_HEALTH_URL` setting has two correct values depending on how the
script runs:

**Host-side / manual dry-run** (running directly on the RP5, outside Docker):

```
DEMO_ALERT_HEALTH_URL=http://localhost:8001/demo/health
```

This is the `DemoSettings` default and is correct when the script runs on the
RP5 host because port 8001 is mapped from the `demo-api` container.

**Docker Compose cron** (script runs inside a one-off Compose container):

```
DEMO_ALERT_HEALTH_URL=http://demo-api:8000/demo/health
```

Inside a one-off Compose container, `localhost:8001` resolves to the
container's own loopback, not the host port mapping. The Compose-network DNS
name `demo-api:8000` reaches the long-running `demo-api` service that was
started by `docker compose up -d demo-api demo-worker`. The reference cron
entries in `infra/cron/asr-demo-alerts.cron` already apply this override.

**Recruiter gate:**

`/demo/health` is behind the recruiter HTTPBasic gate, so an unauthenticated
probe gets a permanent `401` and reports a healthy demo as down. The script
sends Basic credentials from `RECRUITER_USERNAME` / `RECRUITER_PASSWORD`
whenever both are set — the same `.env.demo` values the API container already
receives, so the Compose cron entries need no extra configuration. The
credentials are used only to build the `Authorization` header and never appear
in logs or in the alert body. If they are unset the probe goes out
unauthenticated and a gated endpoint reports `http_4xx`.

**Public / Cloudflare URL** (future, after B14.1):

Once the Cloudflare Tunnel is configured, the health script can be repointed
to the public URL with no code changes:

```
DEMO_ALERT_HEALTH_URL=https://<your-domain>/demo/health
```

---

## Cron install

The cron entries are reference-only in `infra/cron/asr-demo-alerts.cron`.
Install them manually via `crontab -e`. Do NOT copy the file to `/etc/cron.d`.

1. Open the crontab editor:

   ```bash
   crontab -e
   ```

2. Paste the two entries from `infra/cron/asr-demo-alerts.cron`. They run as
   the `gbibbo` user and write output to the shared alerts log:

   ```
   /home/gbibbo/asr_enhancement_runtime/logs/alerts.cron.log
   ```

3. Ensure the log directory exists:

   ```bash
   mkdir -p /home/gbibbo/asr_enhancement_runtime/logs
   ```

4. Save and exit. Verify with:

   ```bash
   crontab -l
   ```

---

## Dry-run verification

Before enabling real SMTP, test the scripts in dry-run mode (no credentials
configured).

**Disk alert dry-run** (forces threshold to 0% so disk always fires):

```bash
docker compose -f infra/compose/docker-compose.demo.yml run --rm --no-deps \
  -v "$PWD/scripts:/app/scripts:ro" \
  -e DEMO_ALERT_DISK_THRESHOLD_PERCENT=0.0 \
  demo-api \
  python -m scripts.demo.alert_disk
```

Expected: exit 0, one `alert.dry_run` JSON log line, no SMTP connection.

**Health alert dry-run** (uses port 9 "discard" to force connection_error):

```bash
docker compose -f infra/compose/docker-compose.demo.yml run --rm --no-deps \
  -v "$PWD/scripts:/app/scripts:ro" \
  -e DEMO_ALERT_HEALTH_URL=http://127.0.0.1:9/demo/health \
  -e DEMO_ALERT_HEALTH_CONSECUTIVE_FAILURES=1 \
  -e DEMO_ALERT_HEALTH_STATE_FILE=/tmp/b12_2_health_dry_run.json \
  demo-api \
  python -m scripts.demo.alert_health
```

Expected: exit 0, failure classified as `connection_error` or `timeout`,
one `alert.dry_run` JSON log line.

Live SMTP test (real send) is performed by the maintainer after explicit
approval with real SMTP credentials in `.env.demo`.

---

## Troubleshooting

**Alerts not firing:**

- Check `DEMO_ALERT_EMAIL_ENABLED=true` is set in `.env.demo`.
- Confirm all five required SMTP fields are non-empty.
- Run the dry-run smoke above and look for `alert.dry_run` vs
  `alert.delivered` in the log output.

**SMTP authentication failure:**

- For Gmail: ensure "Less secure app access" is disabled and use an app password
  instead of the account password.
- Check `DEMO_ALERT_SMTP_USERNAME` matches the account that generated the app
  password.

**Health check always fails inside Compose:**

- Confirm `DEMO_ALERT_HEALTH_URL=http://demo-api:8000/demo/health` in the cron
  entry (not `localhost:8001` which does not resolve inside a container).
- Ensure `demo-api` is running: `docker compose -f infra/compose/docker-compose.demo.yml ps`.

**`last_status_kind: http_4xx` while the demo is actually up:**

- The probe is being rejected by the recruiter gate. Confirm
  `RECRUITER_USERNAME` and `RECRUITER_PASSWORD` are set in `.env.demo` and that
  the cron entry passes `--env-file .env.demo`, so the one-off container
  inherits them.
- Verify by hand from inside the container: an authenticated
  `GET /demo/health` must return `200 {"status":"ok"}`.
- The failure streak clears on the next successful run; no manual state edit is
  needed.

**State file conflicts:**

- The health state file defaults to `<runtime_root>/state/health_check.json`.
- Dry-run smokes use `DEMO_ALERT_HEALTH_STATE_FILE=/tmp/...` to avoid
  polluting the production state file.
- The persistent state directory is mounted via `x-demo-volumes`; if the mount
  is missing the state file will reset on each container run.

**Log location:**

Cron output goes to:

```
/home/gbibbo/asr_enhancement_runtime/logs/alerts.cron.log
```

Container JSON logs go to the rotating file at:

```
/home/gbibbo/asr_enhancement_runtime/logs/demo.api.log
```
