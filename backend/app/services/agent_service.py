"""Agent 服务 - 代码智能问答"""
import json
from typing import Optional
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from ..config import get_settings
from .rag_service import rag_service
from .github_service import github_service
from ..models.database import db


class AgentService:
    """Agent 服务（基于 LangChain v1）"""

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        """懒加载 LLM 模型"""
        if self._llm is None:
            settings = get_settings()
            self._llm = ChatOpenAI(
                model=settings.openai_model,
                openai_api_key=settings.openai_api_key,
                openai_api_base=settings.openai_base_url,
                temperature=0.3
            )
        return self._llm

    def _create_tools(self, owner: str, repo: str, analysis_data: dict):
        """创建工具列表"""

        @tool
        def search_code(query: str) -> str:
            """在代码库中精确搜索关键词、函数名、变量名。返回匹配的代码片段和文件路径。"""
            try:
                # 使用 GitHub API 搜索代码
                import asyncio
                loop = asyncio.get_event_loop()
                results = loop.run_until_complete(
                    github_service.search_code(owner, repo, query)
                )

                if not results:
                    return f"没有找到包含 '{query}' 的代码"

                # 格式化结果
                formatted = []
                for item in results[:5]:  # 限制返回前5个结果
                    formatted.append(
                        f"文件: {item.get('path', 'unknown')}\n"
                        f"```{item.get('language', '')}\n{item.get('content', '')}\n```"
                    )

                return "\n\n".join(formatted)

            except Exception as e:
                return f"搜索失败: {str(e)}"

        @tool
        def find_definition(symbol: str) -> str:
            """查找函数、类、变量的定义位置。返回定义所在的文件和代码。"""
            try:
                # 使用 GitHub API 搜索定义
                import asyncio
                loop = asyncio.get_event_loop()
                results = loop.run_until_complete(
                    github_service.search_code(owner, repo, f"def {symbol}")
                )

                if not results:
                    # 尝试搜索类定义
                    results = loop.run_until_complete(
                        github_service.search_code(owner, repo, f"class {symbol}")
                    )

                if not results:
                    return f"没有找到 '{symbol}' 的定义"

                # 格式化结果
                formatted = []
                for item in results[:3]:  # 限制返回前3个结果
                    formatted.append(
                        f"文件: {item.get('path', 'unknown')}\n"
                        f"```{item.get('language', '')}\n{item.get('content', '')}\n```"
                    )

                return "\n\n".join(formatted)

            except Exception as e:
                return f"查找定义失败: {str(e)}"

        @tool
        def semantic_search(question: str) -> str:
            """语义搜索，理解自然语言问题并检索相关代码。用于回答关于功能、架构、设计的问题。"""
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                results = loop.run_until_complete(
                    rag_service.search(question, owner, repo, k=5)
                )

                if not results:
                    return "没有找到相关的代码"

                # 格式化结果
                formatted = []
                for item in results:
                    formatted.append(
                        f"文件: {item.get('file_path', 'unknown')}\n"
                        f"```\n{item.get('content', '')}\n```"
                    )

                return "\n\n".join(formatted)

            except Exception as e:
                return f"语义搜索失败: {str(e)}"

        @tool
        def get_project_overview() -> str:
            """获取项目整体概览，包括技术栈、架构、摘要等信息。"""
            try:
                if not analysis_data:
                    return "没有找到项目的分析数据"

                # 提取关键信息
                summary = analysis_data.get("summary", "暂无摘要")
                tech_stack = analysis_data.get("tech_stack", {})
                architecture = analysis_data.get("architecture", {})

                # 格式化技术栈
                languages = tech_stack.get("languages", [])
                frameworks = tech_stack.get("frameworks", [])
                tools_list = tech_stack.get("tools", [])

                tech_info = []
                if languages:
                    tech_info.append(f"编程语言: {', '.join([l.get('name', '') for l in languages])}")
                if frameworks:
                    tech_info.append(f"框架: {', '.join([f.get('name', '') for f in frameworks])}")
                if tools_list:
                    tech_info.append(f"工具: {', '.join([t.get('name', '') for t in tools_list])}")

                # 格式化架构信息
                arch_summary = architecture.get("summary", "")
                modules = architecture.get("modules", [])

                result = f"## 项目概览\n\n{summary}\n\n"
                result += f"## 技术栈\n\n{chr(10).join(tech_info)}\n\n"

                if arch_summary:
                    result += f"## 架构\n\n{arch_summary}\n\n"

                if modules:
                    result += "## 主要模块\n\n"
                    for mod in modules[:5]:  # 限制显示前5个模块
                        result += f"- {mod.get('name', '')}: {mod.get('description', '')}\n"

                return result

            except Exception as e:
                return f"获取项目概览失败: {str(e)}"

        return [search_code, find_definition, semantic_search, get_project_overview]

    async def run(self, question: str, owner: str, repo: str, session_id: Optional[str] = None) -> dict:
        """运行 Agent

        Args:
            question: 用户问题
            owner: 仓库所有者
            repo: 仓库名称
            session_id: 会话 ID（可选）

        Returns:
            包含回答、引用、使用工具等信息的字典
        """
        try:
            # 获取分析数据
            analysis_data = db.get_analysis_by_repo(owner, repo)
            if not analysis_data:
                return {
                    "success": False,
                    "error": "项目未分析，请先分析项目"
                }

            # 解析分析数据
            tech_stack = json.loads(analysis_data.get("tech_stack", "{}")) if isinstance(analysis_data.get("tech_stack"), str) else analysis_data.get("tech_stack", {})
            architecture = json.loads(analysis_data.get("architecture", "{}")) if isinstance(analysis_data.get("architecture"), str) else analysis_data.get("architecture", {})

            analysis_result = {
                "summary": analysis_data.get("summary", ""),
                "tech_stack": tech_stack,
                "architecture": architecture
            }

            # 创建工具
            tools = self._create_tools(owner, repo, analysis_result)

            # 创建 Agent
            agent = create_agent(
                model=self.llm,
                tools=tools,
                system_prompt=f"""你是一个代码问答助手，帮助用户理解和分析 {owner}/{repo} 项目。

你可以使用以下工具：
1. search_code - 在代码库中精确搜索关键词、函数名、变量名
2. find_definition - 查找函数、类、变量的定义位置
3. semantic_search - 语义搜索，理解自然语言问题并检索相关代码
4. get_project_overview - 获取项目整体概览

请用中文回答用户的问题。如果需要查找代码，请使用相应的工具。回答时请引用相关的代码片段和文件路径。"""
            )

            # 运行 Agent
            result = agent.invoke({
                "messages": [HumanMessage(content=question)]
            })

            # 提取回答
            answer = ""
            tools_used = []
            references = []

            for message in result.get("messages", []):
                if isinstance(message, AIMessage):
                    answer = message.content
                elif hasattr(message, "tool_calls"):
                    for tool_call in message.tool_calls:
                        tools_used.append(tool_call.get("name", ""))

            return {
                "success": True,
                "answer": answer,
                "tools_used": list(set(tools_used)),
                "references": references
            }

        except Exception as e:
            print(f"[Agent] 运行失败: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": f"问答失败: {str(e)}"
            }


# 全局实例
agent_service = AgentService()
