"""系统配置API"""
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..config import get_settings

router = APIRouter(prefix="/api/config", tags=["系统配置"])


class APIKeyConfig(BaseModel):
    """API Key配置"""
    provider: str
    api_key: str
    base_url: str | None = None
    model: str | None = None


class ModelConfig(BaseModel):
    """模型配置"""
    chat_model: str
    embedding_model: str


class TestRequest(BaseModel):
    """测试请求"""
    provider: str
    api_key: str
    base_url: str | None = None


class FullConfigUpdate(BaseModel):
    """完整配置更新"""
    github_token: str | None = None
    chat_api_key: str | None = None
    chat_base_url: str | None = None
    chat_model: str | None = None
    embedding_api_key: str | None = None
    embedding_base_url: str | None = None
    embedding_model: str | None = None


# 支持的AI提供商
AI_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    },
    "dashscope": {
        "name": "通义千问",
        "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"],
    },
    "deepseek": {
        "name": "DeepSeek",
        "default_base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-coder"],
    },
    "claude": {
        "name": "Claude",
        "default_base_url": "https://api.anthropic.com/v1",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
    },
}

# Embedding模型选项
EMBEDDING_MODELS = {
    "dashscope": {
        "name": "DashScope Embedding",
        "models": ["text-embedding-v4", "text-embedding-v3"],
    },
    "openai": {
        "name": "OpenAI Embedding",
        "models": ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
    },
}


@router.get("/providers")
async def get_providers():
    """获取支持的AI提供商列表"""
    return {
        "code": 0,
        "message": "success",
        "data": {
            "providers": AI_PROVIDERS,
            "embedding_models": EMBEDDING_MODELS,
        }
    }


@router.post("/update")
async def update_full_config(config: FullConfigUpdate):
    """更新完整配置（写入.env文件）"""
    env_path = Path(__file__).parent.parent.parent / ".env"

    # 读取现有.env内容
    env_lines = []
    if env_path.exists():
        env_lines = env_path.read_text(encoding="utf-8").splitlines()

    # 构建更新映射
    updates = {}
    if config.github_token is not None and config.github_token:
        updates["GITHUB_TOKEN"] = config.github_token
    if config.chat_api_key is not None and config.chat_api_key:
        updates["OPENAI_API_KEY"] = config.chat_api_key
    if config.chat_base_url is not None and config.chat_base_url:
        updates["OPENAI_BASE_URL"] = config.chat_base_url
    if config.chat_model is not None and config.chat_model:
        updates["OPENAI_MODEL"] = config.chat_model
    if config.embedding_api_key is not None and config.embedding_api_key:
        updates["EMBEDDING_API_KEY"] = config.embedding_api_key
    if config.embedding_base_url is not None and config.embedding_base_url:
        updates["EMBEDDING_BASE_URL"] = config.embedding_base_url
    if config.embedding_model is not None and config.embedding_model:
        updates["EMBEDDING_MODEL"] = config.embedding_model

    if not updates:
        return {
            "code": 0,
            "message": "没有需要更新的配置",
            "data": None
        }

    # 更新.env行
    new_lines = []
    updated_keys = set()

    for line in env_lines:
        key = line.split("=")[0].strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    # 添加新的配置项
    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}")

    # 写入.env文件
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return {
        "code": 0,
        "message": "配置已保存，立即生效",
        "data": None
    }


@router.get("/keys")
async def get_api_keys():
    """获取当前API Key配置（脱敏）"""
    settings = get_settings()

    def mask_key(key: str) -> str:
        if not key or len(key) < 8:
            return "***未配置***"
        return key[:4] + "*" * (len(key) - 8) + key[-4:]

    return {
        "code": 0,
        "message": "success",
        "data": {
            "github_token": mask_key(settings.github_token),
            "openai_api_key": mask_key(settings.openai_api_key),
            "openai_base_url": settings.openai_base_url,
            "openai_model": settings.openai_model,
            "embedding_api_key": mask_key(settings.embedding_api_key),
            "embedding_base_url": settings.embedding_base_url,
            "embedding_model": settings.embedding_model,
            "claude_api_key": mask_key(settings.claude_api_key),
        }
    }


@router.post("/keys")
async def update_api_key(config: APIKeyConfig):
    """更新API Key配置（写入.env文件）"""
    env_path = Path(__file__).parent.parent.parent / ".env"

    # 读取现有.env内容
    env_lines = []
    if env_path.exists():
        env_lines = env_path.read_text(encoding="utf-8").splitlines()

    # 更新配置
    key_mapping = {
        "openai": {
            "OPENAI_API_KEY": config.api_key,
            "OPENAI_BASE_URL": config.base_url or "https://api.openai.com/v1",
            "OPENAI_MODEL": config.model or "gpt-4o-mini",
        },
        "dashscope": {
            "EMBEDDING_API_KEY": config.api_key,
            "EMBEDDING_BASE_URL": config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        },
        "claude": {
            "CLAUDE_API_KEY": config.api_key,
        },
    }

    updates = key_mapping.get(config.provider, {})
    if not updates:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {config.provider}")

    # 更新.env行
    new_lines = []
    updated_keys = set()

    for line in env_lines:
        key = line.split("=")[0].strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    # 添加新的配置项
    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}")

    # 写入.env文件
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return {
        "code": 0,
        "message": "配置已保存，立即生效",
        "data": None
    }


