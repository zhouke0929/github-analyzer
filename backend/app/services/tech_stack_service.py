"""技术栈分析服务"""
import json
from .github_service import github_service
from .ai_service import ai_service


FRAMEWORK_MAP = {
    # JavaScript/TypeScript
    "react": ("React", "前端框架"),
    "vue": ("Vue.js", "前端框架"),
    "next": ("Next.js", "全栈框架"),
    "nuxt": ("Nuxt.js", "全栈框架"),
    "angular": ("Angular", "前端框架"),
    "svelte": ("Svelte", "前端框架"),
    "express": ("Express", "后端框架"),
    "koa": ("Koa", "后端框架"),
    "fastify": ("Fastify", "后端框架"),
    "nestjs": ("NestJS", "后端框架"),
    # Python
    "fastapi": ("FastAPI", "后端框架"),
    "django": ("Django", "后端框架"),
    "flask": ("Flask", "后端框架"),
    "tornado": ("Tornado", "后端框架"),
    # Go
    "gin": ("Gin", "后端框架"),
    "echo": ("Echo", "后端框架"),
    "fiber": ("Fiber", "后端框架"),
    # Java
    "spring-boot": ("Spring Boot", "后端框架"),
    "spring": ("Spring", "后端框架"),
}

TOOL_MAP = {
    # 测试
    "jest": ("Jest", "测试框架"),
    "mocha": ("Mocha", "测试框架"),
    "pytest": ("Pytest", "测试框架"),
    "vitest": ("Vitest", "测试框架"),
    "cypress": ("Cypress", "测试框架"),
    # 构建
    "webpack": ("Webpack", "构建工具"),
    "vite": ("Vite", "构建工具"),
    "rollup": ("Rollup", "构建工具"),
    "esbuild": ("ESBuild", "构建工具"),
    "turbo": ("Turborepo", "构建工具"),
    # 代码规范
    "eslint": ("ESLint", "代码规范"),
    "prettier": ("Prettier", "代码规范"),
    "black": ("Black", "代码规范"),
    "ruff": ("Ruff", "代码规范"),
    # 容器化
    "docker": ("Docker", "容器化"),
    "kubernetes": ("Kubernetes", "容器编排"),
}

ANALYSIS_PROMPT = """你是一个技术栈分析专家。请分析以下项目的依赖信息，提取出框架和工具。

请以JSON格式返回，格式如下：
{
  "frameworks": [{"name": "框架名", "version": "版本号", "category": "分类"}],
  "tools": [{"name": "工具名", "category": "分类"}]
}

分类说明：
- 框架分类：前端框架、后端框架、全栈框架、移动端框架
- 工具分类：测试框架、构建工具、代码规范、容器化、数据库、其他

只输出JSON，不要添加其他内容。"""


class TechStackService:
    """技术栈分析服务"""

    def __init__(self):
        self.github = github_service
        self.ai = ai_service

    async def analyze(self, owner: str, repo: str) -> dict:
        """分析项目技术栈"""
        # 1. 获取语言分布
        languages_raw = await self.github.get_languages(owner, repo)

        # 2. 获取依赖文件
        dependencies = await self._get_dependencies(owner, repo)

        # 3. 计算语言百分比
        languages = self._calculate_language_percentages(languages_raw)

        # 4. 识别框架和工具
        frameworks, tools = self._detect_from_dependencies(dependencies)

        return {
            "languages": languages,
            "frameworks": frameworks,
            "tools": tools
        }

    def _calculate_language_percentages(self, languages: dict) -> list[dict]:
        """计算语言百分比"""
        if not languages:
            return []

        total = sum(languages.values())
        if total == 0:
            return []

        result = []
        for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            percentage = round((bytes_count / total) * 100, 1)
            result.append({"name": lang, "percentage": percentage})

        return result[:10]  # 最多返回10种语言

    async def _get_dependencies(self, owner: str, repo: str) -> dict:
        """获取依赖文件内容"""
        result = {}
        dep_files = [
            "package.json", "requirements.txt", "Pipfile",
            "pyproject.toml", "go.mod", "Cargo.toml",
            "pom.xml", "build.gradle", "Gemfile"
        ]

        for file in dep_files:
            content = await self.github.get_file_content(owner, repo, file)
            if content:
                result[file] = content

        return result

    def _detect_from_dependencies(self, dependencies: dict) -> tuple[list[dict], list[dict]]:
        """从依赖文件中检测框架和工具"""
        frameworks = []
        tools = []

        # 处理 package.json
        if "package.json" in dependencies:
            try:
                pkg = json.loads(dependencies["package.json"])
                deps = {}
                deps.update(pkg.get("dependencies", {}))
                deps.update(pkg.get("devDependencies", {}))

                for pkg_name, version in deps.items():
                    pkg_lower = pkg_name.lower()
                    if pkg_lower in FRAMEWORK_MAP:
                        name, category = FRAMEWORK_MAP[pkg_lower]
                        frameworks.append({
                            "name": name,
                            "version": version.lstrip("^~>="),
                            "category": category
                        })
                    elif pkg_lower in TOOL_MAP:
                        name, category = TOOL_MAP[pkg_lower]
                        tools.append({"name": name, "category": category})
            except json.JSONDecodeError:
                pass

        # 处理 requirements.txt
        if "requirements.txt" in dependencies:
            content = dependencies["requirements.txt"]
            for line in content.split("\n"):
                line = line.strip().split("==")[0].split(">=")[0].split("<=")[0].strip().lower()
                if line in FRAMEWORK_MAP:
                    name, category = FRAMEWORK_MAP[line]
                    frameworks.append({"name": name, "version": "", "category": category})
                elif line in TOOL_MAP:
                    name, category = TOOL_MAP[line]
                    tools.append({"name": name, "category": category})

        # 去重
        frameworks = list({f["name"]: f for f in frameworks}.values())
        tools = list({t["name"]: t for t in tools}.values())

        return frameworks, tools


# 全局实例
tech_stack_service = TechStackService()
