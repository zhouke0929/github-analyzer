"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  getProjects,
  deleteProject,
  type ProjectItem,
} from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  GitBranch,
  Star,
  GitFork,
  Search,
  Trash2,
  ExternalLink,
  ArrowLeft,
  RefreshCw,
} from "lucide-react";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [filteredProjects, setFilteredProjects] = useState<ProjectItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 加载项目列表
  const loadProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await getProjects();
      if (res.code === 0 && res.data) {
        setProjects(res.data.projects);
        setFilteredProjects(res.data.projects);
      } else {
        setError(res.message || "加载失败");
      }
    } catch {
      setError("网络请求失败");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // 搜索筛选
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredProjects(projects);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = projects.filter(
      (p) =>
        p.full_name.toLowerCase().includes(query) ||
        (p.description || "").toLowerCase().includes(query) ||
        (p.summary || "").toLowerCase().includes(query) ||
        (p.language || "").toLowerCase().includes(query)
    );
    setFilteredProjects(filtered);
  }, [searchQuery, projects]);

  // 删除项目
  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`确定要删除 ${name} 的分析记录吗？`)) return;

    try {
      const res = await deleteProject(id);
      if (res.code === 0) {
        setProjects((prev) => prev.filter((p) => p.id !== id));
      } else {
        alert(res.message || "删除失败");
      }
    } catch {
      alert("删除失败");
    }
  };

  // 格式化数字
  const formatNumber = (num: number) => {
    if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
    return num.toString();
  };

  // 格式化日期
  const formatDate = (dateStr: string) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="w-6 h-6 text-github" />
            <span className="font-semibold text-foreground">
              GitHub 项目智能分析
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* 顶部操作栏 */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm" className="cursor-pointer">
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回
              </Button>
            </Link>
            <h1 className="text-2xl font-bold text-foreground">已分析项目</h1>
            <Badge variant="secondary">{projects.length} 个</Badge>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadProjects}
            className="cursor-pointer"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>

        {/* 搜索栏 */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="搜索项目名称、描述、语言..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* 加载状态 */}
        {isLoading && (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-github mx-auto mb-4" />
            <p className="text-muted-foreground">加载中...</p>
          </div>
        )}

        {/* 错误状态 */}
        {error && (
          <div className="text-center py-12">
            <p className="text-destructive mb-4">{error}</p>
            <Button variant="outline" onClick={loadProjects} className="cursor-pointer">
              重试
            </Button>
          </div>
        )}

        {/* 项目列表 */}
        {!isLoading && !error && (
          <>
            {filteredProjects.length === 0 ? (
              <div className="text-center py-12">
                <GitBranch className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">
                  {searchQuery ? "没有找到匹配的项目" : "还没有分析过任何项目"}
                </p>
                {!searchQuery && (
                  <Link href="/">
                    <Button className="mt-4 cursor-pointer">开始分析</Button>
                  </Link>
                )}
              </div>
            ) : (
              <div className="grid gap-4">
                {filteredProjects.map((project) => (
                  <Card
                    key={project.id}
                    className="hover:border-github/30 transition-colors"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          {/* 项目名称 */}
                          <div className="flex items-center gap-2 mb-2">
                            <Link
                              href={`/analyze/${project.id}`}
                              className="text-lg font-semibold text-foreground hover:text-github transition-colors"
                            >
                              {project.full_name}
                            </Link>
                            {project.language && (
                              <Badge variant="secondary" className="text-xs">
                                {project.language}
                              </Badge>
                            )}
                          </div>

                          {/* 描述 */}
                          {project.description && (
                            <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                              {project.description}
                            </p>
                          )}

                          {/* 摘要 */}
                          {project.summary && (
                            <p className="text-sm text-foreground mb-3 line-clamp-1">
                              💡 {project.summary}
                            </p>
                          )}

                          {/* 统计信息 */}
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Star className="w-3.5 h-3.5" />
                              {formatNumber(project.stars)}
                            </span>
                            <span className="flex items-center gap-1">
                              <GitFork className="w-3.5 h-3.5" />
                              {formatNumber(project.forks)}
                            </span>
                            {project.completed_at && (
                              <span>
                                分析于 {formatDate(project.completed_at)}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* 操作按钮 */}
                        <div className="flex items-center gap-2 ml-4">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="cursor-pointer"
                            title="查看GitHub原项目"
                            onClick={(e) => {
                              e.preventDefault();
                              const url = `https://github.com/${project.owner}/${project.repo}`;
                              window.open(url, '_blank', 'noopener,noreferrer');
                            }}
                          >
                            <GitBranch className="w-4 h-4" />
                          </Button>
                          <Link href={`/analyze/${project.id}`}>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="cursor-pointer"
                            >
                              <ExternalLink className="w-4 h-4" />
                            </Button>
                          </Link>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              handleDelete(project.id, project.full_name)
                            }
                            className="cursor-pointer text-destructive hover:text-destructive"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6 mt-auto">
        <div className="max-w-5xl mx-auto px-4 text-center text-sm text-muted-foreground">
          GitHub 项目智能分析 - AI 驱动的开源项目理解工具
        </div>
      </footer>
    </div>
  );
}
