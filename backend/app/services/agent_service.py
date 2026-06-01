"""Agent 服务 - 基于 LangGraph 的代码智能问答"""
import json
from typing import Optional, Literal
from pydantic import BaseModel as PydanticBaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
import operator
from ..config import get_settings
from .rag_service import rag_service
from .github_service import github_service
from ..models.database import db


# ===== 状态定义 =====

class AgentState(TypedDict):
    """Agent 工作流状态"""
    question: str
    owner: str
    repo: str
    analysis_data: dict
    conversation_history: list[dict]
    intent: str
    tool_results: str
    answer: str
    tools_used: list[str]
    error: Optional[str]


# ===== 意图分类模型 =====

class RouteIntent(PydanticBaseModel):
    """用户意图分类"""
    intent: Literal["code_search", "find_definition", "semantic_search", "project_overview"]
    reasoning: str


# ===== LLM 工具函数 =====

def _get_llm():
    """获取 LLM 模型实例"""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_base_url,
        temperature=0.3
    )


def _keyword_classify_intent(question: str) -> str:
    """基于关键词的意图分类"""
    question_lower = question.lower()

    # 概览类 - 优先级最高（项目级别的问题）
    overview_keywords = ["整体", "架构", "技术栈", "用了什么", "概览", "概述", "介绍",
                         "核心功能", "主要功能", "做什么", "干什么", "用途", "作用",
                         "overview", "architecture", "tech stack", "project", "purpose"]
    if any(kw in question_lower for kw in overview_keywords):
        return "project_overview"

    # 定义查找类 - 需要更精确匹配
    definition_patterns = ["在哪里定义", "定义在哪", "定义位置", "哪个文件定义",
                           "哪里定义", "哪个文件", "定义在",
                           "where is.*defined", "definition of"]
    import re
    if any(re.search(p, question_lower) for p in definition_patterns):
        return "find_definition"

    # "是什么" 只有在问具体符号时才算定义查找
    if "是什么" in question_lower or "什么是" in question_lower:
        # 如果问题很短（可能是问具体符号），算定义查找
        # 如果问题较长（可能是问项目功能），算概览
        if len(question) < 15:
            return "find_definition"
        else:
            return "project_overview"

    # 语义理解类
    semantic_keywords = ["怎么实现", "怎么用", "为什么", "如何", "设计", "原理", "机制",
                         "功能", "how", "why", "implement", "design", "work", "feature"]
    if any(kw in question_lower for kw in semantic_keywords):
        return "semantic_search"

    # 代码搜索类
    code_keywords = ["方法", "函数", "类", "变量", "代码", "搜索", "查找",
                     "function", "method", "class", "variable", "search", "find"]
    if any(kw in question_lower for kw in code_keywords):
        return "code_search"

    # 默认：语义搜索
    return "semantic_search"


# ===== 图节点 =====

async def intent_router(state: AgentState) -> dict:
    """意图识别节点 - 根据问题类型路由到对应处理"""
    question = state["question"]

    # 构建对话历史上下文（用于理解指代关系）
    context_question = question
    if state.get("conversation_history"):
        recent = state["conversation_history"][-4:]
        if recent:
            # 如果问题很短（可能有指代），加上历史上下文
            if len(question) < 15:
                last_exchange = recent[-1] if recent else None
                if last_exchange and last_exchange.get("role") == "user":
                    context_question = f"（上一个问题：{last_exchange['content']}）{question}"

    # 使用关键词分类（对 mimo-v2.5 模型更可靠）
    intent = _keyword_classify_intent(context_question)

    print(f"[Agent] 意图识别: '{question}' -> {intent}")
    return {"intent": intent}


async def code_search_node(state: AgentState) -> dict:
    """精确代码搜索节点"""
    try:
        results = await github_service.search_code(
            state["owner"], state["repo"], state["question"]
        )

        if not results:
            return {
                "tool_results": f"没有找到包含 '{state['question']}' 的代码",
                "tools_used": ["search_code"]
            }

        formatted = []
        for i, item in enumerate(results[:5], 1):
            file_path = item.get('path', 'unknown')
            line_num = item.get('line_number', '')
            language = item.get('language', '')
            content = item.get('content', '')
            location = f"`{file_path}:{line_num}`" if line_num else f"`{file_path}`"
            formatted.append(f"**结果 {i}** - {location}\n```{language}\n{content}\n```")

        return {
            "tool_results": f"找到 {len(results)} 个匹配结果（显示前5个）：\n\n" + "\n\n".join(formatted),
            "tools_used": ["search_code"]
        }
    except Exception as e:
        return {
            "tool_results": f"代码搜索失败: {str(e)}",
            "tools_used": ["search_code"],
            "error": str(e)
        }


