"""项目管理API路由"""
import json
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..models.schemas import ApiResponse
from ..models.database import db

router = APIRouter(prefix="/api", tags=["项目管理"])


@router.get("/projects", response_model=ApiResponse)
async def get_projects(
    search: str = None,
    language: str = None,
    sort_by: str = "created_at",
    order: str = "desc"
):
    """获取已分析的项目列表"""
    try:
        # 获取所有已完成的项目
        projects = db.get_all_projects()

        # 解析数据
        result = []
        for project in projects:
            repo_info = json.loads(project["repo_info"]) if isinstance(project["repo_info"], str) else project.get("repo_info", {})
            tech_stack = json.loads(project["tech_stack"]) if isinstance(project["tech_stack"], str) else project.get("tech_stack", {})

            # 提取语言列表
            languages = [lang["name"] for lang in tech_stack.get("languages", [])]

            item = {
                "id": project["id"],
                "owner": project["owner"],
                "repo": project["repo_name"],
                "full_name": f"{project['owner']}/{project['repo_name']}",
                "description": repo_info.get("description", ""),
                "stars": repo_info.get("stars", 0),
                "forks": repo_info.get("forks", 0),
                "language": repo_info.get("language", ""),
                "languages": languages,
                "topics": repo_info.get("topics", []),
                "summary": project.get("summary", ""),
                "created_at": project["created_at"],
                "completed_at": project.get("completed_at", "")
            }
            result.append(item)

        # 筛选：搜索关键词
        if search:
            search_lower = search.lower()
            result = [
                r for r in result
                if search_lower in r["full_name"].lower()
                or search_lower in (r["description"] or "").lower()
                or search_lower in (r["summary"] or "").lower()
            ]

        # 筛选：编程语言
        if language:
            result = [
                r for r in result
                if language.lower() in [l.lower() for l in r["languages"]]
                or language.lower() == (r["language"] or "").lower()
            ]

        # 排序
        if sort_by == "stars":
            result.sort(key=lambda x: x["stars"], reverse=(order == "desc"))
        elif sort_by == "name":
            result.sort(key=lambda x: x["full_name"].lower(), reverse=(order == "desc"))
        else:  # created_at
            result.sort(key=lambda x: x["created_at"] or "", reverse=(order == "desc"))

        return ApiResponse(
            code=0,
            message="success",
            data={
                "total": len(result),
                "projects": result
            }
        )

    except Exception as e:
        import traceback
        print(f"[错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.get("/projects/{project_id}", response_model=ApiResponse)
async def get_project_detail(project_id: str):
    """获取项目详情"""
    try:
        project = db.get_analysis(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        if project["status"] != "completed":
            raise HTTPException(status_code=400, detail="项目分析未完成")

        # 解析JSON字段
        repo_info = json.loads(project["repo_info"]) if isinstance(project["repo_info"], str) else project["repo_info"]
        tech_stack = json.loads(project["tech_stack"]) if isinstance(project["tech_stack"], str) else project["tech_stack"]

        result = {
            "id": project["id"],
            "repo_info": repo_info,
            "summary": project["summary"],
            "readme_cn": project["readme_cn"],
            "tech_stack": tech_stack
        }

        # 架构分析
        architecture = project.get("architecture")
        if architecture:
            result["architecture"] = json.loads(architecture) if isinstance(architecture, str) else architecture

        # Issues分析
        issues_analysis = project.get("issues_analysis")
        if issues_analysis:
            result["issues_analysis"] = json.loads(issues_analysis) if isinstance(issues_analysis, str) else issues_analysis

        return ApiResponse(
            code=0,
            message="success",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {str(e)}")


@router.delete("/projects/{project_id}", response_model=ApiResponse)
async def delete_project(project_id: str):
    """删除项目"""
    try:
        project = db.get_analysis(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        success = db.delete_analysis(project_id)
        if success:
            return ApiResponse(
                code=0,
                message="项目已删除",
                data={"id": project_id}
            )
        else:
            raise HTTPException(status_code=500, detail="删除失败")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")


@router.post("/projects/{project_id}/reanalyze", response_model=ApiResponse)
async def reanalyze_project(project_id: str):
    """重新分析项目"""
    try:
        project = db.get_analysis(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        owner = project["owner"]
        repo = project["repo_name"]
        repo_url = project["repo_url"]

        # 删除旧记录（避免冗余）
        db.delete_analysis(project_id)
        print(f"[重新分析] 已删除旧记录: {project_id}")

        # 创建新的分析任务
        from ..services.github_service import github_service
        repo_info = await github_service.get_repo_info(owner, repo)

        new_id = uuid.uuid4().hex[:12]
        db.create_analysis(new_id, repo_url, owner, repo, repo_info)

        # 使用后台任务执行分析
        import asyncio
        import importlib
        analyze_module = importlib.import_module("app.api.analyze")
        asyncio.create_task(analyze_module.run_analysis(new_id, owner, repo, repo_info))

        print(f"[重新分析] 新任务已创建: {new_id}")

        return ApiResponse(
            code=0,
            message="重新分析任务已创建",
            data={
                "id": new_id,
                "status": "pending",
                "repo_info": repo_info
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"重新分析失败: {str(e)}")
