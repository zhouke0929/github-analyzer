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
): Promise<ApiResponse<{ id: string; status: string; repo_info: RepoInfo }>> {
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
