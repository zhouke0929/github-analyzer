"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Tag,
} from "lucide-react";
import type { IssuesAnalysis } from "@/lib/api";

interface IssuesAnalysisCardProps {
  issuesAnalysis: IssuesAnalysis;
}

function StatsOverview({ data }: { data: IssuesAnalysis }) {
  const closeRate = Math.round(data.close_rate * 100);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div className="p-4 bg-muted rounded-lg text-center">
        <p className="text-2xl font-bold text-github">{data.total}</p>
        <p className="text-sm text-muted-foreground">总Issues</p>
      </div>
      <div className="p-4 bg-muted rounded-lg text-center">
        <div className="flex items-center justify-center gap-1">
          <AlertCircle className="w-4 h-4 text-orange-500" />
          <p className="text-2xl font-bold text-orange-500">{data.open_count}</p>
        </div>
        <p className="text-sm text-muted-foreground">待处理</p>
      </div>
      <div className="p-4 bg-muted rounded-lg text-center">
        <div className="flex items-center justify-center gap-1">
          <CheckCircle2 className="w-4 h-4 text-green-500" />
          <p className="text-2xl font-bold text-green-500">{data.closed_count}</p>
        </div>
        <p className="text-sm text-muted-foreground">已关闭</p>
      </div>
      <div className="p-4 bg-muted rounded-lg text-center">
        <div className="flex items-center justify-center gap-1">
          <Clock className="w-4 h-4 text-blue-500" />
          <p className="text-2xl font-bold text-blue-500">{data.avg_close_days}天</p>
        </div>
        <p className="text-sm text-muted-foreground">平均处理</p>
      </div>
    </div>
  );
}

function CloseRateBar({ rate }: { rate: number }) {
  const percent = Math.round(rate * 100);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">关闭率</span>
        <span className="font-medium text-foreground">{percent}%</span>
      </div>
      <div className="h-3 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-green-500 transition-all duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

function LabelsList({ labels }: { labels: IssuesAnalysis["top_labels"] }) {
  if (labels.length === 0) return null;

  const colors = [
    "bg-blue-500",
    "bg-green-500",
    "bg-orange-500",
    "bg-purple-500",
    "bg-pink-500",
    "bg-teal-500",
    "bg-yellow-500",
    "bg-red-500",
    "bg-indigo-500",
    "bg-cyan-500",
  ];

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
        <Tag className="w-4 h-4" />
        主要标签
      </h4>
      <div className="flex flex-wrap gap-2">
        {labels.map((label, i) => (
          <Badge
            key={label.name}
            variant="secondary"
            className="text-sm py-1 px-3"
          >
            <span
              className={`w-2 h-2 rounded-full mr-2 ${colors[i % colors.length]}`}
            />
            {label.name}
            <span className="ml-1 text-muted-foreground">({label.count})</span>
          </Badge>
        ))}
      </div>
    </div>
  );
}

function MonthlyTrendView({
  trend,
}: {
  trend: IssuesAnalysis["monthly_trend"];
}) {
  if (trend.length === 0) return null;

  const maxVal = Math.max(
    ...trend.map((t) => Math.max(t.created, t.closed)),
    1
  );

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
        <TrendingUp className="w-4 h-4" />
        月度趋势
      </h4>
      <div className="space-y-2">
        {trend.map((month) => (
          <div key={month.month} className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-16 shrink-0">
              {month.month}
            </span>
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground w-8">新增</span>
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange-500 transition-all duration-500"
                    style={{
                      width: `${(month.created / maxVal) * 100}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-muted-foreground w-8 text-right">
                  {month.created}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground w-8">关闭</span>
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all duration-500"
                    style={{
                      width: `${(month.closed / maxVal) * 100}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-muted-foreground w-8 text-right">
                  {month.closed}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function IssuesAnalysisCard({
  issuesAnalysis,
}: IssuesAnalysisCardProps) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-github" />
          Issues 趋势分析
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 分析摘要 */}
        {issuesAnalysis.summary && (
          <div className="p-4 bg-muted rounded-lg">
            <p className="text-foreground leading-relaxed">
              {issuesAnalysis.summary}
            </p>
          </div>
        )}

        {/* 统计概览 */}
        <StatsOverview data={issuesAnalysis} />

        {/* 关闭率 */}
        <CloseRateBar rate={issuesAnalysis.close_rate} />

        {/* 标签分布 */}
        <LabelsList labels={issuesAnalysis.top_labels} />

        {/* 月度趋势 */}
        <MonthlyTrendView trend={issuesAnalysis.monthly_trend} />
      </CardContent>
    </Card>
  );
}
