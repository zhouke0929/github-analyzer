"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

interface ReadmeViewerProps {
  content: string;
  owner?: string;
  repo?: string;
  defaultBranch?: string;
}

// 将相对路径图片转换为GitHub raw URL
function resolveImageUrl(src: string | Blob | undefined, owner?: string, repo?: string, defaultBranch: string = "main"): string {
  // 如果没有src或是Blob类型，返回空字符串
  if (!src || src instanceof Blob) return "";

  // 如果没有owner或repo，直接返回原src
  if (!owner || !repo) return src;

  // 已经是完整URL，直接返回
  if (src.startsWith("http://") || src.startsWith("https://") || src.startsWith("data:")) {
    return src;
  }

  // 处理相对路径
  let cleanSrc = src;
  if (cleanSrc.startsWith("./")) {
    cleanSrc = cleanSrc.slice(2);
  } else if (cleanSrc.startsWith("../")) {
    // 对于../开头的路径，需要向上一级目录
    // 但GitHub raw URL不支持../，所以直接使用根目录
    cleanSrc = cleanSrc.replace(/^\.\.\//, "");
  }

  // 移除开头的/
  cleanSrc = cleanSrc.replace(/^\//, "");

  return `https://raw.githubusercontent.com/${owner}/${repo}/${defaultBranch}/${cleanSrc}`;
}

export function ReadmeViewer({ content, owner, repo, defaultBranch = "main" }: ReadmeViewerProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <FileText className="w-5 h-5 text-github" />
          README 中文翻译
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="markdown-body">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={{
              img: ({ src, alt, ...props }) => {
                const resolvedSrc = resolveImageUrl(src, owner, repo, defaultBranch);
                return (
                  <img
                    src={resolvedSrc}
                    alt={alt || ""}
                    {...props}
                    style={{ maxWidth: "100%", height: "auto" }}
                  />
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
}
