"""Pydantic数据模型"""
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisMode(str, Enum):
    """分析模式"""
    QUICK = "quick"
    DEEP = "deep"


class ArchitectureMode(str, Enum):
    """架构分析深度"""
    TREE_ONLY = "tree_only"
    BASIC = "basic"
    DEEP = "deep"


# ===== 请求模型 =====

class AnalyzeRequest(BaseModel):
    """分析请求"""
    url: str

    @field_validator("url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        import re
        pattern = r'^https?://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$'
        if not re.match(pattern, v.rstrip('/')):
            raise ValueError('请输入有效的GitHub仓库URL')
        return v.rstrip('/')


# ===== 响应模型 =====

class RepoInfo(BaseModel):
    """仓库基础信息"""
    owner: str
    repo: str
    full_name: str
    description: Optional[str] = None
    stars: int = 0
    forks: int = 0
    language: Optional[str] = None
    updated_at: Optional[str] = None
    topics: list[str] = []


class AnalysisStep(BaseModel):
    """分析步骤"""
    name: str
    label: str
    status: StepStatus


class AnalysisProgress(BaseModel):
    """分析进度"""
    total: int = 3
    completed: int = 0
    current_step: str = ""
    steps: list[AnalysisStep] = []


class AnalyzeResponse(BaseModel):
    """分析响应"""
    id: str
    status: AnalysisStatus
    repo_info: RepoInfo


class AnalysisStatusResponse(BaseModel):
    """分析状态响应"""
    id: str
    status: AnalysisStatus
    progress: AnalysisProgress


class LanguageInfo(BaseModel):
    """语言信息"""
    name: str
    percentage: float


class FrameworkInfo(BaseModel):
    """框架信息"""
    name: str
    version: str
    category: str


class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    category: str


class TechStack(BaseModel):
    """技术栈"""
    languages: list[LanguageInfo] = []
    frameworks: list[FrameworkInfo] = []
    tools: list[ToolInfo] = []


class ModuleInfo(BaseModel):
    """模块信息"""
    name: str
    path: str
    description: str


class FileStats(BaseModel):
    """文件统计"""
    total_files: int = 0
    total_dirs: int = 0
    by_extension: dict = {}
    by_language: dict = {}


class ArchitectureInfo(BaseModel):
    """架构分析结果"""
    tree: str = ""
    summary: str = ""
    modules: list[ModuleInfo] = []
    file_stats: FileStats = FileStats()
    design_patterns: list[str] = []


class LabelInfo(BaseModel):
    """标签信息"""
    name: str
    count: int


class MonthlyTrend(BaseModel):
    """月度趋势"""
    month: str
    created: int
    closed: int


class IssuesAnalysis(BaseModel):
    """Issues分析结果"""
    total: int = 0
    open_count: int = 0
    closed_count: int = 0
    close_rate: float = 0
    avg_close_days: float = 0
    top_labels: list[LabelInfo] = []
    monthly_trend: list[MonthlyTrend] = []
    summary: str = ""


class AnalysisResult(BaseModel):
    """完整分析结果"""
    id: str
    repo_info: RepoInfo
    summary: str
    readme_cn: str
    tech_stack: TechStack
    architecture: Optional[ArchitectureInfo] = None
    issues_analysis: Optional[IssuesAnalysis] = None
    analysis_mode: str = "quick"


class ApiResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[dict] = None
