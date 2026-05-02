from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 20, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    def _cleanup(self, bucket: deque[float], now: float) -> None:
        threshold = now - self.window_seconds
        while bucket and bucket[0] < threshold:
            bucket.popleft()

    def _client_id(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next):
        if request.url.path != "/analyze" or request.method.upper() != "POST":
            return await call_next(request)

        now = time.time()
        client_id = self._client_id(request)
        bucket = self.requests[client_id]
        self._cleanup(bucket, now)
        if len(bucket) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        bucket.append(now)
        return await call_next(request)
