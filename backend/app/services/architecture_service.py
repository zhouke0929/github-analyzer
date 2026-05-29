"""技术架构分析服务"""
from collections import defaultdict
from .github_service import github_service
from .ai_service import ai_service


class ArchitectureService:
    """技术架构分析服务"""

    def __init__(self):
        self.github = github_service
        self.ai = ai_service

    async def analyze(self, owner: str, repo: str, mode: str = "basic") -> dict:
        """
        分析项目架构

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            mode: 分析深度 - "tree_only" | "basic" | "deep"

        Returns:
            架构分析结果
        """
        # 1. 获取默认分支
        default_branch = await self.github.get_default_branch(owner, repo)

        # 2. 获取目录树
        tree_data = await self.github.get_tree(owner, repo, default_branch)
        tree_items = tree_data.get("tree", [])

        if not tree_items:
            return {
                "tree": "无法获取目录结构",
                "summary": "该项目目录结构无法解析",
                "modules": [],
                "file_stats": {},
                "design_patterns": []
            }

        # 3. 生成目录树文本
        tree_text = self._generate_tree_text(tree_items)

        # 4. 统计文件信息
        file_stats = self._calculate_file_stats(tree_items)

        # 5. 根据模式进行分析
        if mode == "tree_only":
            # 仅目录结构
            return {
                "tree": tree_text,
                "summary": f"项目包含 {file_stats['total_files']} 个文件，{file_stats['total_dirs']} 个目录",
                "modules": [],
                "file_stats": file_stats,
                "design_patterns": []
            }

        # 6. 基础分析 - 识别模块
        modules = self._identify_modules(tree_items)

        if mode == "basic":
            # 基础分析 - 不返回summary，前端已通过其他方式展示
            return {
                "tree": tree_text,
                "summary": "",
                "modules": modules,
                "file_stats": file_stats,
                "design_patterns": []
            }

        # 7. 深度分析 - AI分析设计模式
        if mode == "deep":
            ai_analysis = await self._ai_analyzeArchitecture(tree_text, file_stats, modules)
            return {
                "tree": tree_text,
                "summary": ai_analysis.get("summary", ""),
                "modules": modules,
                "file_stats": file_stats,
                "design_patterns": ai_analysis.get("design_patterns", [])
            }

        # 默认返回基础分析
        return {
            "tree": tree_text,
            "summary": f"项目包含 {file_stats['total_files']} 个文件",
            "modules": modules,
            "file_stats": file_stats,
            "design_patterns": []
        }

    def _generate_tree_text(self, tree_items: list, max_depth: int = 3) -> str:
        """生成目录树文本"""
        # 构建树结构
        root = {"name": ".", "children": {}, "type": "tree"}

        for item in tree_items:
            path = item.get("path", "")
            item_type = item.get("type", "blob")
            parts = path.split("/")

            # 限制深度
            if len(parts) > max_depth:
                continue

            current = root
            for i, part in enumerate(parts):
                if part not in current["children"]:
                    current["children"][part] = {
                        "name": part,
                        "children": {},
                        "type": "tree" if i < len(parts) - 1 else item_type
                    }
                current = current["children"][part]

        # 生成文本
        lines = []
        self._build_tree_lines(root, lines, "", True)
        return "\n".join(lines)

    def _build_tree_lines(self, node: dict, lines: list, prefix: str, is_last: bool):
        """递归生成目录树行"""
        if node["name"] != ".":
            connector = "└── " if is_last else "├── "
            suffix = "/" if node["type"] == "tree" else ""
            lines.append(f"{prefix}{connector}{node['name']}{suffix}")

        children = list(node["children"].values())
        for i, child in enumerate(children):
            new_prefix = prefix + ("    " if is_last else "│   ") if node["name"] != "." else ""
            self._build_tree_lines(child, lines, new_prefix, i == len(children) - 1)

    def _calculate_file_stats(self, tree_items: list) -> dict:
        """计算文件统计信息"""
        stats = {
            "total_files": 0,
            "total_dirs": 0,
            "by_extension": defaultdict(int),
            "by_language": defaultdict(int)
        }

        # 语言映射
        ext_to_lang = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React JSX",
            ".tsx": "React TSX",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".h": "C/C++ Header",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".cs": "C#",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".less": "LESS",
            ".vue": "Vue",
            ".svelte": "Svelte",
            ".md": "Markdown",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".toml": "TOML",
            ".xml": "XML",
            ".sql": "SQL",
            ".sh": "Shell",
            ".bash": "Shell",
            ".dockerfile": "Docker",
        }

        for item in tree_items:
            item_type = item.get("type", "blob")
            path = item.get("path", "")

            if item_type == "tree":
                stats["total_dirs"] += 1
            else:
                stats["total_files"] += 1
                # 提取扩展名
                if "." in path:
                    ext = "." + path.split(".")[-1].lower()
                    stats["by_extension"][ext] += 1

                    # 映射到语言
                    lang = ext_to_lang.get(ext)
                    if lang:
                        stats["by_language"][lang] += 1

        # 转换为普通字典并排序
        stats["by_extension"] = dict(sorted(stats["by_extension"].items(), key=lambda x: x[1], reverse=True)[:10])
        stats["by_language"] = dict(sorted(stats["by_language"].items(), key=lambda x: x[1], reverse=True)[:10])

        return stats

    def _identify_modules(self, tree_items: list) -> list:
        """识别主要模块"""
        modules = []
        seen = set()

        # 常见的模块目录名
        module_patterns = {
            "src": "源代码目录",
            "lib": "库文件",
            "app": "应用代码",
            "components": "UI组件",
            "pages": "页面",
            "views": "视图",
            "routes": "路由",
            "api": "API接口",
            "services": "服务层",
            "models": "数据模型",
            "utils": "工具函数",
            "helpers": "辅助函数",
            "hooks": "React Hooks",
            "store": "状态管理",
            "config": "配置文件",
            "tests": "测试文件",
            "test": "测试文件",
            "__tests__": "测试文件",
            "spec": "测试文件",
            "docs": "文档",
            "scripts": "脚本",
            "public": "公共资源",
            "static": "静态资源",
            "assets": "资源文件",
            "images": "图片",
            "styles": "样式",
            "css": "样式",
            "fonts": "字体",
            "middleware": "中间件",
            "controllers": "控制器",
            "handlers": "处理器",
            "repositories": "数据仓库",
            "entities": "实体",
            "dto": "数据传输对象",
            "interfaces": "接口",
            "types": "类型定义",
            "constants": "常量",
            "migrations": "数据库迁移",
            "seeds": "数据填充",
            "fixtures": "测试数据",
            "plugins": "插件",
            "modules": "模块",
            "packages": "包",
            "internal": "内部代码",
            "cmd": "命令行",
            "pkg": "包",
        }

        for item in tree_items:
            if item.get("type") == "tree":
                path = item.get("path", "")
                parts = path.split("/")

                # 只分析前两级目录
                if len(parts) <= 2:
                    dir_name = parts[-1].lower()
                    if dir_name in module_patterns and dir_name not in seen:
                        seen.add(dir_name)
                        modules.append({
                            "name": parts[-1],
                            "path": path,
                            "description": module_patterns[dir_name]
                        })

        return modules[:15]  # 最多返回15个模块

    async def _ai_analyzeArchitecture(self, tree_text: str, file_stats: dict, modules: list) -> dict:
        """AI深度分析架构"""
        modules_desc = ", ".join([m["name"] for m in modules[:10]])
        languages_desc = ", ".join([f"{k}({v}个文件)" for k, v in list(file_stats.get("by_language", {}).items())[:5]])

        prompt = f"""分析以下项目的架构设计。

项目结构（部分）：
{tree_text[:2000]}

主要模块：{modules_desc}
主要语言：{languages_desc}

请分析并返回JSON格式：
{{
  "summary": "项目架构概述（100-200字）",
  "design_patterns": ["识别到的设计模式1", "设计模式2"],
  "architecture_style": "架构风格（如MVC、微服务、分层架构等）",
  "suggestions": ["改进建议1", "改进建议2"]
}}

只输出JSON，设计模式包括但不限于：MVC、MVVM、分层架构、微服务、事件驱动、插件化、组件化等。"""

        try:
            result = await self.ai.generate_json(prompt, max_tokens=1000)
            return result
        except Exception as e:
            print(f"[架构分析AI错误] {type(e).__name__}: {str(e)}")
            return {
                "summary": f"项目采用{len(modules)}个主要模块的组织方式",
                "design_patterns": [],
                "architecture_style": "未知",
                "suggestions": []
            }


# 全局实例
architecture_service = ArchitectureService()
