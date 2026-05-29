"""GitHub API服务"""
import httpx
import base64
from typing import Optional
from ..config import get_settings


class GitHubService:
    """GitHub API封装"""

    def __init__(self):
        self.base_url = "https://api.github.com"

    def _get_headers(self) -> dict:
        """动态获取请求头"""
        settings = get_settings()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        token = settings.github_token
        if token and token.strip():
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @property
    def rate_limit_info(self) -> dict:
        """返回当前速率限制信息"""
        settings = get_settings()
        if settings.github_token and settings.github_token.strip():
            return {"limit": 5000, "authenticated": True, "message": "已认证，5000次/小时"}
        return {"limit": 60, "authenticated": False, "message": "未认证，60次/小时（建议配置GITHUB_TOKEN）"}

    async def _request(self, endpoint: str) -> dict:
        """发送GitHub API请求"""
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            if response.status_code == 404:
                raise Exception("仓库不存在或为私有仓库")
            if response.status_code == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "0")
                if remaining == "0":
                    raise Exception("GitHub API请求频率超限，请稍后重试或配置GITHUB_TOKEN提高限额")
                raise Exception("GitHub API访问被拒绝")
            response.raise_for_status()
            return response.json()

    async def get_repo_info(self, owner: str, repo: str) -> dict:
        """获取仓库基础信息"""
        data = await self._request(f"/repos/{owner}/{repo}")
        return {
            "owner": owner,
            "repo": repo,
            "full_name": data.get("full_name", f"{owner}/{repo}"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "language": data.get("language"),
            "updated_at": data.get("updated_at"),
            "topics": data.get("topics", [])
        }

    async def get_readme(self, owner: str, repo: str) -> str:
        """获取README内容"""
        data = await self._request(f"/repos/{owner}/{repo}/readme")
        content = data.get("content", "")
        encoding = data.get("encoding", "base64")

        if encoding == "base64":
            content = base64.b64decode(content).decode("utf-8")

        return content

    async def get_languages(self, owner: str, repo: str) -> dict:
        """获取语言分布"""
        return await self._request(f"/repos/{owner}/{repo}/languages")

    async def get_topics(self, owner: str, repo: str) -> list[str]:
        """获取项目标签"""
        data = await self._request(f"/repos/{owner}/{repo}/topics")
        return data.get("names", [])

    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """获取文件内容"""
        try:
            data = await self._request(f"/repos/{owner}/{repo}/contents/{path}")
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8")
            return data.get("content")
        except Exception:
            return None


# 全局实例
github_service = GitHubService()
