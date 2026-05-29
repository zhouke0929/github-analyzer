# GitHub项目智能分析 - 后端API接口文档

> 版本：v2.0  
> 日期：2026-05-30  
> 状态：已确认

---

## 基础信息

| 项目 | 说明 |
|------|------|
| Base URL | `http://localhost:8000/api` |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | 无（本地部署） |

## 通用响应结构

**成功响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

**错误响应：**
```json
{
  "code": 400,
  "message": "错误描述",
  "data": null
}
```

---

## 接口总览

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | `/analyze` | 发起分析任务 | ✅ |
| GET | `/analyze/{id}/status` | 查询分析状态 | ✅ |
| GET | `/analyze/{id}/result` | 获取完整分析结果 | ✅ |
| GET | `/health` | 健康检查 | ✅ |

---

## 1. 发起分析任务

`POST /api/analyze`

### Request Body

```json
{
  "url": "https://github.com/facebook/react"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | GitHub仓库URL，格式：`https://github.com/{owner}/{repo}` |

### 成功响应（202 Accepted）

```json
{
  "code": 0,
  "message": "分析任务已创建",
  "data": {
    "id": "a1b2c3d4",
    "status": "pending",
    "repo_info": {
      "owner": "facebook",
      "repo": "react",
      "full_name": "facebook/react",
      "description": "The library for web and native user interfaces.",
      "stars": 234000,
      "forks": 45000,
      "language": "JavaScript",
      "updated_at": "2026-05-28T10:00:00Z",
      "topics": ["javascript", "react", "frontend"]
    }
  }
}
```

### 错误响应

| HTTP状态码 | code | 说明 |
|------------|------|------|
| 400 | 400 | URL格式错误（非GitHub地址） |
| 404 | 404 | 仓库不存在或为私有仓库 |
| 429 | 429 | 请求过于频繁 |

---

## 2. 查询分析状态

`GET /api/analyze/{id}/status`

### Path参数

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 分析任务ID |

### 成功响应（200 OK）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "a1b2c3d4",
    "status": "processing",
    "progress": {
      "total": 5,
      "completed": 2,
      "current_step": "正在翻译README...",
      "steps": [
        {"name": "readme_translate", "label": "翻译README", "status": "completed"},
        {"name": "summary", "label": "生成摘要", "status": "processing"},
        {"name": "tech_stack", "label": "技术栈分析", "status": "processing"},
        {"name": "architecture", "label": "架构分析", "status": "pending"},
        {"name": "issues", "label": "Issues分析", "status": "pending"}
      ]
    }
  }
}
```

### status 枚举值

| 值 | 说明 |
|------|------|
| pending | 排队等待中 |
| processing | 分析进行中 |
| completed | 分析完成 |
| failed | 分析失败 |

### step status 枚举值

| 值 | 说明 |
|------|------|
| pending | 等待执行 |
| processing | 执行中 |
| completed | 已完成 |
| failed | 执行失败 |

---

## 3. 获取完整分析结果

`GET /api/analyze/{id}/result`

> 当 status 为 `completed` 时可调用此接口获取结果

### Path参数

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 分析任务ID |

### 成功响应（200 OK）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "a1b2c3d4",
    "repo_info": {
      "owner": "facebook",
      "repo": "react",
      "full_name": "facebook/react",
      "description": "The library for web and native user interfaces.",
      "stars": 234000,
      "forks": 45000,
      "language": "JavaScript",
      "updated_at": "2026-05-28T10:00:00Z",
      "topics": ["javascript", "react", "frontend"]
    },
    "summary": "用于构建用户界面的声明式JavaScript库",
    "readme_cn": "# React\n\nReact 是一个用于构建用户界面的 JavaScript 库...\n\n（Markdown格式的翻译内容）",
    "tech_stack": {
      "languages": [
        {"name": "JavaScript", "percentage": 85.2},
        {"name": "TypeScript", "percentage": 14.8}
      ],
      "frameworks": [
        {"name": "React", "version": "19.0.0", "category": "前端框架"}
      ],
      "tools": [
        {"name": "Jest", "category": "测试框架"},
        {"name": "Rollup", "category": "构建工具"}
      ]
    },
    "architecture": {
      "tree": "├── src/\n│   ├── components/\n│   ├── hooks/\n│   └── index.js\n├── package.json\n└── README.md",
      "summary": "",
      "modules": [
        {"name": "src", "path": "src", "description": "源代码目录"},
        {"name": "components", "path": "src/components", "description": "UI组件"}
      ],
      "file_stats": {
        "total_files": 540,
        "total_dirs": 111,
        "by_extension": {".js": 200, ".ts": 150},
        "by_language": {"JavaScript": 200, "TypeScript": 150}
      },
      "design_patterns": ["组件模式", "Hooks模式"]
    },
    "issues_analysis": {
      "total": 100,
      "open_count": 15,
      "closed_count": 85,
      "close_rate": 0.85,
      "avg_close_days": 2.5,
      "top_labels": [
        {"name": "bug", "count": 30},
        {"name": "enhancement", "count": 20}
      ],
      "monthly_trend": [
        {"month": "2026-04", "created": 45, "closed": 40},
        {"month": "2026-05", "created": 55, "closed": 45}
      ],
      "summary": "该项目近3个月共有100个Issues，关闭率85%，平均处理时间2.5天，维护质量优秀。"
    }
  }
}
```

