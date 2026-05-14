"""B14.0 recruiter HTTPBasic dependency.

Implements a request-time fail-closed HTTP Basic gate for the six recruiter-
protected /demo/* routes declared in docs/plans/b14_0/agent_plan.md section 2.

Contract summary (state_packet_schemas.yaml recruiter_auth_invariant_record):
  * realm: "asr-demo-recruiter"
  * 401 challenge for any request without valid Basic credentials, including
    when RECRUITER_USERNAME or RECRUITER_PASSWORD is unset or empty
  * empty response body on every challenge
  * constant-time credential comparison via ``secrets.compare_digest``
  * FastAPI app import succeeds regardless of recruiter env state — only
    request handling is gated

The misconfigured-env path returns the same 401 + WWW-Authenticate value as
the unauthenticated path so an external observer cannot distinguish a
misconfigured server from a normal challenge. Server-side, a single
structured log line per process per missing-field-set records the condition
without echoing credential values.
"""
from __future__ import annotations

import base64
import logging
import os
import secrets
import threading
from typing import Optional

from fastapi import Request
from fastapi.responses import Response

RECRUITER_REALM = "asr-demo-recruiter"
RECRUITER_WWW_AUTHENTICATE = f'Basic realm="{RECRUITER_REALM}"'
RECRUITER_USERNAME_ENV = "RECRUITER_USERNAME"
RECRUITER_PASSWORD_ENV = "RECRUITER_PASSWORD"

_logger = logging.getLogger("demo-api.recruiter-auth")
_misconfig_lock = threading.Lock()
_misconfig_logged: set[frozenset[str]] = set()


class RecruiterAuthChallenge(Exception):
    """Raised by the recruiter dependency to request a 401 challenge response.

    A FastAPI exception handler maps this to a Response with status 401, the
    canonical recruiter ``WWW-Authenticate`` header, and an empty body.
    """


def _log_misconfig_once(missing: list[str]) -> None:
    key = frozenset(missing)
    with _misconfig_lock:
        if key in _misconfig_logged:
            return
        _misconfig_logged.add(key)
    _logger.warning(
        "recruiter_auth_env_missing",
        extra={"event": "recruiter_auth_env_missing", "missing": sorted(missing)},
    )


def _reset_misconfig_log_state() -> None:
    """Test-only helper to clear the once-per-process log flag."""
    with _misconfig_lock:
        _misconfig_logged.clear()


def _read_env_credentials() -> Optional[tuple[bytes, bytes]]:
    username = os.environ.get(RECRUITER_USERNAME_ENV, "")
    password = os.environ.get(RECRUITER_PASSWORD_ENV, "")
    missing: list[str] = []
    if not username:
        missing.append(RECRUITER_USERNAME_ENV)
    if not password:
        missing.append(RECRUITER_PASSWORD_ENV)
    if missing:
        _log_misconfig_once(missing)
        return None
    return username.encode("utf-8"), password.encode("utf-8")


def _decode_basic_header(header: Optional[str]) -> Optional[tuple[bytes, bytes]]:
    if not header:
        return None
    parts = header.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, encoded = parts
    if scheme.lower() != "basic":
        return None
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        return None
    if b":" not in raw:
        return None
    user, _, pw = raw.partition(b":")
    return user, pw


async def recruiter_auth_dependency(request: Request) -> None:
    """FastAPI dependency: enforce recruiter HTTPBasic at request time."""
    expected = _read_env_credentials()
    if expected is None:
        raise RecruiterAuthChallenge()
    supplied = _decode_basic_header(request.headers.get("authorization"))
    if supplied is None:
        raise RecruiterAuthChallenge()
    ok_user = secrets.compare_digest(supplied[0], expected[0])
    ok_pass = secrets.compare_digest(supplied[1], expected[1])
    if not (ok_user and ok_pass):
        raise RecruiterAuthChallenge()


async def recruiter_challenge_handler(request: Request, exc: Exception) -> Response:
    """Exception handler: empty 401 with canonical recruiter realm header."""
    return Response(
        status_code=401,
        content=b"",
        headers={"WWW-Authenticate": RECRUITER_WWW_AUTHENTICATE},
    )
