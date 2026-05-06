# DocGen - 智能文档生成器

基于 CrewAI 和 Vue3 构建的网页信息抓取与文档生成系统。

## 功能特性

- 🌐 **网页抓取**: 支持从任意URL抓取内容（知乎、微信公众号、CSDN等）
- 🔍 **多源搜索**: 融合 Bing、搜狗、360、百度等多个搜索引擎，保证结果多样性
- 🤖 **智能生成**: 基于多智能体架构自动生成专业文档
- � **RAG支持**: 支持构建本地知识库进行检索增强生成
- �📄 **多格式导出**: 支持 Markdown、纯文本、PPT 格式
- 📊 **实时预览**: Markdown 原文与渲染预览切换
- 🕐 **历史记录**: 按用户隔离的文档生成历史
- ⚡ **缓存优化**: 支持文档缓存，提升响应速度
- 🔒 **安全防护**: CORS配置、API限流、内容过滤

## 技术栈

### 后端
- Python 3.13+
- FastAPI
- CrewAI
- Playwright
- ChromaDB (RAG)
- python-pptx (PPT导出)

### 前端
- Vue 3
- Tailwind CSS 3
- Vite
- marked (Markdown渲染)

## 快速开始

### 环境要求

- Python >= 3.13
- Node.js >= 20.x
- npm >= 10.x
- Playwright 浏览器 (用于网页抓取)

### 后端安装

```bash
# 进入项目目录
cd web-scraper-docgen

# 安装依赖 (使用 uv 推荐)
uv sync

# 安装 Playwright 浏览器
playwright install chromium

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入您的 API Key
# 支持: 通义千问、DeepSeek、智谱GLM
```

### 前端安装

```bash
cd frontend/vue-project
npm install
```

### 运行项目

```bash
# 启动后端服务 (端口 8000)
uv run python -m src.main

# 启动前端开发服务器 (端口 5173)
cd frontend/vue-project
npm run dev
```

### 生产构建

```bash
# 构建前端
cd frontend/vue-project
npm run build

# 后端部署
uv run python -m src.main --host 0.0.0.0 --port 8000 --workers 4
```

## API 接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/validate` | POST | 验证URL和文档类型 |
| `/api/generate` | POST | 生成文档 |
| `/api/generate-from-rag` | POST | 基于RAG生成文档 |
| `/api/build-rag` | POST | 构建RAG知识库 |
| `/api/search` | POST | 网页搜索 |
| `/api/document/{id}` | GET | 获取文档 |
| `/api/history` | GET | 获取历史记录 |

## 使用示例

```bash
# 验证URL
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "doc_type": "tech_doc"}'

# 生成文档
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "doc_type": "tech_doc", "format": "md"}'

# 获取文档
curl http://localhost:8000/api/document/doc_1234567890
```

## 项目结构

```
web-scraper-docgen/
├── src/                    # 后端源码
│   ├── adapters/           # 适配器模块
│   │   ├── content_filter.py   # 内容安全过滤
│   │   ├── document_cache.py   # 文档缓存
│   │   ├── format_adapter.py   # 格式转换
│   │   ├── rate_limiter.py     # API限流
│   │   ├── session_manager.py  # 会话管理
│   │   └── rag_store.py        # RAG存储
│   ├── agents/             # 智能体定义
│   │   ├── researcher.py       # 研究智能体
│   │   ├── writer.py           # 写作智能体
│   │   └── reviewer.py         # 审查智能体
│   ├── api/                # API接口
│   │   ├── scraper.py          # 文档生成API
│   │   ├── search.py           # 搜索API
│   │   └── rag.py              # RAG API
│   ├── core/               # 核心模块
│   │   ├── crew.py             # CrewAI配置
│   │   ├── llm.py              # LLM配置
│   │   └── utils.py            # 工具函数
│   └── main.py             # 应用入口
├── frontend/               # 前端代码
│   └── vue-project/        # Vue项目
├── output/                 # 生成的文档输出
├── .browser_state/         # 浏览器状态文件
├── .env.example            # 环境变量模板
├── .gitignore              # Git忽略配置
├── pyproject.toml          # Python项目配置
└── README.md               # 项目说明
```

## 配置说明

### 环境变量 (.env)

```env
# 阿里云通义千问
QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 智谱GLM
ANTHROPIC_AUTH_API=your_glm_api_key_here
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# CORS配置（可选）
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 文档类型支持

| 类型 | 描述 |
|------|------|
| `tech_doc` | 技术文档 |
| `api_doc` | API文档 |
| `readme` | README文档 |
| `summary` | 摘要总结 |

## 导出格式

| 格式 | 扩展名 | 描述 |
|------|--------|------|
| `md` | .md | Markdown格式 |
| `txt` | .txt | 纯文本格式 |
| `ppt` | .pptx | PowerPoint格式 |

## 安全特性

- **用户隔离**: 基于IP的会话管理，确保数据隔离
- **内容过滤**: 敏感内容检测和拦截
- **API限流**: 每分钟最多30次请求
- **CORS保护**: 限制允许的来源域名

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过 Issue 联系。
