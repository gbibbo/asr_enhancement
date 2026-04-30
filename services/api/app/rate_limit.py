from __future__ import annotations

import asyncio
import math
import time

# Per-process counter; for the demo's single-replica API container this is
# sufficient. Do not add Redis, slowapi, or any new dependency.

_WINDOW_SECONDS = 60.0


class RateLimiter:
    def __init__(self, per_minute: int) -> None:
        self._per_minute = int(per_minute)
        # Created lazily inside is_allowed so that constructing a RateLimiter
        # outside an asyncio event loop (e.g. test fixture setup on Python 3.9)
        # does not raise.
        self._lock: asyncio.Lock | None = None
        self._buckets: dict[str, tuple[int, float]] = {}

    async def is_allowed(self, client_key: str) -> tuple[bool, int]:
        if self._per_minute <= 0:
            return True, 0

        if self._lock is None:
            self._lock = asyncio.Lock()

        async with self._lock:
            now = time.monotonic()
            entry = self._buckets.get(client_key)
            if entry is None or (now - entry[1]) >= _WINDOW_SECONDS:
                self._buckets[client_key] = (1, now)
                return True, 0

            count, window_start = entry
            new_count = count + 1
            if new_count > self._per_minute:
                retry_after = max(1, math.ceil(window_start + _WINDOW_SECONDS - now))
                return False, int(retry_after)

            self._buckets[client_key] = (new_count, window_start)
            return True, 0

    def reset(self) -> None:
        self._buckets.clear()
