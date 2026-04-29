from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .api.scraper import router as scraper_router
from .adapters.rate_limiter import RateLimiter
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_allowed_origins() -> list:
    env_origins = os.getenv("CORS_ORIGINS", "")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

app = FastAPI(
    title="网页信息抓取与文档生成系统",
    description="基于CrewAI和FastAPI构建的智能文档生成服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_middleware(RateLimiter, calls=30, period=60)

app.include_router(scraper_router, prefix="/api", tags=["scraper"])

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    
    logger.info(f"请求开始 | IP: {client_ip} | 方法: {method} | 路径: {path}")
    
    try:
        response = await call_next(request)
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"请求完成 | IP: {client_ip} | 方法: {method} | 路径: {path} | 状态: {response.status_code} | 耗时: {duration:.3f}s")
        return response
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"请求异常 | IP: {client_ip} | 方法: {method} | 路径: {path} | 错误: {str(e)} | 耗时: {duration:.3f}s")
        raise

@app.get("/")
async def root():
    return {
        "message": "欢迎使用网页信息抓取与文档生成系统",
        "endpoints": [
            {"path": "/api/validate", "method": "POST", "description": "验证URL和文档类型"},
            {"path": "/api/generate", "method": "POST", "description": "生成文档"},
            {"path": "/api/document/{document_id}", "method": "GET", "description": "获取生成的文档"},
            {"path": "/api/scrape", "method": "POST", "description": "提交网页URL生成文档（Legacy）"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