async def find_definition_node(state: AgentState) -> dict:
    """定义查找节点"""
    try:
        question = state["question"]
        # 从问题中提取符号名
        symbol = question
        for prefix in ["查找", "找", "搜索", "查看", "where", "find", "locate"]:
            symbol = symbol.replace(prefix, "")
        for suffix in ["的定义", "在哪里", "定义在哪", "是什么", "定义位置", "defined", "definition"]:
            symbol = symbol.replace(suffix, "")
        symbol = symbol.strip()

        if not symbol:
            symbol = question

        # 优先级搜索模式
        patterns = [
            f"class {symbol}",
            f"def {symbol}",
            f"function {symbol}",
            f"const {symbol} =",
        ]

        all_results = []
        for pattern in patterns:
            results = await github_service.search_code(state["owner"], state["repo"], pattern)
            if results:
                all_results.extend(results)
                if len(all_results) >= 5:
                    break

        if not all_results:
            # 回退到普通搜索
            all_results = await github_service.search_code(
                state["owner"], state["repo"], symbol
            )

        if not all_results:
            return {
                "tool_results": f"没有找到 '{symbol}' 的定义",
                "tools_used": ["find_definition"]
            }

        # 排序：优先非测试文件，优先浅路径
        def score(item):
            path = item.get('path', '')
            is_test = any(t in path.lower() for t in ['test', 'spec', '__test', 'mock'])
            depth = path.count('/')
            return (1 if is_test else 0, depth)

        all_results.sort(key=score)

        formatted = []
        for i, item in enumerate(all_results[:3], 1):
            file_path = item.get('path', 'unknown')
            line_num = item.get('line_number', '')
            language = item.get('language', '')
            content = item.get('content', '')
            location = f"`{file_path}:{line_num}`" if line_num else f"`{file_path}`"
            formatted.append(f"**定义 {i}** - {location}\n```{language}\n{content}\n```")

        return {
            "tool_results": f"找到 '{symbol}' 的定义：\n\n" + "\n\n".join(formatted),
            "tools_used": ["find_definition"]
        }
    except Exception as e:
        return {
            "tool_results": f"查找定义失败: {str(e)}",
            "tools_used": ["find_definition"],
            "error": str(e)
        }


async def semantic_search_node(state: AgentState) -> dict:
    """语义搜索节点"""
    try:
        results = await rag_service.search(
            state["question"], state["owner"], state["repo"], k=5
        )

        if not results:
            return {
                "tool_results": "没有找到相关的代码。可能是代码索引尚未完成，请稍后重试。",
                "tools_used": ["semantic_search"]
            }

        formatted = []
        for i, item in enumerate(results, 1):
            file_path = item.get('file_path', 'unknown')
            content = item.get('content', '')
            preview = content[:300] + "..." if len(content) > 300 else content
            formatted.append(f"**相关代码 {i}** - `{file_path}`\n```\n{preview}\n```")

        return {
            "tool_results": f"找到 {len(results)} 处相关代码：\n\n" + "\n\n".join(formatted),
            "tools_used": ["semantic_search"]
        }
    except Exception as e:
        return {
            "tool_results": f"语义搜索失败: {str(e)}",
            "tools_used": ["semantic_search"],
            "error": str(e)
        }


async def project_overview_node(state: AgentState) -> dict:
    """项目概览节点"""
    try:
        analysis_data = state.get("analysis_data", {})
        if not analysis_data:
            return {
                "tool_results": "没有找到项目的分析数据",
                "tools_used": ["get_project_overview"]
            }

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
            for mod in modules[:5]:
                result += f"- {mod.get('name', '')}: {mod.get('description', '')}\n"

        return {
            "tool_results": result,
            "tools_used": ["get_project_overview"]
        }
    except Exception as e:
        return {
            "tool_results": f"获取项目概览失败: {str(e)}",
            "tools_used": ["get_project_overview"],
            "error": str(e)
        }


