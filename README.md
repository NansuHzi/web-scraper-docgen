# DocGen - 智能文档生成系统

基于 **CrewAI + FastAPI + Vue 3** 构建的智能网页文档生成系统，支持多源搜索、多智能体协作、RAG 知识库等能力。

[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://vuejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 功能概览

### 🌐 文档生成引擎
- **网页抓取** — 支持知乎、微信公众号、CSDN 等主流站点，Playwright 驱动
- **多源搜索** — 融合 Bing、搜狗、360、百度，保证结果多样性
- **多智能体协作** — CrewAI 架构：研究 → 写作 → 审查，自动产出专业文档
- **RAG 知识库** — ChromaDB 向量存储，支持检索增强生成
- **多格式导出** — Markdown / 纯文本 / PowerPoint
- **增量抓取** — 基于内容哈希的去重机制

### 🔧 爬虫引擎
- **四层引擎架构** — requests + Playwright + Hybrid + Firecrawl（自托管）
- **智能站点检测** — 自动识别站点类型，选择最优爬取策略
- **Firecrawl 集成** — 本地自托管 Firecrawl 集群，支持分布式爬取和反检测
- **自动降级** — Firecrawl 不可用时无缝回退到原生引擎

### 📊 运维管理面板
- **系统监控** — 运行时间、文档统计、任务状态实时展示
- **任务队列** — 异步任务提交与状态追踪
- **定时任务** — Cron 表达式调度，可视化创建与管理
- **热点选题** — 微博热搜 + 知乎热榜聚合，LLM 辅助选题分析

### 🏗️ 工程能力
- **模块化架构** — 核心功能与扩展模块解耦，支持按需加载
- **集中式日志** — `logging` 模块统一管理，按级别分级输出
- **配置中心** — Pydantic Settings 统一配置，`.env` 文件驱动
- **健康检查** — `/health` 存活探针 + `/ready` 就绪探针
- **Docker 部署** — 多阶段构建，一键容器化运行
- **单元测试** — 140+ 用例覆盖核心逻辑（pytest）

---

## 技术栈

| 层 | 技术 |
|---|------|
| **后端框架** | FastAPI + Uvicorn |
| **AI 引擎** | CrewAI (多智能体), LangChain, DeepSeek / 通义千问 |
| **网页抓取** | Playwright (Chromium) + BeautifulSoup4 + Firecrawl (自托管) |
| **向量存储** | ChromaDB + sentence-transformers |
| **数据存储** | SQLite |
| **任务调度** | APScheduler (croniter) |
| **前端框架** | Vue 3 + Vite |
| **样式方案** | Tailwind CSS 3 |
| **容器化** | Docker + docker-compose |

---

## 快速开始

### 环境要求

- Python >= 3.13
- Node.js >= 20.x
- npm >= 10.x
- Docker (可选)

### 1. 克隆项目

```bash
git clone <repo-url>
cd web-scraper-docgen
```

### 2. 后端配置

```bash
# 安装依赖 (推荐使用 uv)
uv sync

# 安装 Playwright 浏览器
playwright install chromium

# 复制环境变量模板
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 3. 前端构建

```bash
cd frontend/vue-project
npm install
npm run build
```

### 4. 启动服务

```bash
# 开发模式：后端 + 前端分别启动
uv run python -m src.main          # 后端 :8000
cd frontend/vue-project && npm run dev   # 前端 :5173

# 或直接启动（前端已构建时）
uv run python -m src.main
```

访问 http://localhost:5173 即可使用。

### 5. Docker 一键部署

```bash
docker compose up -d --build
```

### 6. Firecrawl 本地部署（可选）

如需启用 Firecrawl 爬虫引擎：

```bash
# 启动 Firecrawl 服务
docker compose -f docker-compose.firecrawl.yml up -d

# 在 .env 中启用
FIRECRAWL_ENABLED=true
```

---

## 项目结构

```
web-scraper-docgen/
├── src/
│   ├── api/                      # API 接口层
│   │   ├── scraper.py            # 文档生成 API
│   │   ├── search.py             # 搜索 API
│   │   ├── rag.py                # RAG 知识库 API
│   │   ├── crawler.py            # 通用爬虫 API
│   │   ├── tasks.py              # 任务队列 API
│   │   ├── scheduler.py          # 定时任务 API
│   │   ├── topics.py             # 热点选题 API
│   │   ├── monitor.py            # 系统监控 API
│   │   └── auth.py               # 登录认证 API
│   │
│   ├── adapters/                 # 基础设施适配器
│   │   ├── rag_store.py          # RAG 存储 (ChromaDB)
│   │   ├── document_cache.py     # 文档缓存
│   │   ├── scheduler_manager.py  # 任务调度器
│   │   ├── topic_manager.py      # 热点选题管理
│   │   ├── session_manager.py    # 用户会话管理
│   │   ├── content_filter.py     # 内容安全过滤
│   │   ├── rate_limiter.py       # API 限流
│   │   └── format_adapter.py     # 格式转换
│   │
│   ├── agents/                   # CrewAI 智能体
│   │   ├── researcher.py         # 研究员
│   │   ├── writer.py             # 写作员
│   │   ├── reviewer.py           # 审查员
│   │   ├── scheduler.py          # 调度员
│   │   └── topic_selector.py     # 选题员
│   │
│   ├── crawler/                  # 爬虫引擎
│   │   ├── engine.py             # 核心爬取引擎（四层策略）
│   │   ├── firecrawl_client.py   # Firecrawl 客户端
│   │   ├── batch.py              # 批量爬取
│   │   ├── incremental.py        # 增量抓取
│   │   └── site_detector.py      # 站点类型检测
│   │
│   ├── worker/                   # 异步任务 worker
│   │   ├── dispatcher.py         # 任务分发
│   │   ├── executor.py           # 任务执行器
│   │   ├── store.py              # 任务持久化
│   │   └── models.py             # 任务模型
│   │
│   ├── core/                     # 核心工具
│   │   ├── crew.py               # CrewAI 配置
│   │   ├── llm.py                # LLM 客户端封装
│   │   └── utils.py              # 通用工具
│   │
│   ├── config.py                 # Pydantic 配置中心
│   └── main.py                   # 应用入口（支持模块按需加载）
│
├── frontend/vue-project/         # Vue 3 前端
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   │   ├── HomePage.vue       # URL 抓取主页
│   │   │   ├── SearchPage.vue     # 智能搜索
│   │   │   ├── SchedulerPage.vue  # 定时任务
│   │   │   ├── TopicsPage.vue     # 热点选题
│   │   │   ├── MonitorPage.vue    # 系统监控
│   │   │   ├── CrawlerPage.vue    # 通用爬虫
│   │   │   └── TaskQueuePage.vue  # 任务队列
│   │   ├── services/            # API 服务层
│   │   └── router/              # 路由配置
│   └── ...
│
├── tests/                        # 单元测试 (140+ cases)
├── Dockerfile                    # Docker 构建文件
├── docker-compose.yml            # 编排配置
├── docker-compose.firecrawl.yml  # Firecrawl 编排配置
├── .env.example                  # 环境变量模板
├── pyproject.toml                # Python 项目配置
└── README.md                     # 本文件
```

---

## 配置说明

编辑项目根目录 `.env` 文件：

```env
# ===== LLM 配置 =====
DEEPSEEK_API_KEY=                     # DeepSeek API 密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
QWEN_API_KEY=                         # 通义千问 API 密钥
QWEN_BASE_URL=
USE_LLM=true                          # 是否启用 LLM

# ===== 模型选择 =====
INTENT_LLM_MODEL=deepseek-chat
REPLY_LLM_MODEL=deepseek-chat

# ===== 服务配置 =====
SERVER_PUBLIC_URL=http://127.0.0.1:8000
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173

# ===== Firecrawl 爬虫引擎（可选）=====
FIRECRAWL_ENABLED=false
FIRECRAWL_BASE_URL=http://localhost:3002
FIRECRAWL_API_KEY=fc-local
FIRECRAWL_TIMEOUT=60
FIRECRAWL_FALLBACK=true
```

> 未填写的 API Key 不影响基础功能，对应 LLM 能力会降级为规则匹配。

---

## API 接口一览

### 核心接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/validate` | 验证 URL 和文档类型 |
| POST | `/api/generate` | 生成文档（同步） |
| GET | `/api/document/{id}` | 获取生成的文档 |
| GET | `/api/document/{id}/download` | 下载文档文件 |
| POST | `/api/search` | 多源搜索 |
| POST | `/api/build-rag` | 构建 RAG 知识库 |
| GET | `/api/rag/{id}` | 查询知识库状态 |

### 爬虫接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/crawler/crawl` | 单页面爬取 |
| POST | `/api/crawler/batch` | 批量爬取 |
| GET | `/api/crawler/analyze` | 站点类型分析 |

### 任务 & 调度

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/tasks/submit` | 提交异步任务 |
| GET | `/api/tasks/{id}` | 查询任务状态 |
| GET/POST/PUT/DELETE | `/api/scheduler/jobs` | 定时任务 CRUD |
| POST | `/api/scheduler/jobs/{id}/trigger` | 手动触发任务 |

### 系统

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 存活检查 |
| GET | `/ready` | 就绪检查 |
| GET | `/api/monitor/dashboard` | 系统仪表盘 |

---

## 爬虫引擎架构

```
请求 URL
  │
  ├─ Firecrawl 可用且已启用？
  │    ├─ 是 → Firecrawl /v1/scrape
  │    │       └─ 失败？→ FALLBACK → 回退到原始策略
  │    └─ 否 ↓
  │
  ├─ STATIC   → requests + BeautifulSoup（静态页，最快）
  ├─ JS_RENDER → Playwright 全渲染（SPA 页面）
  └─ HYBRID   → 先 static，失败再 js_render
```

---

## 运行测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 查看覆盖率
python -m pytest tests/ --cov=src --cov-report=term-missing
```

---

## Docker 部署

```bash
# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f app

# 停止服务
docker compose down
```

---

## 安全特性

| 特性 | 实现 |
|------|------|
| **API 限流** | 令牌桶算法，30 次/分钟/IP |
| **CORS 保护** | 可配置允许来源 |
| **内容过滤** | 敏感关键词拦截 |
| **SQL 注入防护** | 参数化查询 + 仅允许 SELECT |
| **会话隔离** | 按 IP/User 隔离用户数据 |

---

## License

[MIT](LICENSE)

---

## 贡献

欢迎 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing`)
5. 提交 Pull Request
