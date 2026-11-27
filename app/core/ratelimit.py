
"""Simple in-memory rate limiter for public endpoints.

NOTE: per-process memory only — fine for a single dev instance.
Replace with Redis when running multiple workers (Phase 11).
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

_hits: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(request: Request, limit: int = 30, window_seconds: int = 60):
    """Allow `limit` requests per client IP per `window_seconds`."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    hits = _hits[client_ip]

    # Drop timestamps older than the window.
    while hits and now - hits[0] > window_seconds:
        hits.popleft()

    if len(hits) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down.",
        )

    hits.append(now)
