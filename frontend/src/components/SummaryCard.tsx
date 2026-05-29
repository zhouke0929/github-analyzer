import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Star, GitFork, Code2, Calendar } from "lucide-react";
import type { RepoInfo } from "@/lib/api";

interface SummaryCardProps {
  repoInfo: RepoInfo;
  summary: string;
}

function formatNumber(num: number): string {
  if (num >= 1000) {
    return (num / 1000).toFixed(1).replace(/\.0$/, "") + "k";
  }
  return num.toString();
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function SummaryCard({ repoInfo, summary }: SummaryCardProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="space-y-1">
            <CardTitle className="text-xl">{repoInfo.full_name}</CardTitle>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {repoInfo.description}
            </p>
          </div>
          {repoInfo.language && (
            <Badge variant="secondary" className="shrink-0">
              <Code2 className="w-3 h-3 mr-1" />
              {repoInfo.language}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="p-4 bg-github/5 border border-github/20 rounded-lg">
          <p className="text-base font-medium text-foreground">{summary}</p>
        </div>
        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <Star className="w-4 h-4" />
            <span>{formatNumber(repoInfo.stars)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <GitFork className="w-4 h-4" />
            <span>{formatNumber(repoInfo.forks)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Calendar className="w-4 h-4" />
            <span>更新于 {formatDate(repoInfo.updated_at)}</span>
          </div>
        </div>
        {repoInfo.topics && repoInfo.topics.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {repoInfo.topics.map((topic) => (
              <Badge key={topic} variant="outline" className="text-xs">
                {topic}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
