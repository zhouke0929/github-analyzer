"""分析相关API路由"""
import uuid
import asyncio
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..models.schemas import (
    AnalyzeRequest, AnalyzeResponse, AnalysisStatusResponse,
    AnalysisResult, ApiResponse, RepoInfo, AnalysisProgress,
    AnalysisStep, TechStack
)
from ..models.database import db
from ..utils.parser import parse_github_url
from ..services.github_service import github_service
from ..services.translate_service import translate_service
from ..services.summary_service import summary_service
from ..services.tech_stack_service import tech_stack_service

router = APIRouter(prefix="/api", tags=["分析"])


async def run_analysis(analysis_id: str, owner: str, repo: str, repo_info: dict):
    """后台执行分析任务"""
    try:
        print(f"[分析] 开始分析 {owner}/{repo}，ID: {analysis_id}")

        # 更新状态为处理中
        db.update_status(analysis_id, "processing")

        # 并发执行三个分析任务
        print(f"[分析] 获取README和分析技术栈...")
        readme_task = github_service.get_readme(owner, repo)
        tech_stack_task = tech_stack_service.analyze(owner, repo)

        # 等待获取README
        readme_content = await readme_task
        print(f"[分析] README获取成功，长度: {len(readme_content)}")

        # 翻译和摘要依赖README，并发执行
        print(f"[分析] 开始翻译和生成摘要...")
        translate_task = translate_service.translate_readme(readme_content)
        summary_task = summary_service.generate_summary(repo_info, readme_content)

        # 等待所有任务完成
        readme_cn, summary, tech_stack = await asyncio.gather(
            translate_task,
            summary_task,
            tech_stack_task
        )

        print(f"[分析] 翻译完成，长度: {len(readme_cn)}")
        print(f"[分析] 摘要: {summary}")
        print(f"[分析] 技术栈: {len(tech_stack.get('languages', []))} 种语言")

        # 保存结果
        db.update_result(
            analysis_id,
            readme_cn=readme_cn,
            summary=summary,
            tech_stack=tech_stack
        )

        # 更新状态为完成
        db.update_status(analysis_id, "completed")
        print(f"[分析] 分析完成: {analysis_id}")

    except Exception as e:
        import traceback
        print(f"[分析错误] {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        # 更新状态为失败
        db.update_status(analysis_id, "failed", str(e))


@router.post("/analyze", response_model=ApiResponse)
async def create_analysis(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """发起分析任务"""
    try:
        # 解析URL
        owner, repo = parse_github_url(request.url)

        # 获取仓库基础信息
        repo_info = await github_service.get_repo_info(owner, repo)

        # 生成任务ID
        analysis_id = uuid.uuid4().hex[:12]

        # 创建数据库记录
        db.create_analysis(analysis_id, request.url, owner, repo, repo_info)

        # 启动后台任务
        background_tasks.add_task(run_analysis, analysis_id, owner, repo, repo_info)

        return ApiResponse(
            code=0,
            message="分析任务已创建",
            data={
                "id": analysis_id,
                "status": "pending",
                "repo_info": repo_info
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"[错误] {type(e).__name__}: {error_msg}")
        traceback.print_exc()
        if "不存在" in error_msg or "私有" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=500, detail=f"创建分析任务失败: {error_msg}")


@router.get("/analyze/{analysis_id}/status", response_model=ApiResponse)
async def get_analysis_status(analysis_id: str):
    """查询分析状态"""
    record = db.get_analysis(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="分析任务不存在")

    status = record["status"]

    # 构建进度信息
    steps = [
        {"name": "readme_translate", "label": "翻译README"},
        {"name": "summary", "label": "生成摘要"},
        {"name": "tech_stack", "label": "技术栈分析"}
    ]

    # 根据状态计算进度
    if status == "pending":
        completed = 0
        current_step = "等待开始"
        step_status = ["pending", "pending", "pending"]
    elif status == "processing":
        completed = 1
        current_step = "分析进行中"
        step_status = ["processing", "pending", "pending"]
    elif status == "completed":
        completed = 3
        current_step = "分析完成"
        step_status = ["completed", "completed", "completed"]
    else:  # failed
        completed = 0
        current_step = record.get("error_message", "分析失败")
        step_status = ["failed", "failed", "failed"]

    progress = AnalysisProgress(
        total=3,
        completed=completed,
        current_step=current_step,
        steps=[
            AnalysisStep(name=s["name"], label=s["label"], status=st)
            for s, st in zip(steps, step_status)
        ]
    )

    return ApiResponse(
        code=0,
        message="success",
        data={
            "id": analysis_id,
            "status": status,
            "progress": progress.model_dump()
        }
    )


@router.get("/analyze/{analysis_id}/result", response_model=ApiResponse)
async def get_analysis_result(analysis_id: str):
    """获取完整分析结果"""
    record = db.get_analysis(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="分析任务不存在")

    if record["status"] != "completed":
        raise HTTPException(status_code=400, detail="分析尚未完成")

    # 解析JSON字段
    repo_info = json.loads(record["repo_info"]) if isinstance(record["repo_info"], str) else record["repo_info"]
    tech_stack = json.loads(record["tech_stack"]) if isinstance(record["tech_stack"], str) else record["tech_stack"]

    result = {
        "id": analysis_id,
        "repo_info": repo_info,
        "summary": record["summary"],
        "readme_cn": record["readme_cn"],
        "tech_stack": tech_stack
    }

    return ApiResponse(
        code=0,
        message="success",
        data=result
    )
