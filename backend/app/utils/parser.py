"""URL解析工具"""
import re


def parse_github_url(url: str) -> tuple[str, str]:
    """解析GitHub URL，返回 (owner, repo)"""
    pattern = r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$'
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"无法解析GitHub URL: {url}")
    return match.group(1), match.group(2)