@router.post("/test")
async def test_api_key(request: TestRequest):
    """测试API Key是否有效"""
    import httpx

    test_urls = {
        "openai": f"{request.base_url or 'https://api.openai.com/v1'}/models",
        "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1/models",
        "claude": "https://api.anthropic.com/v1/messages",
    }

    url = test_urls.get(request.provider)
    if not url:
        raise HTTPException(status_code=400, detail=f"不支持的提供商: {request.provider}")

    headers = {"Authorization": f"Bearer {request.api_key}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                return {
                    "code": 0,
                    "message": "API Key有效",
                    "data": {"valid": True}
                }
            else:
                return {
                    "code": 0,
                    "message": f"API Key无效: HTTP {response.status_code}",
                    "data": {"valid": False}
                }
    except Exception as e:
        return {
            "code": 0,
            "message": f"测试失败: {str(e)}",
            "data": {"valid": False}
        }


@router.get("/storage")
async def get_storage_info():
    """获取存储信息"""
    data_dir = Path("./data")

    # SQLite数据库大小
    db_path = data_dir / "analyzer.db"
    db_size = db_path.stat().st_size if db_path.exists() else 0

    # ChromaDB数据大小
    chroma_dir = data_dir / "chroma"
    chroma_size = 0
    if chroma_dir.exists():
        for f in chroma_dir.rglob("*"):
            if f.is_file():
                chroma_size += f.stat().st_size

    # 分析记录数量
    from ..models.database import db
    projects = db.get_all_projects()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "database": {
                "path": str(db_path),
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024 * 1024), 2),
            },
            "chromadb": {
                "path": str(chroma_dir),
                "size_bytes": chroma_size,
                "size_mb": round(chroma_size / (1024 * 1024), 2),
            },
            "total_size_mb": round((db_size + chroma_size) / (1024 * 1024), 2),
            "project_count": len(projects),
        }
    }


@router.post("/cleanup")
async def cleanup_old_data(days: int = 30):
    """清理旧数据"""
    from ..models.database import db
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=days)

    # 获取要删除的项目
    conn = db._get_conn()
    try:
        rows = conn.execute(
            "SELECT id, owner, repo_name FROM analyses WHERE created_at < ?",
            (cutoff_date.isoformat(),)
        ).fetchall()

        deleted_count = 0
        for row in rows:
            analysis_id = row[0]
            owner = row[1]
            repo_name = row[2]

            # 删除ChromaDB数据
            try:
                import chromadb
                client = chromadb.PersistentClient(path="./data/chroma")
                collection_name = f"github_{owner}_{repo_name}"
                try:
                    client.delete_collection(collection_name)
                except Exception:
                    pass
            except Exception:
                pass

            # 删除数据库记录
            conn.execute("DELETE FROM qa_messages WHERE session_id IN (SELECT id FROM qa_sessions WHERE analysis_id = ?)", (analysis_id,))
            conn.execute("DELETE FROM qa_sessions WHERE analysis_id = ?", (analysis_id,))
            conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
            deleted_count += 1

        conn.commit()

        return {
            "code": 0,
            "message": f"已清理 {deleted_count} 个超过 {days} 天的项目",
            "data": {"deleted_count": deleted_count}
        }
    finally:
        conn.close()


@router.get("/models")
async def get_model_config():
    """获取当前模型配置"""
    settings = get_settings()
    return {
        "code": 0,
        "message": "success",
        "data": {
            "chat_model": settings.openai_model,
            "embedding_model": settings.embedding_model,
            "ai_provider": settings.default_ai_provider,
        }
    }


@router.post("/models")
async def update_model_config(config: ModelConfig):
    """更新模型配置"""
    env_path = Path(__file__).parent.parent.parent / ".env"

    # 读取现有.env内容
    env_lines = []
    if env_path.exists():
        env_lines = env_path.read_text(encoding="utf-8").splitlines()

    # 更新配置
    new_lines = []
    updated_keys = set()

    for line in env_lines:
        key = line.split("=")[0].strip()
        if key == "OPENAI_MODEL":
            new_lines.append(f"OPENAI_MODEL={config.chat_model}")
            updated_keys.add(key)
        elif key == "EMBEDDING_MODEL":
            new_lines.append(f"EMBEDDING_MODEL={config.embedding_model}")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    # 添加新的配置项
    if "OPENAI_MODEL" not in updated_keys:
        new_lines.append(f"OPENAI_MODEL={config.chat_model}")
    if "EMBEDDING_MODEL" not in updated_keys:
        new_lines.append(f"EMBEDDING_MODEL={config.embedding_model}")

    # 写入.env文件
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return {
        "code": 0,
        "message": "模型配置已更新，重启后端服务后生效",
        "data": None
    }
