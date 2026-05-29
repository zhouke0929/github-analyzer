"""Issues趋势分析服务"""
from collections import defaultdict
from datetime import datetime, timezone
from .github_service import github_service
from .ai_service import ai_service


class IssuesService:
    """Issues趋势分析服务"""

    def __init__(self):
        self.github = github_service
        self.ai = ai_service

    async def analyze(self, owner: str, repo: str, limit: int = 100) -> dict:
        """
        分析Issues趋势

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            limit: 获取的Issues数量

        Returns:
            Issues分析结果
        """
        # 1. 获取Issues列表
        issues = await self.github.get_issues(owner, repo, per_page=limit)

        if not issues:
            return {
                "total": 0,
                "open_count": 0,
                "closed_count": 0,
                "close_rate": 0,
                "avg_close_days": 0,
                "top_labels": [],
                "monthly_trend": [],
                "summary": "该项目暂无Issues数据"
            }

        # 2. 统计基础数据
        stats = self._calculate_stats(issues)

        # 3. 统计Labels分布
        top_labels = self._analyze_labels(issues)

        # 4. 计算月度趋势
        monthly_trend = self._calculate_monthly_trend(issues)

        # 5. AI生成分析摘要
        summary = await self._generate_summary(stats, top_labels, monthly_trend)

        return {
            "total": stats["total"],
            "open_count": stats["open_count"],
            "closed_count": stats["closed_count"],
            "close_rate": stats["close_rate"],
            "avg_close_days": stats["avg_close_days"],
            "top_labels": top_labels,
            "monthly_trend": monthly_trend,
            "summary": summary
        }

    def _calculate_stats(self, issues: list) -> dict:
        """计算基础统计数据"""
        total = len(issues)
        open_count = 0
        closed_count = 0
        close_times = []

        for issue in issues:
            state = issue.get("state", "")
            if state == "open":
                open_count += 1
            else:
                closed_count += 1
                # 计算关闭时间
                created_at = issue.get("created_at")
                closed_at = issue.get("closed_at")
                if created_at and closed_at:
                    try:
                        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        closed = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                        days = (closed - created).total_seconds() / 86400
                        if days > 0:
                            close_times.append(days)
                    except Exception:
                        pass

        close_rate = round(closed_count / total, 2) if total > 0 else 0
        avg_close_days = round(sum(close_times) / len(close_times), 1) if close_times else 0

        return {
            "total": total,
            "open_count": open_count,
            "closed_count": closed_count,
            "close_rate": close_rate,
            "avg_close_days": avg_close_days
        }

    def _analyze_labels(self, issues: list) -> list:
        """分析Labels分布"""
        label_counts = defaultdict(int)

        for issue in issues:
            labels = issue.get("labels", [])
            for label in labels:
                name = label.get("name", "") if isinstance(label, dict) else str(label)
                if name:
                    label_counts[name] += 1

        # 排序并返回前10个
        sorted_labels = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return [{"name": name, "count": count} for name, count in sorted_labels]

    def _calculate_monthly_trend(self, issues: list) -> list:
        """计算月度趋势"""
        monthly_data = defaultdict(lambda: {"created": 0, "closed": 0})

        for issue in issues:
            created_at = issue.get("created_at")
            if created_at:
                try:
                    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    month_key = created.strftime("%Y-%m")
                    monthly_data[month_key]["created"] += 1
                except Exception:
                    pass

            closed_at = issue.get("closed_at")
            if closed_at:
                try:
                    closed = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                    month_key = closed.strftime("%Y-%m")
                    monthly_data[month_key]["closed"] += 1
                except Exception:
                    pass

        # 转换为列表并排序
        trend = []
        for month in sorted(monthly_data.keys())[-6:]:  # 最近6个月
            data = monthly_data[month]
            trend.append({
                "month": month,
                "created": data["created"],
                "closed": data["closed"]
            })

        return trend

    async def _generate_summary(self, stats: dict, top_labels: list, monthly_trend: list) -> str:
        """生成分析摘要（手动构建，确保质量）"""
        # 过滤掉可能包含特殊字符的标签名
        def clean_label_name(name: str) -> str:
            # 只保留中文、英文、数字和常见标点
            import re
            cleaned = re.sub(r'[^一-龥a-zA-Z0-9\s\-_:/()]', '', name)
            return cleaned.strip() if cleaned else "未命名"

        labels_desc = ", ".join([f"{clean_label_name(l['name'])}({l['count']}个)" for l in top_labels[:5]]) if top_labels else "无标签"
        recent_created = sum(m["created"] for m in monthly_trend[-3:]) if monthly_trend else 0
        recent_closed = sum(m["closed"] for m in monthly_trend[-3:]) if monthly_trend else 0

        close_rate = round(stats['close_rate'] * 100)

        # 评估维护质量
        if close_rate >= 80:
            quality = "优秀"
            quality_desc = "项目维护团队响应迅速，Issues处理效率高"
        elif close_rate >= 60:
            quality = "良好"
            quality_desc = "项目维护较为及时，大部分Issues能得到处理"
        else:
            quality = "一般"
            quality_desc = "项目维护存在一定滞后，部分Issues未能及时处理"

        # 评估活跃度
        if stats['total'] >= 50:
            activity = "高"
            activity_desc = "社区参与度高，用户反馈活跃"
        elif stats['total'] >= 20:
            activity = "中等"
            activity_desc = "社区有一定参与度"
        else:
            activity = "较低"
            activity_desc = "社区参与度相对较低"

        # 构建摘要
        summary = f"该项目近3个月共有{stats['total']}个Issues，关闭率{close_rate}%，平均处理时间{stats['avg_close_days']}天，维护质量{quality}。{activity_desc}，{quality_desc}。主要问题类型包括{labels_desc}。"

        return summary

    def _format_number(self, num: int) -> str:
        """格式化数字"""
        if num >= 1000:
            return f"{num / 1000:.1f}k"
        return str(num)


# 全局实例
issues_service = IssuesService()
