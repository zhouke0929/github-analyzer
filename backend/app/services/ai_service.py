"""AI模型调用服务"""
from openai import AsyncOpenAI
import json
from ..config import get_settings


class AIService:
    """AI服务封装，支持OpenAI兼容接口"""

    def __init__(self):
        self._client = None
        self._model = None

    def _get_client(self) -> tuple[AsyncOpenAI, str]:
        """动态获取客户端和模型"""
        settings = get_settings()
        if self._client is None or self._model != settings.openai_model:
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
            self._model = settings.openai_model
        return self._client, self._model

    async def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """生成文本（JSON格式，适合结构化数据）"""
        client, model = self._get_client()

        json_prompt = f"""{prompt}

请以JSON格式返回结果，格式：{{"result": "你的回答"}}"""

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": json_prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        if content:
            try:
                data = json.loads(content)
                return data.get("result", content)
            except json.JSONDecodeError:
                return content

        return ""

    async def generate_raw(self, prompt: str, max_tokens: int = 4096) -> str:
        """生成原始文本（不强制JSON格式，适合翻译、摘要等需要自然文本的场景）"""
        client, model = self._get_client()

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3
        )

        message = response.choices[0].message

        # 优先返回content字段（最终答案）
        content = message.content
        if content and len(content.strip()) > 10:
            return content.strip()

        # 如果content为空或太短，检查是否有reasoning_content
        # 但不要返回思考过程，而是返回空字符串让调用方使用后备方案
        if hasattr(message, 'reasoning_content') and message.reasoning_content:
            # reasoning_content是思考过程，不应该作为最终答案返回
            # 但如果content确实为空，尝试从reasoning中提取关键信息
            pass

        return content.strip() if content else ""

    async def generate_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        """生成并解析JSON（适合需要结构化返回的场景）"""
        client, model = self._get_client()

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {}
        return {}

    async def generate_with_system(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        """带系统提示的文本生成（JSON格式）"""
        client, model = self._get_client()

        json_user_prompt = f"""{user_prompt}

请以JSON格式返回结果，格式：{{"result": "你的回答"}}"""

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json_user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        if content:
            try:
                data = json.loads(content)
                return data.get("result", content)
            except json.JSONDecodeError:
                return content

        return ""

    async def generate_with_system_raw(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        """带系统提示的原始文本生成（不强制JSON格式）"""
        client, model = self._get_client()

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )

        content = response.choices[0].message.content
        if content:
            return content.strip()

        return ""


# 全局实例
ai_service = AIService()
