"use client";

import { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import {
  getProjectDetail,
  deleteProject,
  reanalyzeProject,
  createQASession,
  sendQAMessage,
  type AnalysisResult,
  type QAMessage,
} from "@/lib/api";
import { SummaryCard } from "@/components/SummaryCard";
import { TechArchitectureCard } from "@/components/TechArchitectureCard";
import { ReadmeViewer } from "@/components/ReadmeViewer";
import { IssuesAnalysisCard } from "@/components/IssuesAnalysisCard";
import { ExportButton } from "@/components/ExportButton";
import { ChatPanel } from "@/components/ChatPanel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import {
  GitBranch,
  ArrowLeft,
  Trash2,
  RefreshCw,
  Loader2,
  ExternalLink,
} from "lucide-react";

export default function AnalyzeDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("readme");
  const [isDeleting, setIsDeleting] = useState(false);
  const [isReanalyzing, setIsReanalyzing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isCreatingSession, setIsCreatingSession] = useState(false);

  // 加载项目详情
  const loadProject = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await getProjectDetail(id);
      if (res.code === 0 && res.data) {
        // 检查是否是pending状态
        if (res.data.status === "pending" || res.data.status === "processing") {
          // 开始轮询等待分析完成
          pollForCompletion(id);
        } else {
          setResult(res.data);
          setIsLoading(false);
        }
      } else {
        setError(res.message || "加载失败");
        setIsLoading(false);
      }
    } catch {
      setError("网络请求失败");
      setIsLoading(false);
    }
  }, [id]);

  // 轮询等待分析完成
  const pollForCompletion = useCallback((projectId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await getProjectDetail(projectId);
        if (res.code === 0 && res.data) {
          if (res.data.status === "completed") {
            clearInterval(interval);
            setResult(res.data);
            setIsLoading(false);
          } else if (res.data.status === "failed") {
            clearInterval(interval);
            setError("分析失败");
            setIsLoading(false);
          }
          // 如果还是pending/processing，继续轮询
        }
      } catch {
        // 轮询出错，继续尝试
      }
    }, 2000); // 每2秒检查一次

    // 5分钟后停止轮询
    setTimeout(() => {
      clearInterval(interval);
      if (isLoading) {
        setError("分析超时，请稍后刷新");
        setIsLoading(false);
      }
    }, 300000);

    return () => clearInterval(interval);
  }, [isLoading]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  // 删除项目
  const handleDelete = async () => {
    if (!result) return;
    if (!confirm(`确定要删除 ${result.repo_info.full_name} 的分析记录吗？`)) return;

    setIsDeleting(true);
    try {
      const res = await deleteProject(id);
      if (res.code === 0) {
        // 跳转回项目列表
        window.location.href = "/projects";
      } else {
        alert(res.message || "删除失败");
      }
    } catch {
      alert("删除失败");
    } finally {
      setIsDeleting(false);
    }
  };

  // 重新分析
  const handleReanalyze = async () => {
    if (!result) return;
    if (!confirm(`确定要重新分析 ${result.repo_info.full_name} 吗？`)) return;

    setIsReanalyzing(true);
    try {
      const res = await reanalyzeProject(id);
      if (res.code === 0 && res.data) {
        // 跳转到新分析结果
        window.location.href = `/analyze/${res.data.id}`;
      } else {
        alert(res.message || "重新分析失败");
      }
    } catch {
      alert("重新分析失败");
    } finally {
      setIsReanalyzing(false);
    }
  };

  // 创建问答会话
  const handleCreateSession = async () => {
    if (!result) return;

    setIsCreatingSession(true);
    try {
      const res = await createQASession(id);
      if (res.code === 0 && res.data) {
        setSessionId(res.data.session_id);
      } else {
        alert(res.message || "创建会话失败");
      }
    } catch {
      alert("创建会话失败");
    } finally {
      setIsCreatingSession(false);
    }
  };

  // 发送消息
  const handleSendMessage = async (message: string): Promise<QAMessage> => {
    if (!sessionId) {
      throw new Error("会话不存在");
    }

    const res = await sendQAMessage(sessionId, message);
    if (res.code === 0 && res.data) {
      return res.data;
    } else {
      throw new Error(res.message || "发送消息失败");
    }
  };

  // 加载中状态
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-github mx-auto mb-4" />
          <p className="text-muted-foreground">正在分析项目，请稍候...</p>
          <p className="text-sm text-muted-foreground mt-2">这可能需要1-2分钟</p>
        </div>
      </div>
    );
  }

  // 错误状态
  if (error || !result) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-4">{error || "项目不存在"}</p>
          <Link href="/projects">
            <Button variant="outline" className="cursor-pointer">
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回项目列表
            </Button>
          </Link>
        </div>
      </div>
    );
  }

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
          <div className="flex items-center gap-2">
            <a
              href={`https://github.com/${result.repo_info.owner}/${result.repo_info.repo}`}
              target="_blank"
              rel="noopener noreferrer"
              title="查看GitHub原项目"
            >
              <Button
                variant="ghost"
                size="sm"
                className="cursor-pointer"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                GitHub
              </Button>
            </a>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReanalyze}
              disabled={isReanalyzing}
              className="cursor-pointer"
            >
              {isReanalyzing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              重新分析
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting}
              className="cursor-pointer text-destructive hover:text-destructive"
            >
              {isDeleting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              删除
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* 顶部操作栏 */}
        <div className="flex items-center justify-between mb-6">
          <Link href="/projects">
            <Button variant="ghost" className="cursor-pointer">
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回项目列表
            </Button>
          </Link>
          <ExportButton result={result} />
        </div>

        {/* Summary Card */}
        <div className="mb-6">
          <SummaryCard
            repoInfo={result.repo_info}
            summary={result.summary}
          />
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full justify-start mb-6 flex-wrap">
            <TabsTrigger value="readme" className="cursor-pointer">
              README 翻译
            </TabsTrigger>
            <TabsTrigger value="tech-arch" className="cursor-pointer">
              技术栈与架构
            </TabsTrigger>
            {result.issues_analysis && (
              <TabsTrigger value="issues" className="cursor-pointer">
                Issues 趋势
              </TabsTrigger>
            )}
            <TabsTrigger value="qa" className="cursor-pointer">
              智能问答
            </TabsTrigger>
          </TabsList>

          <TabsContent value="readme">
            <ReadmeViewer
              content={result.readme_cn}
              owner={result.repo_info.owner}
              repo={result.repo_info.repo}
              defaultBranch={result.default_branch}
            />
          </TabsContent>

          <TabsContent value="tech-arch">
            <TechArchitectureCard
              techStack={result.tech_stack}
              architecture={result.architecture}
            />
          </TabsContent>

          {result.issues_analysis && (
            <TabsContent value="issues">
              <IssuesAnalysisCard issuesAnalysis={result.issues_analysis} />
            </TabsContent>
          )}

          <TabsContent value="qa">
            {sessionId ? (
              <ChatPanel
                sessionId={sessionId}
                owner={result.repo_info.owner}
                repo={result.repo_info.repo}
                onSendMessage={handleSendMessage}
              />
            ) : (
              <div className="text-center py-12">
                <Button
                  onClick={handleCreateSession}
                  disabled={isCreatingSession}
                  className="cursor-pointer"
                >
                  {isCreatingSession ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : null}
                  {isCreatingSession ? "正在初始化..." : "开始智能问答"}
                </Button>
                <p className="text-sm text-muted-foreground mt-2">
                  首次使用需要索引代码，可能需要一些时间
                </p>
              </div>
            )}
          </TabsContent>
        </Tabs>
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
