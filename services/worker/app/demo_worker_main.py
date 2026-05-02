from __future__ import annotations

import logging
import signal
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger("demo-worker")

_shutdown = False


def _handle_signal(signum: int, frame: object) -> None:
    global _shutdown
    log.info("Demo worker received signal %d, shutting down", signum)
    _shutdown = True


def main() -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    log.info("Demo worker started (idle, waiting for B3.2 job queue)")
    while not _shutdown:
        time.sleep(1)
    log.info("Demo worker stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
