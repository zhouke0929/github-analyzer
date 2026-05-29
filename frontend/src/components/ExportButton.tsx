"use client";

import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import type { AnalysisResult } from "@/lib/api";

interface ExportButtonProps {
  result: AnalysisResult;
}

export function ExportButton({ result }: ExportButtonProps) {
  const handleExport = () => {
    // 基础报告内容
    let report = `# ${result.repo_info.full_name} - 智能分析报告

> 生成时间：${new Date().toLocaleDateString("zh-CN")}
> 分析工具：GitHub项目智能分析

## 📋 项目概览

- **一句话摘要**：${result.summary}
- **Star数**：${result.repo_info.stars.toLocaleString()}
- **Fork数**：${result.repo_info.forks.toLocaleString()}
- **主要语言**：${result.repo_info.language}
- **最近更新**：${new Date(result.repo_info.updated_at).toLocaleDateString("zh-CN")}

## 🌐 README 中文翻译

${result.readme_cn}

## 🛠️ 技术栈与架构

### 编程语言
${result.tech_stack.languages.map((l) => `- ${l.name}: ${l.percentage}%`).join("\n")}

### 框架
${result.tech_stack.frameworks.map((f) => `- ${f.name} ${f.version || ""} (${f.category || ""})`).join("\n")}

### 工具
${result.tech_stack.tools.map((t) => `- ${t.name} (${t.category || ""})`).join("\n")}
`;

    // 架构分析部分
    if (result.architecture) {
      report += `
### 架构概述
${result.architecture.summary}

### 文件统计
- 文件总数：${result.architecture.file_stats.total_files}
- 目录总数：${result.architecture.file_stats.total_dirs}

### 主要模块
${result.architecture.modules.map((m) => `- **${m.name}** (${m.path}): ${m.description}`).join("\n")}
`;

      if (result.architecture.design_patterns.length > 0) {
        report += `
### 设计模式
${result.architecture.design_patterns.map((p) => `- ${p}`).join("\n")}
`;
      }
    }

    // Issues分析部分
    if (result.issues_analysis) {
      report += `
## 📊 Issues 趋势分析

### 统计概览
- **总Issues数**：${result.issues_analysis.total}
- **待处理**：${result.issues_analysis.open_count}
- **已关闭**：${result.issues_analysis.closed_count}
- **关闭率**：${Math.round(result.issues_analysis.close_rate * 100)}%
- **平均处理时间**：${result.issues_analysis.avg_close_days}天

### 分析摘要
${result.issues_analysis.summary}

### 主要标签
${result.issues_analysis.top_labels.map((l) => `- ${l.name}: ${l.count}个`).join("\n")}
`;
    }

    report += `
---
*报告由 GitHub项目智能分析 自动生成*
`;

    const blob = new Blob([report], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${result.repo_info.repo}-analysis-report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Button
      variant="outline"
      onClick={handleExport}
      className="cursor-pointer"
    >
      <Download className="w-4 h-4 mr-2" />
      导出报告
    </Button>
  );
}
