# GitHub 项目智能分析

AI 驱动的 Web 应用，帮助中国开发者快速理解和评估 GitHub 项目。

## 功能特性

### P0 核心功能
- **README 中文翻译** - 保留 Markdown 格式的中文翻译，支持 HTML 标签渲染
- **项目一句话摘要** - 用 15-30 个汉字概括项目核心价值
- **技术栈分析** - 识别语言分布、框架和工具
- **架构分析** - 项目目录结构、模块划分、设计模式
- **Issues 趋势分析** - 标签分布、月度趋势、关闭率
- **报告导出** - 支持导出分析报告

### P1 项目管理
- **项目列表** - 已分析项目的搜索、筛选、排序
- **项目详情** - 查看完整分析结果
- **重新分析** - 更新项目分析数据
- **删除项目** - 清理不需要的分析记录

### P2 Agent 智能问答
- **LangGraph StateGraph 编排** - 显式意图路由
- **GitHub API 精确代码搜索** - 带行号提取
- **ChromaDB RAG 语义检索** - DashScope text-embedding-v4
- **AST 代码分块** - Python 文件按函数/类边界
- **后台异步代码索引** - 最多 50 个文件，支持 .md 文档
- **索引进度可视化** - 实时显示索引状态
- **对话历史持久化** - localStorage + 数据库
- **停止生成按钮** - AbortController

### P3 系统设置
- **配置管理** - GitHub Token、聊天模型、向量模型配置
- **存储管理** - 数据大小查看、旧数据清理
- **热更新** - 配置修改后立即生效，无需重启
- **Docker 部署** - Dockerfile + docker-compose.yml

## 技术栈

- **前端**: Next.js 16 + React 19 + Tailwind CSS + shadcn/ui
- **后端**: FastAPI + SQLite + ChromaDB
- **AI**: LangGraph + DashScope Embedding + 多模型支持

## 项目结构

```
GitHub项目智能分析/
├── README.md
├── docker-compose.yml
├── backend/
│   ├── .dockerignore
│   ├── .env
│   ├── .env.example
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── analyze.py
│   │   │   ├── config.py
│   │   │   ├── health.py
│   │   │   ├── projects.py
│   │   │   └── qa.py
│   │   ├── models/
│   │   │   ├── database.py
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── agent_service.py
│   │   │   ├── ai_service.py
│   │   │   ├── architecture_service.py
│   │   │   ├── github_service.py
│   │   │   ├── issues_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── summary_service.py
│   │   │   ├── tech_stack_service.py
│   │   │   └── translate_service.py
│   │   └── utils/
│   └── data/
└── frontend/
    ├── .dockerignore
    ├── .env.local
    ├── Dockerfile
    ├── next.config.ts
    ├── package.json
    └── src/
        ├── app/
        │   ├── page.tsx
        │   ├── layout.tsx
        │   ├── analyze/
        │   ├── projects/
        │   └── settings/
        ├── components/
        │   ├── ChatPanel.tsx
        │   ├── UrlInput.tsx
        │   └── ui/
        └── lib/
            ├── api.ts
            └── utils.ts
```

## 快速启动

### 方式一：Docker 部署（推荐）

**前提条件：** 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/github-analyzer.git
cd github-analyzer

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 API Key

# 3. 一键启动
docker-compose up -d

# 4. 访问应用
# 前端：http://localhost:3000
# 后端：http://localhost:8001
```

**常用命令：**
```bash
docker-compose up -d        # 启动服务
docker-compose down         # 停止服务
docker-compose logs -f      # 查看日志
docker-compose up -d --build  # 重新构建（代码更新后）
```

### 方式二：手动部署

**前提条件：** Python 3.11+、Node.js 20+

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/github-analyzer.git
cd github-analyzer

# 2. 配置后端
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入你的 API Key
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 3. 配置前端（新终端）
cd frontend
npm install
npm run dev
```

**访问地址：**
- 前端：http://localhost:3000
- 后端：http://localhost:8001
- API 文档：http://localhost:8001/docs

## 环境变量配置

在 `backend/.env` 中配置：

```env
# GitHub 配置（可选，提高 API 限额）
GITHUB_TOKEN=your_github_token

# AI 模型配置（必填）
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Embedding 模型配置（用于 RAG 向量检索）
EMBEDDING_API_KEY=your_embedding_key
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v4
```

### 支持的 AI 提供商

| 提供商 | OPENAI_BASE_URL | 模型示例 |
|--------|-----------------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-turbo |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| 智谱 AI | https://open.bigmodel.cn/api/paas/v4 | GLM-4.5-Air |
| Moonshot | https://api.moonshot.cn/v1 | moonshot-v1-8k |

## 页面路由

| 路径 | 说明 |
|------|------|
| `/` | 首页 - 输入 GitHub 仓库地址进行分析 |
| `/projects` | 已分析项目列表 |
| `/analyze/[id]` | 项目分析详情 |
| `/settings` | 系统设置（配置管理、存储管理） |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/analyze` | 发起分析任务 |
| GET | `/api/analyze/{id}/status` | 查询分析状态 |
| GET | `/api/analyze/{id}/result` | 获取分析结果 |
| GET | `/api/projects` | 获取项目列表 |
| GET | `/api/projects/{id}` | 获取项目详情 |
| DELETE | `/api/projects/{id}` | 删除项目 |
| POST | `/api/projects/{id}/reanalyze` | 重新分析 |
| POST | `/api/qa/sessions` | 创建问答会话 |
| POST | `/api/qa/sessions/{id}/messages` | 发送问答消息 |
| GET | `/api/qa/sessions/{id}/history` | 获取对话历史 |
| GET | `/api/qa/index-status/{owner}/{repo}` | 查询索引状态 |
| POST | `/api/qa/reindex/{owner}/{repo}` | 重新索引代码 |
| GET | `/api/config/providers` | 获取支持的提供商 |
| GET | `/api/config/keys` | 获取当前配置 |
| POST | `/api/config/update` | 更新配置 |
| GET | `/api/config/storage` | 获取存储信息 |
| POST | `/api/config/cleanup` | 清理旧数据 |
| GET | `/api/health` | 健康检查 |

## 已知限制

1. DashScope Embedding 每批最多 10 个文本
2. 代码索引最多 50 个文件
3. 只有 Python 文件支持 AST 分块，其他语言使用字符分割

## 许可证

MIT
