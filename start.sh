#!/bin/bash

echo "================================================"
echo "         Web Scraper DocGen 一键启动"
echo "================================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
PROJECT_DIR="$SCRIPT_DIR"

echo "[1/3] 检查 Python 环境..."
if ! command -v python3 &>/dev/null; then
    echo "ERROR: 未找到 Python3，请安装 Python 3.13+"
    exit 1
fi

echo "[2/3] 检查 Node.js 环境..."
if ! command -v node &>/dev/null; then
    echo "ERROR: 未找到 Node.js，请安装 Node.js 18+"
    exit 1
fi

echo ""
echo "[3/3] 启动服务..."
echo ""

# 创建日志目录
mkdir -p logs

# 启动后端服务
echo "启动后端服务..."
cd "$PROJECT_DIR"
pip install -e . >/dev/null 2>&1
nohup uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 启动前端服务
echo "启动前端服务..."
cd "$PROJECT_DIR/frontend/vue-project"
npm install >/dev/null 2>&1
nohup npm run dev > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务 PID: $FRONTEND_PID"

echo ""
echo "服务启动完成！"
echo ""
echo "前端页面: http://localhost:5173"
echo "后端 API: http://localhost:8000"
echo ""
echo "日志文件:"
echo "  - 后端: logs/backend.log"
echo "  - 前端: logs/frontend.log"
echo ""
echo "停止服务命令:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""

# 保存 PID 到文件
echo "$BACKEND_PID" > logs/backend.pid
echo "$FRONTEND_PID" > logs/frontend.pid