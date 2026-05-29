"""README翻译服务"""
import re
from .ai_service import ai_service


class TranslateService:
    """翻译服务"""

    def __init__(self):
        self.ai = ai_service

    async def translate_readme(self, content: str) -> str:
        """翻译README内容"""
        # 1. 预处理：提取代码块
        code_blocks, processed_content = self._extract_code_blocks(content)

        # 2. 翻译 - 使用generate_raw方法，不强制JSON格式
        prompt = f"""你是一个专业的技术文档翻译专家。请将以下Markdown格式的README内容翻译成中文。

翻译要求：
1. 保留所有Markdown格式（标题、列表、代码块、链接等）
2. 代码块内容不翻译（```内的代码保持原样）
3. 链接URL保持不变
4. 图片链接保持不变
5. 技术术语首次出现时保留英文，格式：「中文翻译（English）」
6. 翻译要自然流畅，符合中文表达习惯
7. 只输出翻译后的内容，不要添加任何解释或JSON包装

待翻译内容：
{processed_content}"""

        translated = await self.ai.generate_raw(prompt, max_tokens=8192)

        # 3. 后处理：还原代码块
        result = self._restore_code_blocks(translated, code_blocks)

        return result

    def _extract_code_blocks(self, content: str) -> tuple[list[str], str]:
        """提取代码块，用占位符替换"""
        code_blocks = []
        pattern = r'```[\s\S]*?```'

        def replace(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks)-1}__"

        processed = re.sub(pattern, replace, content)
        return code_blocks, processed

    def _restore_code_blocks(self, content: str, code_blocks: list[str]) -> str:
        """还原代码块"""
        for i, block in enumerate(code_blocks):
            content = content.replace(f"__CODE_BLOCK_{i}__", block)
        return content


# 全局实例
translate_service = TranslateService()
