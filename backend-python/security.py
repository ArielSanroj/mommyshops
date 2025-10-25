"""
Security utilities for the MommyShops backend.
"""

from __future__ import annotations

import os
import re
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class SensitiveDataFilter:
    """
    Logging filter that masks common sensitive tokens so they are not persisted.
    """

    _PATTERN = re.compile(r"(?i)(authorization|api[_-]?key|token)(\s*[:=]\s*)([^\s,;]+)")

    def filter(self, record) -> bool:  # pragma: no cover - minimal logic
        message = record.getMessage()
        cleaned = self._PATTERN.sub(r"\1\2<redacted>", message)
        if cleaned != message:
            record.msg = cleaned
            record.args = ()
        return True


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Very lightweight, in-memory rate limiter to avoid DoS/DDoS on public endpoints.
    The defaults can be tuned through RATE_LIMIT_PER_MINUTE and RATE_LIMIT_WINDOW env vars.
    """

    def __init__(self, app, limit: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.limit = max(1, limit)
        self.window = max(1, window_seconds)
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        client_id = self._resolve_client_id(request)
        now = time.time()
        bucket = self._requests[client_id]

        while bucket and now - bucket[0] > self.window:
            bucket.popleft()

        if len(bucket) >= self.limit:
            retry_after = max(1, int(self.window - (now - bucket[0])))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit excedido. Intenta nuevamente en unos segundos.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)
        return await call_next(request)

    def _resolve_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host or "unknown"
        return "unknown"


def configure_security(app) -> None:
    """
    Attach middleware and logging filters defined in this module.
    """

    minute_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "90"))
    window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    app.add_middleware(
        RateLimiterMiddleware,
        limit=minute_limit,
        window_seconds=window_seconds,
    )

    sensitive_filter = SensitiveDataFilter()
    root_logger = __import__("logging").getLogger()
    root_logger.addFilter(sensitive_filter)
