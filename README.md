# GitHub项目智能分析

AI驱动的Web应用，帮助中国开发者快速理解和评估GitHub项目。

## 功能特性

- **README中文翻译** - 保留Markdown格式的中文翻译
- **项目一句话摘要** - 用15-30个汉字概括项目核心价值
- **技术栈分析** - 识别语言分布、框架和工具

## 项目结构

```
GitHub项目智能分析/
├── backend/                    # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/               # API路由
│   │   ├── services/          # 业务服务
│   │   ├── models/            # 数据模型
│   │   └── main.py            # 入口
│   ├── requirements.txt
│   └── run.py
├── github-analyzer-frontend/   # 前端应用 (Next.js)
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
python run.py
```

后端地址：http://localhost:8000

### 前端

```bash
cd github-analyzer-frontend
npm install
npm run dev
```

前端地址：http://localhost:3000

## 环境变量配置

在 `backend/.env` 中配置：

```env
# AI模型配置（必填）
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# GitHub配置（可选，提高API限额）
GITHUB_TOKEN=your_github_token
```

## API文档

启动后端后访问：http://localhost:8000/docs

## 技术栈

- **后端**: Python, FastAPI, SQLite
- **前端**: TypeScript, Next.js, React, Tailwind CSS
- **AI**: OpenAI兼容接口（支持多家提供商）

## 许可证

MIT
