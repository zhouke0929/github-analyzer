"""项目摘要服务"""
from .ai_service import ai_service


class SummaryService:
    """摘要服务"""

    def __init__(self):
        self.ai = ai_service

    async def generate_summary(self, repo_info: dict, readme_content: str) -> str:
        """生成项目一句话摘要"""
        description = repo_info.get('description', '') or ''
        language = repo_info.get('language', '') or ''
        full_name = repo_info.get('full_name', '')

        # 如果有英文描述，调用AI生成中文摘要
        if description:
            system_prompt = "你是一个简洁的翻译助手。只输出翻译结果，不要输出任何思考过程、解释或分析。"
            prompt = f"将以下英文翻译成中文，15-30个汉字：{description}"
            try:
                summary = await self.ai.generate_with_system(system_prompt, prompt, max_tokens=100)
                # 清理可能的引号和空白
                summary = summary.strip().strip('"').strip("'").strip("「」").strip()
                if summary and len(summary) > 3:
                    return summary
            except Exception as e:
                print(f"[摘要错误] {type(e).__name__}: {str(e)}")

        # 后备方案：使用描述原文
        if description:
            return f"{language}项目：{description[:50]}"

        return f"{language}项目 - {full_name}"


# 全局实例
summary_service = SummaryService()