async def generate_answer(state: AgentState) -> dict:
    """生成最终回答节点"""
    try:
        llm = _get_llm()

        # 构建对话历史消息
        history_messages = []
        if state.get("conversation_history"):
            for msg in state["conversation_history"][-6:]:
                if msg["role"] == "user":
                    history_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    history_messages.append(AIMessage(content=msg["content"]))

        system_prompt = f"""你是 {state['owner']}/{state['repo']} 项目的代码问答助手。

## 回答规范
1. 使用中文回答，专业术语可保留英文
2. 涉及代码时必须标注文件路径，格式：`文件路径` 或 `文件路径:行号`
3. 用代码块引用关键代码
4. 先给出简洁结论，再用代码支撑论点"""

        user_prompt = f"""基于以下工具检索结果回答用户问题。

工具检索结果：
{state['tool_results']}

用户问题：{state['question']}"""

        messages = [SystemMessage(content=system_prompt)] + history_messages + [HumanMessage(content=user_prompt)]
        response = await llm.ainvoke(messages)

        return {"answer": response.content}
    except Exception as e:
        return {"answer": f"生成回答失败: {str(e)}", "error": str(e)}


# ===== Agent 服务类 =====

class AgentService:
    """Agent 服务（基于 LangGraph）"""

    def __init__(self):
        self._graph = None

    def _build_graph(self):
        """构建 LangGraph 工作流"""
        if self._graph is not None:
            return self._graph

        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("intent_router", intent_router)
        workflow.add_node("code_search", code_search_node)
        workflow.add_node("find_definition", find_definition_node)
        workflow.add_node("semantic_search", semantic_search_node)
        workflow.add_node("project_overview", project_overview_node)
        workflow.add_node("generate_answer", generate_answer)

        # 条件路由：从意图识别到对应处理节点
        workflow.add_conditional_edges(
            "intent_router",
            lambda state: state["intent"],
            {
                "code_search": "code_search",
                "find_definition": "find_definition",
                "semantic_search": "semantic_search",
                "project_overview": "project_overview",
            }
        )

        # 所有处理节点流向生成回答
        workflow.add_edge(START, "intent_router")
        workflow.add_edge("code_search", "generate_answer")
        workflow.add_edge("find_definition", "generate_answer")
        workflow.add_edge("semantic_search", "generate_answer")
        workflow.add_edge("project_overview", "generate_answer")
        workflow.add_edge("generate_answer", END)

        self._graph = workflow.compile()
        return self._graph

    async def run(self, question: str, owner: str, repo: str,
                  session_id: Optional[str] = None,
                  history: Optional[list] = None) -> dict:
        """运行 Agent

        Args:
            question: 用户问题
            owner: 仓库所有者
            repo: 仓库名称
            session_id: 会话 ID（可选）
            history: 对话历史（可选）

        Returns:
            包含回答、使用工具等信息的字典
        """
        try:
            # 获取分析数据
            analysis_data = db.get_analysis_by_repo(owner, repo)
            if not analysis_data:
                return {"success": False, "error": "项目未分析，请先分析项目"}

            # 解析分析数据
            tech_stack = json.loads(analysis_data.get("tech_stack", "{}")) if isinstance(
                analysis_data.get("tech_stack"), str) else analysis_data.get("tech_stack", {})
            architecture = json.loads(analysis_data.get("architecture", "{}")) if isinstance(
                analysis_data.get("architecture"), str) else analysis_data.get("architecture", {})

            analysis_result = {
                "summary": analysis_data.get("summary", ""),
                "tech_stack": tech_stack,
                "architecture": architecture
            }

            # 构建初始状态
            initial_state: AgentState = {
                "question": question,
                "owner": owner,
                "repo": repo,
                "analysis_data": analysis_result,
                "conversation_history": history or [],
                "intent": "",
                "tool_results": "",
                "answer": "",
                "tools_used": [],
                "error": None
            }

            # 运行图
            graph = self._build_graph()
            result = await graph.ainvoke(initial_state)

            return {
                "success": True,
                "answer": result.get("answer", ""),
                "tools_used": result.get("tools_used", []),
                "references": []
            }

        except Exception as e:
            print(f"[Agent] 运行失败: {type(e).__name__}: {str(e)}")
            return {"success": False, "error": f"问答失败: {str(e)}"}


# 全局实例
agent_service = AgentService()
