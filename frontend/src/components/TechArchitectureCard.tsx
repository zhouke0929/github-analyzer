"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Layers,
  Wrench,
  Code2,
  FolderTree,
  Lightbulb,
} from "lucide-react";
import type { TechStack, TechStackItem, ArchitectureInfo } from "@/lib/api";

interface TechArchitectureCardProps {
  techStack: TechStack;
  architecture?: ArchitectureInfo;
}

// 语言分布条
function LanguageBar({ languages }: { languages: TechStackItem[] }) {
  const colors = [
    "bg-github",
    "bg-chart-2",
    "bg-chart-3",
    "bg-chart-4",
    "bg-chart-5",
  ];

  return (
    <div className="space-y-2">
      <div className="flex h-3 rounded-full overflow-hidden bg-muted">
        {languages.map((lang, i) => (
          <div
            key={lang.name}
            className={`${colors[i % colors.length]} transition-all duration-500`}
            style={{ width: `${lang.percentage || 0}%` }}
            title={`${lang.name}: ${lang.percentage}%`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-3">
        {languages.map((lang, i) => (
          <div key={lang.name} className="flex items-center gap-1.5 text-sm">
            <div
              className={`w-2.5 h-2.5 rounded-full ${colors[i % colors.length]}`}
            />
            <span className="text-foreground">{lang.name}</span>
            <span className="text-muted-foreground">{lang.percentage}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// 框架/工具列表
function ItemList({
  items,
  icon: Icon,
}: {
  items: TechStackItem[];
  icon: typeof Layers;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <Badge key={item.name} variant="secondary" className="text-sm py-1 px-3">
          <Icon className="w-3.5 h-3.5 mr-1.5" />
          {item.name}
          {item.version && (
            <span className="ml-1 text-muted-foreground">{item.version}</span>
          )}
        </Badge>
      ))}
    </div>
  );
}

// 文件统计
function FileStatsView({ fileStats }: { fileStats: ArchitectureInfo["file_stats"] }) {
  const languages = Object.entries(fileStats.by_language || {}).slice(0, 6);

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
        <Code2 className="w-4 h-4" />
        文件统计
      </h4>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3 bg-muted rounded-lg text-center">
          <p className="text-xl font-bold text-github">{fileStats.total_files}</p>
          <p className="text-xs text-muted-foreground">文件总数</p>
        </div>
        <div className="p-3 bg-muted rounded-lg text-center">
          <p className="text-xl font-bold text-foreground">{fileStats.total_dirs}</p>
          <p className="text-xs text-muted-foreground">目录总数</p>
        </div>
        <div className="p-3 bg-muted rounded-lg text-center">
          <p className="text-xl font-bold text-foreground">
            {Object.keys(fileStats.by_extension || {}).length}
          </p>
          <p className="text-xs text-muted-foreground">文件类型</p>
        </div>
        <div className="p-3 bg-muted rounded-lg text-center">
          <p className="text-xl font-bold text-foreground">{languages.length}</p>
          <p className="text-xs text-muted-foreground">编程语言</p>
        </div>
      </div>
    </div>
  );
}

// 模块列表
function ModuleList({ modules }: { modules: ArchitectureInfo["modules"] }) {
  if (modules.length === 0) return null;

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
        <FolderTree className="w-4 h-4" />
        主要模块
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {modules.map((mod) => (
          <div
            key={mod.path}
            className="p-2 bg-muted rounded-lg border border-border"
          >
            <div className="flex items-center gap-2">
              <FolderTree className="w-3.5 h-3.5 text-github" />
              <span className="font-medium text-sm text-foreground">{mod.name}</span>
              <span className="text-xs text-muted-foreground">- {mod.description}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// 设计模式
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
          <Badge key={pattern} variant="outline" className="text-sm">
            {pattern}
          </Badge>
        ))}
      </div>
    </div>
  );
}

// 目录树
function DirectoryTree({ tree }: { tree: string }) {
  if (!tree) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
        <FolderTree className="w-4 h-4" />
        目录结构
      </h4>
      <div className="relative rounded-lg border border-border bg-muted/50 overflow-hidden">
        <div className="overflow-x-auto max-h-[300px] overflow-y-auto">
          <pre className="p-4 text-xs leading-5" style={{ fontFamily: 'Consolas, Monaco, "Courier New", monospace', tabSize: 4 }}>
            {tree}
          </pre>
        </div>
      </div>
    </div>
  );
}

export function TechArchitectureCard({ techStack, architecture }: TechArchitectureCardProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Layers className="w-5 h-5 text-github" />
          技术栈与架构
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 编程语言 */}
        {techStack.languages.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
              <Code2 className="w-4 h-4" />
              编程语言
            </h4>
            <LanguageBar languages={techStack.languages} />
          </div>
        )}

        {/* 框架 */}
        {techStack.frameworks.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
              <Layers className="w-4 h-4" />
              框架
            </h4>
            <ItemList items={techStack.frameworks} icon={Layers} />
          </div>
        )}

        {/* 工具 */}
        {techStack.tools.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
              <Wrench className="w-4 h-4" />
              工具
            </h4>
            <ItemList items={techStack.tools} icon={Wrench} />
          </div>
        )}

        {/* 分割线 */}
        {architecture && (
          <div className="border-t border-border pt-4">
            <h3 className="text-base font-semibold mb-4 text-foreground">项目架构</h3>

            {/* 文件统计 */}
            <FileStatsView fileStats={architecture.file_stats} />

            {/* 模块列表 */}
            <div className="mt-4">
              <ModuleList modules={architecture.modules} />
            </div>

            {/* 目录树 */}
            <div className="mt-4">
              <DirectoryTree tree={architecture.tree} />
            </div>

            {/* 设计模式 */}
            <div className="mt-4">
              <DesignPatternsView patterns={architecture.design_patterns} />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
