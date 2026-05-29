"""健康检查API"""
from datetime import datetime
from fastapi import APIRouter
from ..config import get_settings
from ..services.github_service import github_service

router = APIRouter(tags=["健康检查"])


@router.get("/api/health")
async def health_check():
    """健康检查"""
    settings = get_settings()
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "github_api": github_service.rate_limit_info
    }
