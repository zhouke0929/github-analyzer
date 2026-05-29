"""项目摘要服务"""
from .ai_service import ai_service


SUMMARY_PROMPT = "你是一个技术项目分析专家。请用一句话概括项目核心价值。只输出摘要，15-30个汉字。"


class SummaryService:
    """摘要服务"""

    def __init__(self):
        self.ai = ai_service

    async def generate_summary(self, repo_info: dict, readme_content: str) -> str:
        """生成项目一句话摘要"""
        # 构建简洁的用户提示
        description = repo_info.get('description', '') or ''
        language = repo_info.get('language', '') or ''
        stars = repo_info.get('stars', 0)
        topics = ', '.join(repo_info.get('topics', [])[:5])

        user_prompt = f"项目：{repo_info.get('full_name', '')}，描述：{description}，语言：{language}，Star：{stars}，标签：{topics}"

        summary = await self.ai.generate_with_system(
            system_prompt=SUMMARY_PROMPT,
            user_prompt=user_prompt,
            max_tokens=200
        )

        # 清理可能的引号
        summary = summary.strip().strip('"').strip("'").strip("「」")

        return summary


# 全局实例
summary_service = SummaryService()
