"""技术栈分析服务"""
import json
import re
from .github_service import github_service
from .ai_service import ai_service


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

        # 4. 提取依赖名称
        deps_list = self._extract_dependencies(dependencies)

        # 5. 调用AI识别框架和工具
        frameworks, tools = await self._detect_with_ai(deps_list)

        return {
            "languages": languages,
            "frameworks": frameworks,
            "tools": tools
        }

    def _calculate_language_percentages(self, languages: dict) -> list:
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

        return result[:10]

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

    def _extract_dependencies(self, dependencies: dict) -> list:
        """从依赖文件中提取依赖名称和版本"""
        deps = []

        # 处理 package.json
        if "package.json" in dependencies:
            try:
                pkg = json.loads(dependencies["package.json"])
                for name, version in pkg.get("dependencies", {}).items():
                    deps.append({"name": name, "version": version, "type": "production"})
                for name, version in pkg.get("devDependencies", {}).items():
                    deps.append({"name": name, "version": version, "type": "dev"})
            except json.JSONDecodeError:
                pass

        # 处理 requirements.txt
        if "requirements.txt" in dependencies:
            for line in dependencies["requirements.txt"].split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    # 提取包名和版本
                    match = re.match(r'^([a-zA-Z0-9_-]+)\s*(.*)', line)
                    if match:
                        name = match.group(1)
                        version = match.group(2).strip()
                        deps.append({"name": name, "version": version, "type": "production"})

        # 处理 pyproject.toml
        if "pyproject.toml" in dependencies:
            content = dependencies["pyproject.toml"]
            in_deps = False
            for line in content.split('\n'):
                stripped = line.strip()
                if stripped.startswith('dependencies') and '=' in stripped:
                    in_deps = True
                    if '[' in stripped and ']' in stripped:
                        match = re.search(r'\[(.*?)\]', stripped)
                        if match:
                            for item in match.group(1).split(','):
                                item = item.strip().strip('"').strip("'")
                                if item:
                                    pkg_match = re.match(r'^([a-zA-Z0-9_-]+)\s*(.*)', item)
                                    if pkg_match:
                                        deps.append({"name": pkg_match.group(1), "version": pkg_match.group(2).strip(), "type": "production"})
                        in_deps = False
                    continue
                if in_deps:
                    if stripped.startswith(']'):
                        in_deps = False
                        continue
                    if stripped.startswith('"') or stripped.startswith("'"):
                        item = stripped.strip('"').strip("'").rstrip(',')
                        if item:
                            pkg_match = re.match(r'^([a-zA-Z0-9_-]+)\s*(.*)', item)
                            if pkg_match:
                                deps.append({"name": pkg_match.group(1), "version": pkg_match.group(2).strip(), "type": "production"})

        # 处理 go.mod
        if "go.mod" in dependencies:
            for line in dependencies["go.mod"].split("\n"):
                line = line.strip()
                if line.startswith("require"):
                    continue
                match = re.match(r'^([^\s]+)\s+(v[\d.]+)', line)
                if match:
                    deps.append({"name": match.group(1), "version": match.group(2), "type": "production"})

        # 去重并限制数量
        seen = set()
        unique_deps = []
        for dep in deps:
            key = dep["name"].lower()
            if key not in seen:
                seen.add(key)
                unique_deps.append(dep)

        return unique_deps[:50]  # 最多返回50个依赖

    async def _detect_with_ai(self, deps_list: list) -> tuple:
        """调用AI识别框架和工具"""
        if not deps_list:
            return [], []

        # 构建简洁的依赖列表文本
        deps_text = ", ".join([f"{d['name']}{d['version']}" for d in deps_list])

        prompt = f"""分析以下依赖列表，识别框架和工具。

依赖：{deps_text}

返回JSON格式：
{{"frameworks": [{{"name": "框架名", "version": "版本号", "category": "分类"}}], "tools": [{{"name": "工具名", "category": "分类"}}]}}

分类：前端框架、后端框架、全栈框架、模板引擎、ORM框架、数据验证、UI框架、测试框架、构建工具、代码规范、容器化、数据库、命令行工具、HTTP客户端、其他
只输出JSON，只返回主要的框架和工具。"""

        try:
            # 使用generate_json直接获取解析后的字典
            data = await self.ai.generate_json(prompt, max_tokens=500)
            if not data:
                # 后备：尝试用generate方法
                response = await self.ai.generate(prompt, max_tokens=500)
                if isinstance(response, dict):
                    data = response
                elif isinstance(response, str):
                    try:
                        data = json.loads(response)
                    except json.JSONDecodeError:
                        return [], []
            return data.get("frameworks", []), data.get("tools", [])
        except Exception as e:
            print(f"[技术栈AI分析错误] {type(e).__name__}: {str(e)}")
            return [], []


# 全局实例
tech_stack_service = TechStackService()
