# GitHub项目智能分析

AI驱动的Web应用，帮助中国开发者快速理解和评估GitHub项目。

## 功能特性

- **README中文翻译** - 保留Markdown格式的中文翻译，支持HTML标签渲染
- **项目一句话摘要** - 用15-30个汉字概括项目核心价值
- **技术栈分析** - 识别语言分布、框架和工具
- **仓库更新时间** - 显示代码实际推送时间（pushed_at）

## 项目结构

```
GitHub项目智能分析/
├── backend/                    # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/               # API路由
│   │   │   ├── analyze.py     # 分析接口（核心业务逻辑）
│   │   │   └── health.py      # 健康检查
│   │   ├── services/          # 业务服务
│   │   │   ├── ai_service.py          # AI模型调用封装
│   │   │   ├── github_service.py      # GitHub API封装
│   │   │   ├── translate_service.py   # README翻译服务
│   │   │   ├── summary_service.py     # 项目摘要服务
│   │   │   └── tech_stack_service.py  # 技术栈分析服务
│   │   ├── models/            # 数据模型
│   │   ├── utils/             # 工具函数
│   │   ├── config.py          # 配置管理
│   │   └── main.py            # FastAPI入口
│   ├── data/                  # 数据目录（自动生成）
│   ├── .env.example           # 环境变量示例
│   └── requirements.txt
├── frontend/                   # 前端应用 (Next.js 16)
│   ├── src/
│   │   ├── app/               # 页面和布局
│   │   ├── components/        # UI组件
│   │   ├── hooks/             # 自定义Hook
│   │   └── lib/               # API客户端
│   ├── next.config.ts         # Next.js配置（含API代理）
│   └── package.json
├── docs/                       # 项目文档
└── README.md
```

## 快速启动

### 后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env   # 配置API密钥
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端地址：http://localhost:8000
API文档：http://localhost:8000/docs

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：http://localhost:3000（同时支持 http://127.0.0.1:3000）

## 环境变量配置

在 `backend/.env` 中配置：

```env
# AI模型配置（必填）
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# GitHub配置（可选，提高API限额）
GITHUB_TOKEN=your_github_token

# CORS配置
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

### 支持的AI提供商

| 提供商 | OPENAI_BASE_URL | 模型示例 |
|--------|-----------------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-turbo |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| 智谱AI | https://open.bigmodel.cn/api/paas/v4 | GLM-4.5-Air |
| Moonshot | https://api.moonshot.cn/v1 | moonshot-v1-8k |

## API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/analyze` | 发起分析任务 |
| GET | `/api/analyze/{id}/status` | 查询分析状态 |
| GET | `/api/analyze/{id}/result` | 获取分析结果 |
| GET | `/api/health` | 健康检查 |

## 项目文档

- [开发指南](docs/开发指南.md) - 完整的开发文档，包含架构、已知问题
- [API接口文档](docs/API接口文档.md) - 后端API详细说明
- [需求规格文档](docs/需求规格文档.md) - 产品需求
- [技术实现方案文档](docs/技术实现方案文档.md) - 技术方案

## 技术栈

- **后端**: Python, FastAPI, SQLite, httpx, Pydantic
- **前端**: TypeScript, Next.js 16, React 19, Tailwind CSS 4, shadcn/ui
- **AI**: OpenAI兼容接口（支持多家提供商）
- **GitHub**: REST API v3

## 许可证

MIT
