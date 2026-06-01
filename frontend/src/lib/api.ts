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
  status: string;
  repo_info: RepoInfo;
  summary: string;
  readme_cn: string;
  tech_stack: TechStack;
  architecture?: ArchitectureInfo;
  issues_analysis?: IssuesAnalysis;
  analysis_mode?: string;
  default_branch?: string;
}

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

async function request<T>(
  endpoint: string,
  options?: RequestInit & { signal?: AbortSignal }
): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    return await res.json();
  } catch (error) {
    // 如果是用户取消，返回特定错误
    if (error instanceof Error && error.name === 'AbortError') {
      return {
        code: -2,
        message: "请求已取消",
        data: null,
      };
    }
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
  repo_url: string;
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

// 问答相关接口

export interface QASession {
  session_id: string;
  analysis_id: string;
  owner: string;
  repo: string;
  created_at: string;
}

export interface QAMessage {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  references?: { file_path: string; content: string }[];
  tools_used?: string[];
  created_at: string;
}

export async function createQASession(
  analysisId: string
): Promise<ApiResponse<QASession>> {
  return request("/api/qa/sessions", {
    method: "POST",
    body: JSON.stringify({ analysis_id: analysisId }),
  });
}

export async function sendQAMessage(
  sessionId: string,
  message: string,
  signal?: AbortSignal
): Promise<ApiResponse<QAMessage>> {
  return request(`/api/qa/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ message }),
    signal,
  });
}

export async function getQAHistory(
  sessionId: string
): Promise<ApiResponse<{ session_id: string; messages: QAMessage[] }>> {
  return request(`/api/qa/sessions/${sessionId}/history`);
}

// 索引状态相关接口

export interface IndexProgress {
  status: "indexing" | "completed" | "failed";
  total: number;
  current: number;
  message: string;
}

export interface IndexStatus {
  owner: string;
  repo: string;
  is_indexed: boolean;
  collection_name: string;
  document_count: number;
  progress?: IndexProgress;
}

export async function getIndexStatus(
  owner: string,
  repo: string
): Promise<ApiResponse<IndexStatus>> {
  return request(`/api/qa/index-status/${owner}/${repo}`);
}

export async function reindexCode(
  owner: string,
  repo: string
): Promise<ApiResponse<{ owner: string; repo: string; status: string }>> {
  return request(`/api/qa/reindex/${owner}/${repo}`, {
    method: "POST",
  });
}

export async function cancelIndex(
  owner: string,
  repo: string
): Promise<ApiResponse<{ owner: string; repo: string; status: string }>> {
  return request(`/api/qa/cancel-index/${owner}/${repo}`, {
    method: "POST",
  });
}

// 系统配置相关接口

export interface APIKeyConfig {
  provider: string;
  api_key: string;
  base_url?: string;
  model?: string;
}

export interface ModelConfig {
  chat_model: string;
  embedding_model: string;
}

export interface StorageInfo {
  database: {
    path: string;
    size_bytes: number;
    size_mb: number;
  };
  chromadb: {
    path: string;
    size_bytes: number;
    size_mb: number;
  };
  total_size_mb: number;
  project_count: number;
}

export interface ProvidersData {
  providers: Record<string, {
    name: string;
    default_base_url: string;
    models: string[];
  }>;
  embedding_models: Record<string, {
    name: string;
    models: string[];
  }>;
}

export async function getProviders(): Promise<ApiResponse<ProvidersData>> {
  return request("/api/config/providers");
}

export async function getAPIKeys(): Promise<ApiResponse<Record<string, string>>> {
  return request("/api/config/keys");
}

export async function updateAPIKey(config: APIKeyConfig): Promise<ApiResponse<null>> {
  return request("/api/config/keys", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export async function testAPIKey(provider: string, apiKey: string, baseUrl?: string): Promise<ApiResponse<{ valid: boolean }>> {
  return request("/api/config/test", {
    method: "POST",
    body: JSON.stringify({ provider, api_key: apiKey, base_url: baseUrl }),
  });
}

export async function getStorageInfo(): Promise<ApiResponse<StorageInfo>> {
  return request("/api/config/storage");
}

export async function cleanupOldData(days: number = 30): Promise<ApiResponse<{ deleted_count: number }>> {
  return request(`/api/config/cleanup?days=${days}`, {
    method: "POST",
  });
}

export async function getModelConfig(): Promise<ApiResponse<ModelConfig & { ai_provider: string }>> {
  return request("/api/config/models");
}

export async function updateModelConfig(config: ModelConfig): Promise<ApiResponse<null>> {
  return request("/api/config/models", {
    method: "POST",
    body: JSON.stringify(config),
  });
}
