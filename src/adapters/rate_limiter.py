import time
from collections import defaultdict
from typing import Dict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
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
            calls, period = RateLimitConfig.get_limiter(path)
            if not self._check_rate_limit(client_ip, calls, period):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后再试"}
                )

        response = await call_next(request)
        return response

    def _check_rate_limit(self, key: str, calls: int, period: int) -> bool:
        now = time.time()
        self._cleanup(now, period)

        if key not in self.requests:
            self.requests[key] = []

        if len(self.requests[key]) >= calls:
            return False

        self.requests[key].append(now)
        return True

    def _cleanup(self, now: float, period: int):
        cutoff = now - period
        for key in list(self.requests.keys()):
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
            if not self.requests[key]:
                del self.requests[key]


class RateLimitConfig:
    """限流配置 — 按端点差异化"""

    @classmethod
    def get_limiter(cls, endpoint: str):
        if endpoint in ("/api/generate", "/api/scrape"):
            return 5, 60       # 文档生成最耗资源，严格限制
        elif endpoint == "/api/generate-from-rag":
            return 30, 60
        elif endpoint == "/api/build-rag":
            return 30, 60      # RAG构建（仅保存URL，已简化）
        elif endpoint == "/api/search":
            return 10, 60      # 搜索调用外部 API
        elif endpoint == "/api/validate":
            return 30, 60      # 验证轻量
        elif endpoint.startswith("/api/document"):
            return 60, 60      # 查询文档高频但轻量
        elif endpoint.startswith("/api/rag"):
            return 60, 60      # 查询 RAG 状态
        elif endpoint == "/api/history":
            return 30, 60
        return 30, 60          # 默认兜底
