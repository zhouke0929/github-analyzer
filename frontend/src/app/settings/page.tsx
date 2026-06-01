"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { GitBranch, ArrowLeft, Save, Loader2, MessageSquare, Database, RefreshCw, Trash2, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ThemeToggle } from "@/components/ThemeToggle";
import { toast } from "sonner";
import { getStorageInfo, cleanupOldData, type StorageInfo } from "@/lib/api";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("config");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // 存储管理状态
  const [storageInfo, setStorageInfo] = useState<StorageInfo | null>(null);
  const [cleaning, setCleaning] = useState(false);
  const [cleanupDays, setCleanupDays] = useState(30);

  // GitHub 配置
  const [githubToken, setGithubToken] = useState("");
  const [githubTokenConfigured, setGithubTokenConfigured] = useState(false);

  // 聊天模型配置
  const [chatApiKey, setChatApiKey] = useState("");
  const [chatApiKeyConfigured, setChatApiKeyConfigured] = useState(false);
  const [chatBaseUrl, setChatBaseUrl] = useState("");
  const [chatModel, setChatModel] = useState("");

  // 向量模型配置
  const [embeddingApiKey, setEmbeddingApiKey] = useState("");
  const [embeddingApiKeyConfigured, setEmbeddingApiKeyConfigured] = useState(false);
  const [embeddingBaseUrl, setEmbeddingBaseUrl] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("");

  // 加载数据
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [storageRes, keysRes] = await Promise.all([
        getStorageInfo(),
        fetch("/api/config/keys").then(r => r.json()),
      ]);

      if (storageRes.code === 0 && storageRes.data) {
        setStorageInfo(storageRes.data);
      }

      if (keysRes.code === 0 && keysRes.data) {
        const data = keysRes.data;
        // 不加载脱敏的 API Key 和 Token，但记录是否已配置
        if (data.github_token && !data.github_token.includes("***未配置***")) {
          setGithubTokenConfigured(true);
        }
        if (data.openai_api_key && !data.openai_api_key.includes("***未配置***")) {
          setChatApiKeyConfigured(true);
        }
        if (data.embedding_api_key && !data.embedding_api_key.includes("***未配置***")) {
          setEmbeddingApiKeyConfigured(true);
        }
        setChatBaseUrl(data.openai_base_url || "");
        setChatModel(data.openai_model || "");
        setEmbeddingBaseUrl(data.embedding_base_url || "");
        setEmbeddingModel(data.embedding_model || "");
      }
    } catch {
      toast.error("加载配置失败");
    } finally {
      setLoading(false);
    }
  };

  // 保存所有配置
  const handleSaveAll = async () => {
    setSaving(true);
    try {
      const response = await fetch("/api/config/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          github_token: githubToken,
          chat_api_key: chatApiKey,
          chat_base_url: chatBaseUrl,
          chat_model: chatModel,
          embedding_api_key: embeddingApiKey,
          embedding_base_url: embeddingBaseUrl,
          embedding_model: embeddingModel,
        }),
      });

      const res = await response.json();
      if (res.code === 0) {
        toast.success(res.message || "配置已保存");
      } else {
        toast.error(res.message || "保存失败");
      }
    } catch {
      toast.error("保存失败");
    } finally {
      setSaving(false);
    }
  };

  // 清理旧数据
  const handleCleanup = async () => {
    if (!confirm(`确定要清理 ${cleanupDays} 天前的数据吗？此操作不可恢复。`)) {
      return;
    }

    setCleaning(true);
    try {
      const res = await cleanupOldData(cleanupDays);
      if (res.code === 0) {
        toast.success(res.message || "清理完成");
        loadData();
      } else {
        toast.error(res.message || "清理失败");
      }
    } catch {
      toast.error("清理失败");
    } finally {
      setCleaning(false);
    }
  };

  // 格式化文件大小
  const formatSize = (mb: number) => {
    if (mb < 1) return `${(mb * 1024).toFixed(1)} KB`;
    return `${mb.toFixed(2)} MB`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link href="/">
              <Button variant="ghost" size="sm" className="cursor-pointer">
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回
              </Button>
            </Link>
            <GitBranch className="w-6 h-6 text-github" />
            <span className="font-semibold text-foreground">系统设置</span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="w-full justify-start mb-6">
            <TabsTrigger value="config" className="cursor-pointer">
              <Settings className="w-4 h-4 mr-2" />
              配置管理
            </TabsTrigger>
            <TabsTrigger value="storage" className="cursor-pointer">
              <Database className="w-4 h-4 mr-2" />
              存储管理
            </TabsTrigger>
          </TabsList>

          {/* 配置管理 */}
          <TabsContent value="config">
            <div className="space-y-6">
              {/* GitHub 配置 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <GitBranch className="w-5 h-5" />
                    GitHub 配置
                  </CardTitle>
                  <CardDescription>配置 GitHub API 访问令牌（可选）</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Label>GitHub Token</Label>
                    <Input
                      type="password"
                      placeholder={githubTokenConfigured ? "已配置（留空保持不变）" : "ghp_xxxxxxxxxxxx"}
                      value={githubToken}
                      onChange={(e) => setGithubToken(e.target.value)}
                    />
                    <p className="text-sm text-muted-foreground">
                      可选配置。不填写时 API 限制 60 次/小时，填写后提升至 5000 次/小时
                      {githubTokenConfigured && " · 当前已配置"}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* 聊天模型配置 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    聊天模型配置
                  </CardTitle>
                  <CardDescription>配置 AI 聊天模型（用于项目分析和问答）</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>模型名称</Label>
                    <Input
                      placeholder="gpt-4o-mini"
                      value={chatModel}
                      onChange={(e) => setChatModel(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>API Key</Label>
                    <Input
                      type="password"
                      placeholder={chatApiKeyConfigured ? "已配置（留空保持不变）" : "输入聊天模型 API Key"}
                      value={chatApiKey}
                      onChange={(e) => setChatApiKey(e.target.value)}
                    />
                    {chatApiKeyConfigured && (
                      <p className="text-xs text-green-600">当前已配置</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label>Base URL</Label>
                    <Input
                      placeholder="兼容 OpenAI 接口的服务地址"
                      value={chatBaseUrl}
                      onChange={(e) => setChatBaseUrl(e.target.value)}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* 向量模型配置 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="w-5 h-5" />
                    向量模型配置
                  </CardTitle>
                  <CardDescription>配置 Embedding 模型（用于代码语义检索）</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>模型名称</Label>
                    <Input
                      placeholder="text-embedding-v4"
                      value={embeddingModel}
                      onChange={(e) => setEmbeddingModel(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>API Key</Label>
                    <Input
                      type="password"
                      placeholder={embeddingApiKeyConfigured ? "已配置（留空保持不变）" : "输入向量模型 API Key"}
                      value={embeddingApiKey}
                      onChange={(e) => setEmbeddingApiKey(e.target.value)}
                    />
                    {embeddingApiKeyConfigured && (
                      <p className="text-xs text-green-600">当前已配置</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label>Base URL</Label>
                    <Input
                      placeholder="兼容 OpenAI 接口的服务地址"
                      value={embeddingBaseUrl}
                      onChange={(e) => setEmbeddingBaseUrl(e.target.value)}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* 保存按钮 */}
              <div className="flex justify-end">
                <Button onClick={handleSaveAll} disabled={saving} className="cursor-pointer" size="lg">
                  {saving ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4 mr-2" />
                  )}
                  保存所有配置
                </Button>
              </div>
            </div>
          </TabsContent>

          {/* 存储管理 */}
          <TabsContent value="storage">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="w-5 h-5" />
                    存储概览
                  </CardTitle>
                  <CardDescription>查看数据存储使用情况</CardDescription>
                </CardHeader>
                <CardContent>
                  {storageInfo && (
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="p-4 bg-muted rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">SQLite 数据库</div>
                        <div className="text-2xl font-bold">{formatSize(storageInfo.database.size_mb)}</div>
                      </div>
                      <div className="p-4 bg-muted rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">ChromaDB 向量数据</div>
                        <div className="text-2xl font-bold">{formatSize(storageInfo.chromadb.size_mb)}</div>
                      </div>
                      <div className="p-4 bg-muted rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">总存储大小</div>
                        <div className="text-2xl font-bold">{formatSize(storageInfo.total_size_mb)}</div>
                      </div>
                      <div className="p-4 bg-muted rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">已分析项目数</div>
                        <div className="text-2xl font-bold">{storageInfo.project_count}</div>
                      </div>
                    </div>
                  )}
                  <Button onClick={loadData} variant="outline" className="mt-4 cursor-pointer">
                    <RefreshCw className="w-4 h-4 mr-2" />
                    刷新
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>清理旧数据</CardTitle>
                  <CardDescription>删除指定天数之前的分析数据</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="space-y-2 flex-1">
                      <Label>保留天数</Label>
                      <Input
                        type="number"
                        min={1}
                        value={cleanupDays}
                        onChange={(e) => setCleanupDays(parseInt(e.target.value) || 30)}
                      />
                    </div>
                    <div className="flex items-end">
                      <Button
                        onClick={handleCleanup}
                        disabled={cleaning}
                        variant="destructive"
                        className="cursor-pointer"
                      >
                        {cleaning ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4 mr-2" />
                        )}
                        清理数据
                      </Button>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    清理 {cleanupDays} 天前的所有分析数据，包括项目分析、QA 会话和向量索引。此操作不可恢复。
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
