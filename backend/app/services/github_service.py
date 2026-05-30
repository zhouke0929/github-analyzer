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
            "updated_at": data.get("pushed_at") or data.get("updated_at"),
            "topics": data.get("topics", [])
        }

    async def get_readme(self, owner: str, repo: str) -> str:
        """获取README内容"""
        data = await self._request(f"/repos/{owner}/{repo}/readme")
        content = data.get("content", "")
        encoding = data.get("encoding", "base64")

        if encoding == "base64":
            content = base64.b64decode(content).decode("utf-8")

        # 将相对路径的图片链接转换为绝对路径
        content = self._fix_relative_urls(content, owner, repo)

        return content

    def _fix_relative_urls(self, content: str, owner: str, repo: str) -> str:
        """将相对路径的URL转换为绝对路径"""
        import re

        # GitHub raw内容的基础URL
        base_raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main"
        # GitHub仓库的基础URL
        base_repo_url = f"https://github.com/{owner}/{repo}"

        # 处理Markdown图片语法: ![alt](url)
        def replace_image_url(match):
            alt = match.group(1)
            url = match.group(2)

            # 如果已经是绝对路径，不处理
            if url.startswith("http://") or url.startswith("https://"):
                return match.group(0)

            # 相对路径转换为绝对路径
            if url.startswith("./"):
                url = url[2:]
            elif url.startswith("/"):
                url = url[1:]

            # 使用raw.githubusercontent.com来获取图片
            absolute_url = f"{base_raw_url}/{url}"
            return f"![{alt}]({absolute_url})"

        # 处理Markdown链接语法: [text](url)
        def replace_link_url(match):
            text = match.group(1)
            url = match.group(2)

            # 如果已经是绝对路径，不处理
            if url.startswith("http://") or url.startswith("https://"):
                return match.group(0)

            # 如果是锚点链接，不处理
            if url.startswith("#"):
                return match.group(0)

            # 相对路径转换为绝对路径
            if url.startswith("./"):
                url = url[2:]
            elif url.startswith("/"):
                url = url[1:]

            absolute_url = f"{base_repo_url}/{url}"
            return f"[{text}]({absolute_url})"

        # 处理HTML img标签: <img src="url">
        def replace_html_img(match):
            prefix = match.group(1)
            url = match.group(2)
            suffix = match.group(3)

            # 如果已经是绝对路径，不处理
            if url.startswith("http://") or url.startswith("https://"):
                return match.group(0)

            # 相对路径转换为绝对路径
            if url.startswith("./"):
                url = url[2:]
            elif url.startswith("/"):
                url = url[1:]

            absolute_url = f"{base_raw_url}/{url}"
            return f'{prefix}{absolute_url}{suffix}'

        # 应用替换
        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image_url, content)
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link_url, content)
        content = re.sub(r'(<img[^>]*src=["\'])([^"\']+)(["\'][^>]*>)', replace_html_img, content)

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

    async def get_tree(self, owner: str, repo: str, sha: str = "main") -> dict:
        """获取仓库目录树"""
        try:
            data = await self._request(f"/repos/{owner}/{repo}/git/trees/{sha}?recursive=1")
            return data
        except Exception:
            # 尝试master分支
            try:
                data = await self._request(f"/repos/{owner}/{repo}/git/trees/master?recursive=1")
                return data
            except Exception:
                return {"tree": []}

    async def get_default_branch(self, owner: str, repo: str) -> str:
        """获取默认分支名"""
        try:
            data = await self._request(f"/repos/{owner}/{repo}")
            return data.get("default_branch", "main")
        except Exception:
            return "main"

    async def get_issues(self, owner: str, repo: str, per_page: int = 100, state: str = "all") -> list:
        """获取Issues列表"""
        try:
            data = await self._request(f"/repos/{owner}/{repo}/issues?state={state}&per_page={per_page}&sort=created&direction=desc")
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[GitHub] 获取Issues失败: {e}")
            return []


# 全局实例
github_service = GitHubService()
