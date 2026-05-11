from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .api.scraper import router as scraper_router
from .api.search import router as search_router
from .api.rag import router as rag_router
from .api.auth import router as auth_router
from .api.scheduler import router as scheduler_router
from .api.topics import router as topics_router
from .api.monitor import router as monitor_router
from .api.crawler import router as crawler_router
from .api.tasks import router as tasks_router
from .adapters.rate_limiter import RateLimiter
import logging
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)

HAS_BOT_MODULE = False
HAS_DATABASE_API = False

try:
    from .bot.log import setup_logging, get_logger
    HAS_BOT_MODULE = True
except ImportError:
    def setup_logging(level="INFO"):
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def get_logger(name):
        return logging.getLogger(name)

try:
    from .api.xianyu import router as xianyu_router
    HAS_BOT_MODULE = True
except ImportError:
    xianyu_router = None

try:
    from .api.database import router as database_router
    HAS_DATABASE_API = True
except ImportError:
    database_router = None

setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)

def get_allowed_origins() -> list:
    if settings.CORS_ORIGINS:
        return [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

app = FastAPI(
    title="DocGen - 智能文档生成系统",
    description="基于 CrewAI 和 FastAPI 构建的智能文档生成服务",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_middleware(RateLimiter, calls=30, period=60)

app.include_router(scraper_router, prefix="/api", tags=["scraper"])
app.include_router(search_router, prefix="/api", tags=["search"])
app.include_router(rag_router, prefix="/api", tags=["rag"])
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(scheduler_router, prefix="/api", tags=["scheduler"])
app.include_router(topics_router, prefix="/api", tags=["topics"])
app.include_router(monitor_router, prefix="/api", tags=["monitor"])
app.include_router(crawler_router, prefix="/api", tags=["crawler"])
app.include_router(tasks_router, prefix="/api", tags=["tasks"])

if xianyu_router is not None:
    app.include_router(xianyu_router, prefix="/api", tags=["xianyu"])
    logger.info("闲鱼客服模块已加载")
else:
    logger.info("闲鱼客服模块未安装，跳过加载")

if database_router is not None:
    app.include_router(database_router, prefix="/api", tags=["database"])
    logger.info("数据库管理模块已加载")
else:
    logger.info("数据库管理模块未安装，跳过加载")


@app.get("/health")
async def health_check():
    return {"status": "ok", "modules": {"bot": HAS_BOT_MODULE, "database_api": HAS_DATABASE_API}}


@app.get("/ready")
async def readiness_check():
    checks = {"status": "ok", "checks": {}}
    try:
        from .adapters.scheduler_manager import scheduler_manager
        checks["checks"]["scheduler"] = "ok" if scheduler_manager._running else "not_running"
    except Exception as e:
        checks["checks"]["scheduler"] = f"error: {e}"
        checks["status"] = "degraded"

    if HAS_BOT_MODULE:
        try:
            from .bot.database import db
            db_conn = db._conn
            checks["checks"]["database"] = "ok" if db_conn else "not_connected"
        except Exception as e:
            checks["checks"]["database"] = f"error: {e}"
            checks["status"] = "degraded"

    return checks


@app.on_event("startup")
async def startup_event():
    from .adapters.rag_store import rag_store
    rag_store.start_cleanup()
    from .adapters.scheduler_manager import scheduler_manager
    import asyncio
    scheduler_manager.set_event_loop(asyncio.get_running_loop())
    scheduler_manager.start()

    from .worker.executor import register_default_handlers
    register_default_handlers()

    from .worker.dispatcher import task_dispatcher
    await task_dispatcher.start()

    if HAS_BOT_MODULE:
        try:
            from .bot.reply import reply_engine
            from .bot.llm_reply import llm_reply_engine
            from .bot.poller import get_poller
            from .bot.session import session_manager
            from .bot.database import db

            use_llm = settings.USE_LLM
            active_reply_engine = llm_reply_engine if use_llm else reply_engine

            session_manager.restore_from_db()
            logger.info("已从数据库恢复会话状态")

            async def on_task_complete(task):
                if task.user_id:
                    poller = get_poller()
                    gateway = poller._gateway
                    if gateway is None:
                        try:
                            from .api.xianyu import get_gateway
                            gateway = get_gateway()
                        except ImportError:
                            pass
                    if task.status.value == "completed":
                        reply = active_reply_engine.task_completed_reply(
                            task.user_id, task.id, task.result or {}
                        )

                        session = session_manager.get(task.user_id)
                        if session:
                            order_id = session.context.get("_order_id")
                            if order_id:
                                order = db.get_order(order_id)
                                if order and order["payment_status"] == "paid":
                                    all_done = True
                                    for tid in order.get("task_ids", []):
                                        from .worker.store import task_store as ts
                                        t = ts.get(tid)
                                        if t and t.status.value not in ("completed", "failed", "cancelled"):
                                            all_done = False
                                            break
                                    if all_done:
                                        db.update_order_payment(order_id, "delivered")
                                        logger.info("订单 %s 已交付", order_id)
                    else:
                        reply = active_reply_engine.task_failed_reply(
                            task.user_id, task.id, task.error_message or "未知错误"
                        )
                    try:
                        await gateway.send_reply(reply)
                    except Exception as e:
                        logger.error("发送任务完成通知失败: %s", e)

            task_dispatcher.on_task_complete(on_task_complete)
            logger.info("闲鱼客服回调已注册")
        except Exception as e:
            logger.warning("闲鱼客服模块初始化失败（不影响核心功能）: %s", e)
    else:
        logger.info("闲鱼客服模块未安装，任务完成通知功能不可用")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path

    logger.info("请求开始 | IP: %s | 方法: %s | 路径: %s", client_ip, method, path)

    try:
        response = await call_next(request)
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("请求完成 | IP: %s | 方法: %s | 路径: %s | 状态: %s | 耗时: %.3fs", client_ip, method, path, response.status_code, duration)
        return response
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error("请求异常 | IP: %s | 方法: %s | 路径: %s | 错误: %s | 耗时: %.3fs", client_ip, method, path, str(e), duration)
        raise


@app.get("/")
async def root():
    endpoints = [
        {"path": "/api/validate", "method": "POST", "description": "验证URL和文档类型"},
        {"path": "/api/generate", "method": "POST", "description": "生成文档"},
        {"path": "/api/document/{document_id}", "method": "GET", "description": "获取生成的文档"},
        {"path": "/api/scrape", "method": "POST", "description": "提交网页URL生成文档"},
        {"path": "/api/search", "method": "POST", "description": "搜索相关网站"},
        {"path": "/api/build-rag", "method": "POST", "description": "构建RAG知识库"},
        {"path": "/api/rag/{rag_id}", "method": "GET", "description": "获取知识库构建状态"},
        {"path": "/api/crawler/crawl", "method": "POST", "description": "通用网页爬取"},
        {"path": "/api/crawler/batch", "method": "POST", "description": "批量网页爬取"},
        {"path": "/api/crawler/analyze", "method": "GET", "description": "站点类型分析"},
        {"path": "/api/tasks/submit", "method": "POST", "description": "提交异步任务"},
        {"path": "/api/tasks/{task_id}", "method": "GET", "description": "查询任务状态"},
    ]

    if HAS_BOT_MODULE:
        endpoints.extend([
            {"path": "/api/xianyu/webhook", "method": "POST", "description": "闲鱼消息Webhook"},
            {"path": "/api/xianyu/gateway/start", "method": "POST", "description": "启动网关"},
            {"path": "/api/xianyu/gateway/stop", "method": "POST", "description": "停止网关"},
            {"path": "/api/xianyu/gateway/status", "method": "GET", "description": "网关状态"},
        ])

    return {
        "message": "欢迎使用 DocGen 智能文档生成系统",
        "endpoints": endpoints,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
