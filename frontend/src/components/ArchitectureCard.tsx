"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FolderTree, Layers, Code2, Lightbulb } from "lucide-react";
import type { ArchitectureInfo } from "@/lib/api";

interface ArchitectureCardProps {
  architecture: ArchitectureInfo;
}

function TreeView({ tree }: { tree: string }) {
  return (
    <div className="relative">
      <pre className="p-4 bg-muted rounded-lg text-sm font-mono overflow-x-auto max-h-[400px] overflow-y-auto">
        {tree}
      </pre>
    </div>
  );
}

function ModuleList({ modules }: { modules: ArchitectureInfo["modules"] }) {
  if (modules.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
        <Layers className="w-4 h-4" />
        主要模块
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {modules.map((mod) => (
          <div
            key={mod.path}
            className="p-3 bg-muted rounded-lg border border-border hover:border-github/30 transition-colors"
          >
            <div className="flex items-center gap-2 mb-1">
              <FolderTree className="w-4 h-4 text-github" />
              <span className="font-medium text-foreground">{mod.name}</span>
            </div>
            <p className="text-sm text-muted-foreground">{mod.description}</p>
            <p className="text-xs text-muted-foreground mt-1 font-mono">
              {mod.path}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function FileStatsView({ fileStats }: { fileStats: ArchitectureInfo["file_stats"] }) {
  const languages = Object.entries(fileStats.by_language || {}).slice(0, 8);

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
        <Code2 className="w-4 h-4" />
        文件统计
      </h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 bg-muted rounded-lg text-center">
          <p className="text-2xl font-bold text-github">{fileStats.total_files}</p>
          <p className="text-xs text-muted-foreground">文件总数</p>
        </div>
        <div className="p-3 bg-muted rounded-lg text-center">
          <p className="text-2xl font-bold text-foreground">{fileStats.total_dirs}</p>
          <p className="text-xs text-muted-foreground">目录总数</p>
        </div>
        <div className="p-3 bg-muted rounded-lg text-center">
          <p className="text-2xl font-bold text-foreground">
            {Object.keys(fileStats.by_extension || {}).length}
          </p>
          <p className="text-xs text-muted-foreground">文件类型</p>
        </div>
        <div className="p-3 bg-muted rounded-lg text-center">
          <p className="text-2xl font-bold text-foreground">{languages.length}</p>
          <p className="text-xs text-muted-foreground">编程语言</p>
        </div>
      </div>

      {languages.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {languages.map(([lang, count]) => (
            <Badge key={lang} variant="secondary" className="text-xs">
              {lang}: {count}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

function DesignPatternsView({ patterns }: { patterns: string[] }) {
  if (patterns.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
        <Lightbulb className="w-4 h-4" />
        设计模式
      </h4>
      <div className="flex flex-wrap gap-2">
        {patterns.map((pattern) => (
          <Badge key={pattern} variant="outline" className="text-sm py-1 px-3">
            {pattern}
          </Badge>
        ))}
      </div>
    </div>
  );
}

export function ArchitectureCard({ architecture }: ArchitectureCardProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <FolderTree className="w-5 h-5 text-github" />
          技术架构分析
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 架构概述 */}
        {architecture.summary && (
          <div className="p-4 bg-muted rounded-lg">
            <p className="text-foreground leading-relaxed">{architecture.summary}</p>
          </div>
        )}

        {/* 目录树 */}
        {architecture.tree && <TreeView tree={architecture.tree} />}

        {/* 文件统计 */}
        <FileStatsView fileStats={architecture.file_stats} />

        {/* 模块列表 */}
        <ModuleList modules={architecture.modules} />

        {/* 设计模式 */}
        <DesignPatternsView patterns={architecture.design_patterns} />
      </CardContent>
    </Card>
  );
}
