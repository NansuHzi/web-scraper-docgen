import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter(BaseHTTPMiddleware):
    """简单的内存限流中间件"""

    def __init__(self, app, calls: int = 10, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        if path.startswith("/api/"):
            if not self._check_rate_limit(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail="请求过于频繁，请稍后再试"
                )

        response = await call_next(request)
        return response

    def _check_rate_limit(self, key: str) -> bool:
        now = time.time()
        self._cleanup(now)

        if key not in self.requests:
            self.requests[key] = []

        if len(self.requests[key]) >= self.calls:
            return False

        self.requests[key].append(now)
        return True

    def _cleanup(self, now: float):
        cutoff = now - self.period
        for key in list(self.requests.keys()):
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
            if not self.requests[key]:
                del self.requests[key]


class RateLimitConfig:
    """限流配置"""

    GENERATE_RATE = 5
    GENERATE_PERIOD = 60

    VALIDATE_RATE = 30
    VALIDATE_PERIOD = 60

    DOCUMENT_RATE = 60
    DOCUMENT_PERIOD = 60

    @classmethod
    def get_limiter(cls, endpoint: str):
        if endpoint == "/api/generate":
            return cls.GENERATE_RATE, cls.GENERATE_PERIOD
        elif endpoint == "/api/validate":
            return cls.VALIDATE_RATE, cls.VALIDATE_PERIOD
        elif endpoint.startswith("/api/document"):
            return cls.DOCUMENT_RATE, cls.DOCUMENT_PERIOD
        return 100, 60


def create_rate_limit_middleware(app, calls: int = 10, period: int = 60):
    return RateLimiter(app, calls=calls, period=period)