# GitHub 项目智能分析 - 前端

基于 Next.js + shadcn/ui 构建的前端应用，配合后端 API 提供 GitHub 项目分析功能。

## 技术栈

- **框架**: Next.js 16 (App Router)
- **UI**: shadcn/ui + Tailwind CSS v4
- **语言**: TypeScript
- **Markdown**: react-markdown + remark-gfm

## 项目结构

```
src/
├── app/
│   ├── layout.tsx          # 根布局（Inter字体、Toaster）
│   ├── page.tsx            # 主页面（分析流程）
│   └── globals.css         # 全局样式（设计系统）
├── components/
│   ├── ui/                 # shadcn/ui 基础组件
│   ├── UrlInput.tsx        # GitHub URL 输入框
│   ├── ProgressBar.tsx     # 分析进度条
│   ├── SummaryCard.tsx     # 项目摘要卡片
│   ├── TechStackCard.tsx   # 技术栈分析卡片
│   ├── ReadmeViewer.tsx    # README 翻译查看器
│   ├── ExportButton.tsx    # 导出报告按钮
│   └── ThemeToggle.tsx     # 深色/浅色主题切换
├── hooks/
│   └── useAnalysis.ts      # 分析状态管理（轮询机制）
└── lib/
    ├── api.ts              # 后端 API 客户端
    └── utils.ts            # 工具函数（shadcn）
```

## 开发命令

```bash
npm install         # 安装依赖
npm run dev         # 启动开发服务器 (http://localhost:3000)
npm run build       # 构建生产版本
npm start           # 启动生产服务器
```

## 环境变量

创建 `.env.local` 文件（可选）：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

默认连接 `http://localhost:8000/api`。

## 设计规范

- 主色调: 绿色系 (oklch 0.45-0.6, hue 160) - GitHub 主题
- 背景: 浅色 oklch(0.985) / 深色 oklch(0.13)
- 字体: Inter
- 禁止使用蓝紫渐变色

## 添加 shadcn/ui 组件

```bash
npx shadcn@latest add <component-name>
```

已安装: button, card, input, badge, progress, tabs, separator, skeleton, sonner, textarea
