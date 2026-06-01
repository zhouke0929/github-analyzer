"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { MessageSquare, Send, Loader2, Bot, User, Database, CheckCircle, AlertCircle, Square } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { getIndexStatus, getQAHistory, cancelIndex, reindexCode, type IndexStatus, type IndexProgress, type QAMessage } from "@/lib/api";

interface Message {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  references?: { file_path: string; content: string }[];
  tools_used?: string[];
  created_at: string;
}

interface ChatPanelProps {
  sessionId: string;
  owner: string;
  repo: string;
  onSendMessage: (message: string, signal?: AbortSignal) => Promise<Message>;
}

export function ChatPanel({ sessionId, owner, repo, onSendMessage }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [isIndexing, setIsIndexing] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 滚动到底部
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 加载对话历史
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const res = await getQAHistory(sessionId);
        if (res.code === 0 && res.data?.messages) {
          const historyMessages: Message[] = res.data.messages.map((msg: QAMessage) => ({
            message_id: msg.message_id,
            role: msg.role,
            content: msg.content,
            references: msg.references,
            tools_used: msg.tools_used,
            created_at: msg.created_at,
          }));
          if (historyMessages.length > 0) {
            setMessages(historyMessages);
          }
        }
      } catch (error) {
        console.error("加载对话历史失败:", error);
      }
    };

    loadHistory();
  }, [sessionId]);

  // 轮询索引状态
  useEffect(() => {
    let isMounted = true;
    let interval: NodeJS.Timeout | null = null;

    const checkIndexStatus = async () => {
      try {
        const res = await getIndexStatus(owner, repo);
        if (isMounted && res.code === 0 && res.data) {
          setIndexStatus(res.data);

          // 判断是否正在索引：progress 存在且状态为 indexing
          const indexing = !!(res.data.progress && res.data.progress.status === "indexing");
          setIsIndexing(indexing);

          // 如果索引完成（有文档且不在索引中），停止轮询
          if (res.data.document_count > 0 && !indexing && interval) {
            clearInterval(interval);
            interval = null;
          }
        }
      } catch (error) {
        console.error("获取索引状态失败:", error);
      }
    };

    // 立即检查一次
    checkIndexStatus();

    // 每 3 秒轮询一次（直到索引完成）
    interval = setInterval(checkIndexStatus, 3000);

    return () => {
      isMounted = false;
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [owner, repo]);

  // 停止生成
  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  // 手动触发索引
  const handleReindex = async () => {
    try {
      setIsIndexing(true);
      await reindexCode(owner, repo);
      // 重新检查索引状态
      const res = await getIndexStatus(owner, repo);
      if (res.code === 0 && res.data) {
        setIndexStatus(res.data);
      }
    } catch (error) {
      console.error("触发索引失败:", error);
      setIsIndexing(false);
    }
  };

  // 发送消息
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      message_id: `user-${Date.now()}`,
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // 创建新的 AbortController
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await onSendMessage(input, abortController.signal);
      // 检查是否被取消
      if (abortController.signal.aborted) {
        const cancelMessage: Message = {
          message_id: `cancel-${Date.now()}`,
          role: "assistant",
          content: "生成已停止。",
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, cancelMessage]);
      } else {
        setMessages((prev) => [...prev, response]);
      }
    } catch (error) {
      // 如果是取消操作，不显示错误
      if (abortController.signal.aborted) {
        const cancelMessage: Message = {
          message_id: `cancel-${Date.now()}`,
          role: "assistant",
          content: "生成已停止。",
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, cancelMessage]);
      } else {
        console.error("发送消息失败:", error);
        const errorMessage: Message = {
          message_id: `error-${Date.now()}`,
          role: "assistant",
          content: "抱歉，发送消息时出现错误，请重试。",
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 预设问题
  const presetQuestions = [
    "这个项目的核心功能是什么？",
    "如何快速上手使用这个项目？",
    "项目的主要模块有哪些？",
    "这个项目使用了哪些设计模式？",
  ];

  return (
    <Card className="w-full h-[600px] flex flex-col">
      <CardHeader className="pb-3 shrink-0">
        <CardTitle className="text-lg flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-github" />
          智能问答
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          关于 {owner}/{repo} 的代码问答
        </p>

        {/* 索引状态指示器 */}
        {indexStatus && (
          <div className={`flex flex-col gap-1 text-xs px-3 py-2 rounded-md mt-2 ${
            indexStatus.document_count > 0
              ? "bg-green-50 text-green-700 border border-green-200"
              : isIndexing
                ? "bg-yellow-50 text-yellow-700 border border-yellow-200"
                : "bg-gray-50 text-gray-500 border border-gray-200"
          }`}>
            <div className="flex items-center gap-2">
              <Database className="w-3.5 h-3.5" />
              {indexStatus.document_count > 0 ? (
                <>
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span>代码索引就绪 ({indexStatus.document_count} 个文档块)</span>
                </>
              ) : isIndexing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>正在索引代码...</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>代码未索引（语义搜索不可用）</span>
                  <Button
                    variant="outline"
                    size="sm"
                    className="ml-auto cursor-pointer"
                    onClick={handleReindex}
                  >
                    立即索引
                  </Button>
                </>
              )}
            </div>
            {/* 索引进度详情 */}
            {indexStatus.progress && indexStatus.progress.status === "indexing" && (
              <div className="ml-5">
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-yellow-100 rounded-full h-1.5">
                    <div
                      className="bg-yellow-500 h-1.5 rounded-full transition-all duration-300"
                      style={{
                        width: `${indexStatus.progress.total > 0
                          ? (indexStatus.progress.current / indexStatus.progress.total * 100)
                          : 0}%`
                      }}
                    />
                  </div>
                  <span className="text-yellow-600">
                    {indexStatus.progress.current}/{indexStatus.progress.total}
                  </span>
                </div>
                <p className="text-yellow-600 mt-0.5">{indexStatus.progress.message}</p>
              </div>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0 min-h-0">
        {/* 消息区域 */}
        <div
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4"
          style={{ minHeight: 0 }}
        >
          {messages.length === 0 ? (
            <div className="text-center py-8">
              <Bot className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-4">
                你好！我可以帮你理解和分析这个项目的代码。
              </p>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">试试问我：</p>
                {presetQuestions.map((question, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    className="mr-2 mb-2 cursor-pointer"
                    onClick={() => {
                      setInput(question);
                    }}
                  >
                    {question}
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.message_id}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-lg p-3 ${
                    msg.role === "user"
                      ? "bg-github text-white"
                      : "bg-muted"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {msg.role === "assistant" && (
                      <Bot className="w-4 h-4 mt-1 shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      {msg.role === "user" ? (
                        <div className="whitespace-pre-wrap">{msg.content}</div>
                      ) : (
                        <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeRaw]}
                            components={{
                              pre: ({ children, ...props }) => (
                                <pre className="overflow-x-auto bg-background/50 rounded p-2" {...props}>
                                  {children}
                                </pre>
                              ),
                              code: ({ children, className, ...props }) => {
                                const isInline = !className;
                                return isInline ? (
                                  <code className="bg-background/50 rounded px-1 py-0.5 text-sm" {...props}>
                                    {children}
                                  </code>
                                ) : (
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                );
                              },
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      )}

                      {/* 显示使用的工具 */}
                      {msg.tools_used && msg.tools_used.length > 0 && (
                        <div className="mt-2 text-xs opacity-70">
                          使用工具: {msg.tools_used.join(", ")}
                        </div>
                      )}

                      {/* 显示代码引用 */}
                      {msg.references && msg.references.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {msg.references.map((ref, index) => (
                            <div
                              key={index}
                              className="text-xs bg-background/50 rounded p-2"
                            >
                              <div className="font-medium">{ref.file_path}</div>
                              <pre className="mt-1 overflow-x-auto">
                                <code>{ref.content}</code>
                              </pre>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    {msg.role === "user" && (
                      <User className="w-4 h-4 mt-1 shrink-0" />
                    )}
                  </div>
                </div>
              </div>
            ))
          )}

          {/* 加载状态 */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>思考中...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 输入区域 */}
        <div className="border-t p-4 shrink-0">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入你的问题..."
              className="flex-1 min-h-[60px] max-h-[120px]"
              disabled={isLoading}
            />
            {isLoading ? (
              <Button
                onClick={handleStop}
                variant="destructive"
                className="cursor-pointer"
                title="停止生成"
              >
                <Square className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                onClick={handleSend}
                disabled={!input.trim()}
                className="cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </Button>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            {isLoading ? "生成中...点击红色按钮停止" : "按 Enter 发送，Shift + Enter 换行"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
