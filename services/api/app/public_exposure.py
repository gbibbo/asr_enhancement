"""
B14.1 public-exposure flag accessor.

Single-purpose, read-only helper that exposes the PUBLIC_DEMO_EXPOSURE
environment flag to application code as a boolean. The default value is
False (loopback-only operation). This module performs no FastAPI hook
installation, no router mutation, no authority decision: callers that
later consume the flag MUST NOT key any application-layer authority
decision on it (the recruiter HTTPBasic gate remains the sole authority
for public /demo/* access under B14.0).

No credential, hostname, token, or auth-key value is ever read or logged
by this module.
"""
from __future__ import annotations

import os

PUBLIC_DEMO_EXPOSURE_ENV = "PUBLIC_DEMO_EXPOSURE"
_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"", "0", "false", "no", "off"})


def get_public_demo_exposure_flag() -> bool:
    """Return the PUBLIC_DEMO_EXPOSURE flag as a boolean.

    Default is False when the environment variable is unset or empty.
    Any value outside the recognised truthy/falsy sets is treated as
    False so that misconfiguration cannot accidentally promote the
    runtime to public exposure.
    """
    raw = os.environ.get(PUBLIC_DEMO_EXPOSURE_ENV, "")
    normalised = raw.strip().lower()
    if normalised in _TRUTHY:
        return True
    return False
