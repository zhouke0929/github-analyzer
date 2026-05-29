const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export interface RepoInfo {
  owner: string;
  repo: string;
  full_name: string;
  description: string;
  stars: number;
  forks: number;
  language: string;
  updated_at: string;
  topics?: string[];
}

export interface TechStackItem {
  name: string;
  percentage?: number;
  version?: string;
  category?: string;
}

export interface TechStack {
  languages: TechStackItem[];
  frameworks: TechStackItem[];
  tools: TechStackItem[];
}

export interface AnalysisStep {
  name: string;
  label: string;
  status: "pending" | "processing" | "completed" | "failed";
}

export interface AnalysisProgress {
  total: number;
  completed: number;
  current_step: string;
  steps: AnalysisStep[];
}

export interface AnalysisStatus {
  id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress?: AnalysisProgress;
}

export interface ModuleInfo {
  name: string;
  path: string;
  description: string;
}

export interface FileStats {
  total_files: number;
  total_dirs: number;
  by_extension: Record<string, number>;
  by_language: Record<string, number>;
}

export interface ArchitectureInfo {
  tree: string;
  summary: string;
  modules: ModuleInfo[];
  file_stats: FileStats;
  design_patterns: string[];
}

export interface LabelInfo {
  name: string;
  count: number;
}

export interface MonthlyTrend {
  month: string;
  created: number;
  closed: number;
}

export interface IssuesAnalysis {
  total: number;
  open_count: number;
  closed_count: number;
  close_rate: number;
  avg_close_days: number;
  top_labels: LabelInfo[];
  monthly_trend: MonthlyTrend[];
  summary: string;
}

export interface AnalysisResult {
  id: string;
  repo_info: RepoInfo;
  summary: string;
  readme_cn: string;
  tech_stack: TechStack;
  architecture?: ArchitectureInfo;
  issues_analysis?: IssuesAnalysis;
  analysis_mode?: string;
}

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    return await res.json();
  } catch (error) {
    return {
      code: -1,
      message: error instanceof Error ? error.message : "网络请求失败",
      data: null,
    };
  }
}

export async function startAnalysis(
  url: string
): Promise<ApiResponse<{ id: string; status: string; repo_info: RepoInfo; is_existing?: boolean }>> {
  return request("/api/analyze", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export async function getAnalysisStatus(
  id: string
): Promise<ApiResponse<AnalysisStatus>> {
  return request(`/api/analyze/${id}/status`);
}

export async function getAnalysisResult(
  id: string
): Promise<ApiResponse<AnalysisResult>> {
  return request(`/api/analyze/${id}/result`);
}

export async function healthCheck(): Promise<{
  status: string;
  version: string;
}> {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

// 项目管理相关接口

export interface ProjectItem {
  id: string;
  owner: string;
  repo: string;
  full_name: string;
  description: string;
  stars: number;
  forks: number;
  language: string;
  languages: string[];
  topics: string[];
  summary: string;
  created_at: string;
  completed_at: string;
}

export interface ProjectsResponse {
  total: number;
  projects: ProjectItem[];
}

export async function getProjects(params?: {
  search?: string;
  language?: string;
  sort_by?: string;
  order?: string;
}): Promise<ApiResponse<ProjectsResponse>> {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.set("search", params.search);
  if (params?.language) searchParams.set("language", params.language);
  if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
  if (params?.order) searchParams.set("order", params.order);

  const query = searchParams.toString();
  return request(`/api/projects${query ? `?${query}` : ""}`);
}

export async function getProjectDetail(
  id: string
): Promise<ApiResponse<AnalysisResult>> {
  return request(`/api/projects/${id}`);
}

export async function deleteProject(
  id: string
): Promise<ApiResponse<{ id: string }>> {
  return request(`/api/projects/${id}`, {
    method: "DELETE",
  });
}

export async function reanalyzeProject(
  id: string
): Promise<ApiResponse<{ id: string; status: string; repo_info: RepoInfo }>> {
  return request(`/api/projects/${id}/reanalyze`, {
    method: "POST",
  });
}
