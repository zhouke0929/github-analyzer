"""AI模型调用服务"""
from openai import AsyncOpenAI
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
        """生成文本"""
        client, model = self._get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3
        )
        return response.choices[0].message.content

    async def generate_with_system(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        """带系统提示的文本生成"""
        client, model = self._get_client()
        print(f"[AI调试] 模型: {model}")
        print(f"[AI调试] 系统提示前50字: {system_prompt[:50]}...")
        print(f"[AI调试] 用户提示前50字: {user_prompt[:50]}...")
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
        print(f"[AI调试] 响应内容: {repr(content)}")
        return content


# 全局实例
ai_service = AIService()
