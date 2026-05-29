"""FastAPI应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .api import analyze, health
from .services.github_service import github_service

settings = get_settings()

# 调试信息
print(f"[启动] GitHub Token: {'已配置' if settings.github_token and settings.github_token.strip() else '未配置'}")
print(f"[启动] GitHub API限制: {github_service.rate_limit_info['message']}")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="GitHub项目智能分析后端API"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(analyze.router)
app.include_router(health.router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs"
    }
