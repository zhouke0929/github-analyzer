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

# 索引进度跟踪（内存中）
_index_progress = {}  # {owner/repo: {"status": "indexing", "total": 50, "current": 10, "message": "正在获取文件..."}}


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

# 活跃的索引任务跟踪
_active_index_tasks = {}  # {owner/repo: asyncio.Task}


async def _index_code_background(owner: str, repo: str):
    """后台索引代码（优化速度 + 进度跟踪 + 可取消）"""
    import asyncio

    progress_key = f"{owner}/{repo}"

    # 检查是否已有索引任务在运行
    if progress_key in _active_index_tasks and not _active_index_tasks[progress_key].done():
        print(f"[QA] 索引任务已在运行: {owner}/{repo}")
        return

    try:
        collection_name = rag_service._get_collection_name(owner, repo)

        # 检查集合是否存在且有文档
        if rag_service._collection_exists(collection_name):
            try:
                import chromadb
                client = chromadb.PersistentClient(path=rag_service.persist_dir)
                collection = client.get_collection(collection_name)
                if collection.count() > 0:
                    print(f"[QA] 代码已索引: {owner}/{repo}, {collection.count()} 个文档")
                    _index_progress[progress_key] = {
                        "status": "completed",
                        "total": 0,
                        "current": 0,
                        "message": f"索引完成（{collection.count()} 个文档）"
                    }
                    return
                else:
                    print(f"[QA] 集合存在但无文档，重新索引: {owner}/{repo}")
            except Exception:
                pass

        from ..services.github_service import github_service

        # 更新进度：获取目录树
        _index_progress[progress_key] = {
            "status": "indexing",
            "total": 0,
            "current": 0,
            "message": "正在获取项目目录树..."
        }

        # 使用 asyncio.to_thread 避免阻塞事件循环
        tree_data = await github_service.get_tree(owner, repo)
        tree = tree_data.get("tree", [])

        # 筛选可索引文件（按优先级排序）
        code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".h"}
        doc_extensions = {".md", ".txt", ".rst", ".adoc"}
        supported_extensions = code_extensions | doc_extensions

        files_info = []

        for item in tree:
            if item.get("type") == "blob":
                path = item.get("path", "")
                ext = "." + path.split(".")[-1] if "." in path else ""
                if ext in supported_extensions:
                    # 优先级：代码文件 > 文档文件；src/ 目录 > 其他目录；短路径 > 长路径
                    priority = 0
                    if ext in code_extensions:
                        priority += 3  # 代码文件优先级更高
                    if "src/" in path or "lib/" in path:
                        priority += 1
                    if path.count("/") < 3:
                        priority += 1
                    # 跳过测试文件（降低优先级）
                    if any(t in path.lower() for t in ['test', 'spec', '__test', 'mock']):
                        priority -= 2
                    files_info.append((priority, path, ext))

        # 按优先级排序，取前 50 个
        files_info.sort(key=lambda x: -x[0])
        files_info = files_info[:50]

        total_files = len(files_info)
        print(f"[QA] 开始索引 {owner}/{repo}, 共 {total_files} 个文件")

        # 更新进度：开始获取文件
        _index_progress[progress_key] = {
            "status": "indexing",
            "total": total_files,
            "current": 0,
            "message": f"正在获取文件内容 (0/{total_files})..."
        }

        # 串行获取文件（避免并发导致的资源问题）
        code_files = []
        for i, (_, path, _) in enumerate(files_info):
            try:
                content = await github_service.get_file_content(owner, repo, path)
                if content and 50 < len(content) < 100000:  # 100KB 限制
                    code_files.append((path, content))

                # 更新进度
                _index_progress[progress_key] = {
                    "status": "indexing",
                    "total": total_files,
                    "current": i + 1,
                    "message": f"正在获取文件内容 ({i + 1}/{total_files})..."
                }
            except Exception as e:
                print(f"[QA] 获取文件失败 {path}: {e}")
                continue

        if code_files:
            # 更新进度：开始向量化
            _index_progress[progress_key] = {
                "status": "indexing",
                "total": total_files,
                "current": total_files,
                "message": f"正在向量化 {len(code_files)} 个文件..."
            }

            await rag_service.index_code(owner, repo, code_files)
            print(f"[QA] 代码索引完成: {owner}/{repo}, {len(code_files)} 个文件")

            # 更新进度：完成
            _index_progress[progress_key] = {
                "status": "completed",
                "total": total_files,
                "current": total_files,
                "message": f"索引完成（{len(code_files)} 个文件）"
            }
        else:
            print(f"[QA] 没有可索引的代码文件: {owner}/{repo}")
            _index_progress[progress_key] = {
                "status": "completed",
                "total": 0,
                "current": 0,
                "message": "没有可索引的代码文件"
            }

    except Exception as e:
        print(f"[QA] 后台索引失败: {type(e).__name__}: {str(e)}")
        _index_progress[progress_key] = {
            "status": "failed",
            "total": 0,
            "current": 0,
            "message": f"索引失败: {str(e)}"
        }


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

        # 在后台索引代码（检查是否已有任务在运行）
        import asyncio
        progress_key = f"{owner}/{repo}"

        # 检查索引状态，如果未完成则触发索引
        need_index = False
        collection_name = rag_service._get_collection_name(owner, repo)
        if not rag_service._collection_exists(collection_name):
            need_index = True
        else:
            try:
                import chromadb
                client = chromadb.PersistentClient(path=rag_service.persist_dir)
                collection = client.get_collection(collection_name)
                if collection.count() == 0:
                    need_index = True
            except Exception:
                need_index = True

        if need_index:
            if progress_key not in _active_index_tasks or _active_index_tasks[progress_key].done():
                _active_index_tasks[progress_key] = asyncio.create_task(
                    _index_code_background(owner, repo)
                )

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

        # 获取对话历史（在保存当前消息之前，最近 20 条）
        history_messages = db.get_qa_messages(session_id)
        history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history_messages[-20:]
        ]

        # 保存用户消息
        user_message_id = uuid.uuid4().hex[:12]
        db.create_qa_message(session_id, user_message_id, "user", request.message)

        # 运行 Agent（带对话历史）
        result = await agent_service.run(
            question=request.message,
            owner=owner,
            repo=repo,
            session_id=session_id,
            history=history
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


@router.get("/index-status/{owner}/{repo}", response_model=ApiResponse)
async def get_index_status(owner: str, repo: str):
    """查询代码索引状态

    Returns:
        索引状态信息，包括是否已索引、文档块数量、索引进度等
    """
    try:
        collection_name = rag_service._get_collection_name(owner, repo)
        is_indexed = rag_service._collection_exists(collection_name)

        result = {
            "owner": owner,
            "repo": repo,
            "is_indexed": is_indexed,
            "collection_name": collection_name
        }

        # 如果已索引，获取文档数量
        if is_indexed:
            try:
                import chromadb
                client = chromadb.PersistentClient(path=rag_service.persist_dir)
                collection = client.get_collection(collection_name)
                result["document_count"] = collection.count()
            except Exception:
                result["document_count"] = -1

        # 获取索引进度
        progress_key = f"{owner}/{repo}"
        if progress_key in _index_progress:
            result["progress"] = _index_progress[progress_key]
        else:
            result["progress"] = None

        return ApiResponse(
            code=0,
            message="success",
            data=result
        )

    except Exception as e:
        import traceback
        print(f"[错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"查询索引状态失败: {str(e)}")


@router.post("/reindex/{owner}/{repo}", response_model=ApiResponse)
async def reindex_code(owner: str, repo: str):
    """重新索引代码

    删除现有索引并重新建立索引
    """
    try:
        # 删除现有索引
        rag_service.delete_collection(owner, repo)

        # 重新索引
        await _index_code_background(owner, repo)

        return ApiResponse(
            code=0,
            message="重新索引已启动",
            data={
                "owner": owner,
                "repo": repo,
                "status": "indexing"
            }
        )

    except Exception as e:
        import traceback
        print(f"[错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"重新索引失败: {str(e)}")


@router.post("/cancel-index/{owner}/{repo}", response_model=ApiResponse)
async def cancel_index(owner: str, repo: str):
    """取消正在进行的索引任务"""
    try:
        progress_key = f"{owner}/{repo}"

        # 取消任务
        if progress_key in _active_index_tasks:
            task = _active_index_tasks[progress_key]
            if not task.done():
                task.cancel()
                print(f"[QA] 已取消索引任务: {owner}/{repo}")

            # 更新进度状态
            _index_progress[progress_key] = {
                "status": "failed",
                "total": 0,
                "current": 0,
                "message": "索引已取消"
            }

        return ApiResponse(
            code=0,
            message="索引任务已取消",
            data={
                "owner": owner,
                "repo": repo,
                "status": "cancelled"
            }
        )

    except Exception as e:
        import traceback
        print(f"[错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"取消索引失败: {str(e)}")
