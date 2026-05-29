"use client";

import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import type { AnalysisResult } from "@/lib/api";

interface ExportButtonProps {
  result: AnalysisResult;
}

export function ExportButton({ result }: ExportButtonProps) {
  const handleExport = () => {
    const report = `# ${result.repo_info.full_name} - 智能分析报告

> 生成时间：${new Date().toLocaleDateString("zh-CN")}
> 分析工具：GitHub项目智能分析

## 项目概览

- **一句话摘要**：${result.summary}
- **Star数**：${result.repo_info.stars.toLocaleString()}
- **Fork数**：${result.repo_info.forks.toLocaleString()}
- **主要语言**：${result.repo_info.language}
- **最近更新**：${new Date(result.repo_info.updated_at).toLocaleDateString("zh-CN")}

## README 中文翻译

${result.readme_cn}

## 技术栈分析

### 编程语言
${result.tech_stack.languages.map((l) => `- ${l.name}: ${l.percentage}%`).join("\n")}

### 框架
${result.tech_stack.frameworks.map((f) => `- ${f.name} ${f.version || ""} (${f.category || ""})`).join("\n")}

### 工具
${result.tech_stack.tools.map((t) => `- ${t.name} (${t.category || ""})`).join("\n")}
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
