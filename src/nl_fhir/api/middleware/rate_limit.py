"""Simple in-process rate limiting middleware."""

from __future__ import annotations

import asyncio
from collections import deque
from time import monotonic
from typing import Deque, Dict

from fastapi import Request, status
from fastapi.responses import JSONResponse

from ...config import settings


class _RateLimitState:
    """Track request timestamps for a given client key."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = float(window_seconds)
        self._requests: Dict[str, Deque[float]] = {}
        self._lock = asyncio.Lock()

    async def register(self, key: str) -> tuple[bool, float | None]:
        """Register a request and determine if it exceeds the quota."""

        async with self._lock:
            now = monotonic()
            window_start = now - self.window_seconds
            entries = self._requests.setdefault(key, deque())

            while entries and entries[0] < window_start:
                entries.popleft()

            if len(entries) >= self.max_requests:
                retry_after = max(entries[0] + self.window_seconds - now, 0.0)
                return False, retry_after

            entries.append(now)
            return True, None


_rate_limit_state = _RateLimitState(
    settings.rate_limit_requests_per_minute,
    settings.rate_limit_window_seconds,
)


async def rate_limit_middleware(request: Request, call_next):
    """Reject requests that exceed the configured rate limit."""

    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else "anonymous"

    allowed, retry_after = await _rate_limit_state.register(client_ip)
    if not allowed:
        headers = {"Retry-After": f"{int(retry_after or 0)}"}
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Too many requests. Please retry later.",
                "client": client_ip,
            },
            headers=headers,
        )

    return await call_next(request)
