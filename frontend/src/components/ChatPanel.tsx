"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { MessageSquare, Send, Loader2, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

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
  onSendMessage: (message: string) => Promise<Message>;
}

export function ChatPanel({ sessionId, owner, repo, onSendMessage }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // 滚动到底部
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

    try {
      const response = await onSendMessage(input);
      setMessages((prev) => [...prev, response]);
    } catch (error) {
      console.error("发送消息失败:", error);
      const errorMessage: Message = {
        message_id: `error-${Date.now()}`,
        role: "assistant",
        content: "抱歉，发送消息时出现错误，请重试。",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
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
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="cursor-pointer"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            按 Enter 发送，Shift + Enter 换行
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
