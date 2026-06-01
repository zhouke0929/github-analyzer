# GitHub 项目智能分析

> AI 驱动的 GitHub 项目分析工具，帮助中国开发者快速理解和评估开源项目。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 功能特性

### 项目分析
- **README 中文翻译** - 智能翻译，保留 Markdown 格式和代码块
- **项目摘要生成** - 一句话概括项目核心价值
- **技术栈识别** - 自动识别语言、框架、工具
- **架构分析** - 目录结构、模块划分、设计模式
- **Issues 趋势** - 标签分布、月度趋势、关闭率统计

### 智能问答
- **代码语义检索** - 基于 RAG 的代码理解，支持自然语言提问
- **精确代码搜索** - GitHub API 直接搜索，带行号定位
- **对话历史** - 支持多轮对话，上下文理解
- **索引进度** - 实时显示代码索引状态

### 系统管理
- **配置管理** - 支持多种 AI 提供商（OpenAI、通义千问、DeepSeek 等）
- **存储管理** - 数据大小查看、历史数据清理
- **热更新** - 配置修改后立即生效

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│         React 19 + Tailwind CSS + shadcn/ui             │
└─────────────────────────┬───────────────────────────────┘
                          │ API
┌─────────────────────────▼───────────────────────────────┐
│                   Backend (FastAPI)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ 分析引擎 │  │ Agent    │  │ RAG      │  │ 配置    │ │
│  │          │  │ (LangGraph)│ │ (LangChain)│ │ 管理    │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────┬───────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐    ┌──────▼──────┐   ┌─────▼─────┐
    │ SQLite  │    │  ChromaDB   │   │ GitHub API│
    │ 数据库  │    │  向量数据库  │   │           │
    └─────────┘    └─────────────┘   └───────────┘
```

**技术栈：**
- 前端：Next.js 16、React 19、Tailwind CSS、shadcn/ui
- 后端：FastAPI、SQLite、ChromaDB
- AI：LangChain、LangGraph、DashScope Embedding
- 部署：Docker、docker-compose

## 快速开始

### Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/zhouke0929/github-analyzer.git
cd github-analyzer

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 API Key

# 3. 启动服务
docker-compose up -d

# 4. 访问应用
# 前端：http://localhost:3000
# 后端：http://localhost:8001
```

### 手动部署

**环境要求：** Python 3.11+、Node.js 20+

```bash
# 1. 克隆项目
git clone https://github.com/zhouke0929/github-analyzer.git
cd github-analyzer

# 2. 后端
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 API Key
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 3. 前端（新终端）
cd frontend
npm install
npm run dev
```

## 环境变量配置

在 `backend/.env` 中配置：

```env
# GitHub Token（可选，提高 API 限额）
GITHUB_TOKEN=your_github_token

# AI 模型配置（必填，兼容 OpenAI 接口）
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Embedding 模型配置（用于代码语义检索）
EMBEDDING_API_KEY=your_embedding_key
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v4
```

> 所有兼容 OpenAI 接口的 AI 服务均可使用，只需修改 `OPENAI_BASE_URL` 和模型名称即可。

## 使用说明

1. **分析项目**：在首页输入 GitHub 仓库地址，点击分析
2. **查看结果**：查看翻译、摘要、技术栈、架构、Issues 分析
3. **智能问答**：点击"开始对话"，等待代码索引完成，即可提问
4. **系统设置**：在设置页面配置 API Key、模型、存储管理

## 项目结构

```
github-analyzer/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── services/       # 业务服务
│   │   ├── models/         # 数据模型
│   │   └── config.py       # 配置管理
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── app/            # 页面
│   │   ├── components/     # 组件
│   │   └── lib/            # 工具库
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 许可证

MIT License

## 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - AI 应用框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent 编排框架
- [ChromaDB](https://github.com/chroma-core/chroma) - 向量数据库
- [shadcn/ui](https://github.com/shadcn-ui/ui) - UI 组件库
