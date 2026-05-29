"use client";

import { useState, type FormEvent } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { GitBranch, Loader2, Search } from "lucide-react";

interface UrlInputProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

export function UrlInput({ onSubmit, isLoading }: UrlInputProps) {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onSubmit(url.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto space-y-4">
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
          <GitBranch className="w-5 h-5" />
        </div>
        <Input
          type="url"
          placeholder="输入 GitHub 仓库地址，例如 https://github.com/facebook/react"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="pl-10 h-14 text-base bg-card border-border focus:ring-2 focus:ring-github/30"
          disabled={isLoading}
        />
      </div>
      <Button
        type="submit"
        disabled={!url.trim() || isLoading}
        className="w-full h-12 text-base font-medium bg-github hover:bg-github/90 text-github-foreground cursor-pointer transition-all duration-200"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            分析中...
          </>
        ) : (
          <>
            <Search className="w-5 h-5 mr-2" />
            开始分析
          </>
        )}
      </Button>
    </form>
  );
}
