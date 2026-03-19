"""Captures Python log records and streams them to the frontend via SSE."""

import asyncio
import json
import logging
import queue
import time
from collections import deque
from typing import AsyncGenerator

# Thread-safe queue for log records produced by any thread.
_log_queue: queue.Queue[dict] = queue.Queue(maxsize=2000)

# Keep last N entries so a newly-connected client gets recent context.
_recent: deque[dict] = deque(maxlen=50)

_LEVEL_MAP = {
    "DEBUG": "debug",
    "INFO": "info",
    "WARNING": "warn",
    "ERROR": "error",
    "CRITICAL": "error",
}


class _BroadcastHandler(logging.Handler):
    """Logging handler that serialises records into the shared queue."""

    def emit(self, record: logging.LogRecord) -> None:
        entry = {
            "ts": time.strftime("%H:%M:%S", time.localtime(record.created)),
            "level": _LEVEL_MAP.get(record.levelname, "info"),
            "name": record.name,
            "message": self.format(record),
        }
        _recent.append(entry)
        try:
            _log_queue.put_nowait(entry)
        except queue.Full:
            pass  # drop oldest if consumer is too slow


def install_log_handler() -> None:
    """Attach the broadcast handler to the root logger."""
    handler = _BroadcastHandler()
    handler.setFormatter(logging.Formatter("%(name)s  %(message)s"))
    logging.getLogger().addHandler(handler)


async def log_event_generator() -> AsyncGenerator[str, None]:
    """Async generator that yields SSE-formatted log events."""
    # Send recent backlog first so the client sees context immediately.
    for entry in list(_recent):
        yield f"data: {json.dumps(entry)}\n\n"

    while True:
        try:
            entry = _log_queue.get_nowait()
            yield f"data: {json.dumps(entry)}\n\n"
        except queue.Empty:
            # Heartbeat comment keeps the connection alive.
            yield ": heartbeat\n\n"
            await asyncio.sleep(0.4)
