from fastapi import FastAPI
from .api.scraper import router as scraper_router
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

app = FastAPI(
    title="网页信息抓取与文档生成系统",
    description="基于CrewAI和FastAPI构建的智能文档生成服务",
    version="1.0.0"
)

# 注册路由
app.include_router(scraper_router, prefix="/api", tags=["scraper"])

@app.get("/")
async def root():
    return {
        "message": "欢迎使用网页信息抓取与文档生成系统",
        "endpoints": [
            {"path": "/api/scrape", "method": "POST", "description": "提交网页URL生成文档"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)