### 错误响应

| HTTP状态码 | code | 说明 |
|------------|------|------|
| 404 | 404 | 分析任务不存在 |
| 400 | 400 | 分析尚未完成 |

---

## 4. 健康检查

`GET /api/health`

### 成功响应（200 OK）

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-30T12:00:00Z",
  "github_api": {
    "limit": 5000,
    "authenticated": true,
    "message": "已认证，5000次/小时"
  }
}
```

---

## 前端调用流程

```
1. 用户输入URL
   → POST /api/analyze
   → 获得任务ID + 仓库基础信息（立即展示）

2. 轮询分析状态（建议每2秒一次）
   → GET /api/analyze/{id}/status
   → 展示进度条和当前步骤

3. 分析完成（status = completed）
   → GET /api/analyze/{id}/result
   → 展示完整分析结果
```

### 分析步骤说明

| 步骤 | 名称 | 说明 |
|------|------|------|
| 1 | readme_translate | 获取并翻译README |
| 2 | summary | 生成项目一句话摘要 |
| 3 | tech_stack | 分析技术栈（语言、框架、工具） |
| 4 | architecture | 分析项目架构（目录结构、模块） |
| 5 | issues | 分析Issues趋势 |

### 轮询建议

- 轮询间隔：2秒
- 首次轮询延迟：1秒（发起分析后）
- 最大轮询时长：120秒（超时后提示用户刷新）

---

## 字段说明

### repo_info

| 字段 | 类型 | 说明 |
|------|------|------|
| owner | string | 仓库所有者 |
| repo | string | 仓库名称 |
| full_name | string | 完整名称（owner/repo） |
| description | string | 仓库描述 |
| stars | number | Star数量 |
| forks | number | Fork数量 |
| language | string | 主要编程语言 |
| updated_at | string | 最近更新时间（ISO 8601） |
| topics | string[] | 项目标签 |

### tech_stack

| 字段 | 类型 | 说明 |
|------|------|------|
| languages | array | 编程语言分布 |
| languages[].name | string | 语言名称 |
| languages[].percentage | number | 占比（百分比） |
| frameworks | array | 框架列表 |
| frameworks[].name | string | 框架名称 |
| frameworks[].version | string | 版本号 |
| frameworks[].category | string | 分类 |
| tools | array | 工具列表 |
| tools[].name | string | 工具名称 |
| tools[].category | string | 分类 |

### architecture

| 字段 | 类型 | 说明 |
|------|------|------|
| tree | string | 目录树文本 |
| summary | string | 架构概述（可为空） |
| modules | array | 主要模块列表 |
| modules[].name | string | 模块名称 |
| modules[].path | string | 模块路径 |
| modules[].description | string | 模块说明 |
| file_stats | object | 文件统计 |
| file_stats.total_files | number | 文件总数 |
| file_stats.total_dirs | number | 目录总数 |
| file_stats.by_extension | object | 按扩展名统计 |
| file_stats.by_language | object | 按语言统计 |
| design_patterns | string[] | 设计模式列表 |

### issues_analysis

| 字段 | 类型 | 说明 |
|------|------|------|
| total | number | Issues总数 |
| open_count | number | 待处理数量 |
| closed_count | number | 已关闭数量 |
| close_rate | number | 关闭率（0-1） |
| avg_close_days | number | 平均关闭天数 |
| top_labels | array | 主要标签 |
| top_labels[].name | string | 标签名称 |
| top_labels[].count | number | 标签数量 |
| monthly_trend | array | 月度趋势 |
| monthly_trend[].month | string | 月份（YYYY-MM） |
| monthly_trend[].created | number | 新增数量 |
| monthly_trend[].closed | number | 关闭数量 |
| summary | string | 分析摘要 |

---

**文档维护：** 后端开发  
**最后更新：** 2026-05-30
