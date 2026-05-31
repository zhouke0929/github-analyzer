"""问答相关API路由"""
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..models.schemas import ApiResponse
from ..models.database import db
from ..services.agent_service import agent_service
from ..services.rag_service import rag_service

router = APIRouter(prefix="/api/qa", tags=["问答"])


# ===== 请求模型 =====

class CreateSessionRequest(BaseModel):
    """创建问答会话请求"""
    analysis_id: str


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    message: str


# ===== 响应模型 =====

class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    analysis_id: str
    created_at: str


class MessageResponse(BaseModel):
    """消息响应"""
    message_id: str
    role: str
    content: str
    references: list = []
    tools_used: list = []
    created_at: str


class HistoryResponse(BaseModel):
    """历史记录响应"""
    session_id: str
    messages: list


# ===== 后台任务 =====

async def _index_code_background(owner: str, repo: str):
    """后台索引代码"""
    try:
        collection_name = rag_service._get_collection_name(owner, repo)
        if rag_service._collection_exists(collection_name):
            print(f"[QA] 代码已索引: {owner}/{repo}")
            return

        from ..services.github_service import github_service

        tree_data = await github_service.get_tree(owner, repo)
        tree = tree_data.get("tree", [])

        code_files = []
        supported_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".h"}
        max_files = 50

        for item in tree:
            if len(code_files) >= max_files:
                break
            if item.get("type") == "blob":
                path = item.get("path", "")
                ext = "." + path.split(".")[-1] if "." in path else ""
                if ext in supported_extensions:
                    content = await github_service.get_file_content(owner, repo, path)
                    if content and len(content) > 50:
                        code_files.append((path, content))

        if code_files:
            await rag_service.index_code(owner, repo, code_files)
            print(f"[QA] 代码索引完成: {owner}/{repo}, {len(code_files)} 个文件")
    except Exception as e:
        print(f"[QA] 后台索引失败: {type(e).__name__}: {str(e)}")


# ===== API 路由 =====

@router.post("/sessions", response_model=ApiResponse)
async def create_session(request: CreateSessionRequest):
    """创建问答会话"""
    try:
        # 验证分析记录存在
        analysis = db.get_analysis(request.analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="分析记录不存在")

        if analysis["status"] != "completed":
            raise HTTPException(status_code=400, detail="分析尚未完成")

        # 创建会话记录
        session_id = uuid.uuid4().hex[:12]
        owner = analysis["owner"]
        repo = analysis["repo_name"]

        # 保存会话到数据库
        db.create_qa_session(session_id, request.analysis_id, owner, repo)

        # 在后台索引代码
        import asyncio
        asyncio.create_task(_index_code_background(owner, repo))

        return ApiResponse(
            code=0,
            message="问答会话已创建",
            data={
                "session_id": session_id,
                "analysis_id": request.analysis_id,
                "owner": owner,
                "repo": repo,
                "created_at": datetime.now().isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"创建问答会话失败: {str(e)}")


@router.post("/sessions/{session_id}/messages", response_model=ApiResponse)
async def send_message(session_id: str, request: SendMessageRequest):
    """发送问答消息"""
    try:
        # 获取会话信息
        session = db.get_qa_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        owner = session["owner"]
        repo = session["repo_name"]

        # 保存用户消息
        user_message_id = uuid.uuid4().hex[:12]
        db.create_qa_message(session_id, user_message_id, "user", request.message)

        # 运行 Agent
        result = await agent_service.run(
            question=request.message,
            owner=owner,
            repo=repo,
            session_id=session_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "问答失败"))

        # 保存助手消息
        assistant_message_id = uuid.uuid4().hex[:12]
        db.create_qa_message(
            session_id,
            assistant_message_id,
            "assistant",
            result.get("answer", ""),
            json.dumps(result.get("references", []), ensure_ascii=False),
            json.dumps(result.get("tools_used", []), ensure_ascii=False)
        )

        return ApiResponse(
            code=0,
            message="success",
            data={
                "message_id": assistant_message_id,
                "role": "assistant",
                "content": result.get("answer", ""),
                "references": result.get("references", []),
                "tools_used": result.get("tools_used", []),
                "created_at": datetime.now().isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@router.get("/sessions/{session_id}/history", response_model=ApiResponse)
async def get_history(session_id: str):
    """获取对话历史"""
    try:
        # 验证会话存在
        session = db.get_qa_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 获取消息历史
        messages = db.get_qa_messages(session_id)

        # 格式化消息
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "message_id": msg["id"],
                "role": msg["role"],
                "content": msg["content"],
                "created_at": msg["created_at"]
            }

            # 解析引用和工具
            if msg.get("code_references"):
                try:
                    formatted_msg["references"] = json.loads(msg["code_references"])
                except json.JSONDecodeError:
                    formatted_msg["references"] = []

            if msg.get("tools_used"):
                try:
                    formatted_msg["tools_used"] = json.loads(msg["tools_used"])
                except json.JSONDecodeError:
                    formatted_msg["tools_used"] = []

            formatted_messages.append(formatted_msg)

        return ApiResponse(
            code=0,
            message="success",
            data={
                "session_id": session_id,
                "messages": formatted_messages
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")
