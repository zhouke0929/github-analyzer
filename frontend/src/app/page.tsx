"use client";

import { useState } from "react";
import Link from "next/link";
import { UrlInput } from "@/components/UrlInput";
import { ProgressBar } from "@/components/ProgressBar";
import { SummaryCard } from "@/components/SummaryCard";
import { TechArchitectureCard } from "@/components/TechArchitectureCard";
import { ReadmeViewer } from "@/components/ReadmeViewer";
import { IssuesAnalysisCard } from "@/components/IssuesAnalysisCard";
import { ExportButton } from "@/components/ExportButton";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ChatPanel } from "@/components/ChatPanel";
import { useAnalysis } from "@/hooks/useAnalysis";
import { createQASession, sendQAMessage, type QAMessage } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { GitBranch, ArrowLeft, AlertCircle, FolderOpen, ExternalLink, Loader2, Settings, Database } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Home() {
  const {
    isLoading,
    error,
    repoInfo,
    status,
    result,
    startAnalysisJob,
    reset,
  } = useAnalysis();
  const [activeTab, setActiveTab] = useState("readme");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isCreatingSession, setIsCreatingSession] = useState(false);

  const progressPercent = status?.progress
    ? Math.round(
        (status.progress.completed / status.progress.total) * 100
      )
    : 0;

  // 创建问答会话
  const handleCreateSession = async () => {
    if (!result) return;

    setIsCreatingSession(true);
    try {
      const res = await createQASession(result.id);
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
            <Link href="/projects">
              <Button variant="ghost" size="sm" className="cursor-pointer">
                <FolderOpen className="w-4 h-4 mr-2" />
                已分析项目
              </Button>
            </Link>
            <Link href="/settings">
              <Button variant="ghost" size="sm" className="cursor-pointer">
                <Settings className="w-4 h-4 mr-2" />
                系统设置
              </Button>
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* 分析中 - 全屏加载视图 */}
        {isLoading && (
          <section className="max-w-5xl mx-auto px-4 pt-20 pb-8">
            <div className="text-center space-y-6 mb-10">
              <h1 className="text-3xl font-bold tracking-tight text-foreground">
                正在分析项目
              </h1>
              {repoInfo && (
                <p className="text-lg text-muted-foreground">
                  {repoInfo.full_name}
                </p>
              )}
            </div>

            {status && (
              <ProgressBar
                currentStep={status.progress?.current_step || "处理中..."}
                progress={progressPercent}
              />
            )}

            {!status && (
              <div className="max-w-2xl mx-auto space-y-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4 mx-auto" />
              </div>
            )}

            {error && (
              <div className="mt-6 max-w-2xl mx-auto p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-destructive">
                    分析失败
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">{error}</p>
                  <Button
                    variant="link"
                    size="sm"
                    onClick={reset}
                    className="mt-2 p-0 h-auto text-destructive cursor-pointer"
                  >
                    重试
                  </Button>
                </div>
              </div>
            )}
          </section>
        )}

        {/* 输入页面 - 未加载未结果 */}
        {!isLoading && !result && (
          <section className="max-w-5xl mx-auto px-4 pt-16 pb-8">
            <div className="text-center space-y-6 mb-10">
              <h1 className="text-4xl font-bold tracking-tight text-foreground">
                快速理解任何 GitHub 项目
              </h1>
              <p className="text-lg text-muted-foreground max-w-xl mx-auto">
                输入 GitHub 仓库地址，AI 将为你翻译 README、分析技术栈、架构、Issues 趋势
              </p>
            </div>

            <UrlInput
              onSubmit={(url) => startAnalysisJob(url)}
              isLoading={isLoading}
            />

            {error && (
              <div className="mt-6 max-w-2xl mx-auto p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-destructive">
                    分析失败
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">{error}</p>
                  <Button
                    variant="link"
                    size="sm"
                    onClick={reset}
                    className="mt-2 p-0 h-auto text-destructive cursor-pointer"
                  >
                    重试
                  </Button>
                </div>
              </div>
            )}
          </section>
        )}

        {/* Results Section */}
        {result && (
          <section className="max-w-5xl mx-auto px-4 py-8">
            <div className="flex items-center justify-between mb-6">
              <Button
                variant="ghost"
                onClick={reset}
                className="cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回
              </Button>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="cursor-pointer"
                  title="查看GitHub原项目"
                  onClick={(e) => {
                    e.preventDefault();
                    const url = `https://github.com/${result.repo_info.owner}/${result.repo_info.repo}`;
                    window.open(url, '_blank', 'noopener,noreferrer');
                  }}
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  GitHub
                </Button>
                <ExportButton result={result} />
              </div>
            </div>

            {/* Summary Card */}
            <div className="mb-6">
              <SummaryCard
                repoInfo={result.repo_info}
                summary={result.summary}
              />
            </div>

            {/* Tabs for detailed content */}
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
                <ReadmeViewer content={result.readme_cn} />
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
          </section>
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
