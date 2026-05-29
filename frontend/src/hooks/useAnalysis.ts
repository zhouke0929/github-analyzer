"use client";

import { useState, useCallback, useRef } from "react";
import {
  startAnalysis,
  getAnalysisStatus,
  getAnalysisResult,
  type AnalysisResult,
  type AnalysisStatus,
  type RepoInfo,
} from "@/lib/api";

interface UseAnalysisReturn {
  isLoading: boolean;
  error: string | null;
  analysisId: string | null;
  repoInfo: RepoInfo | null;
  status: AnalysisStatus | null;
  result: AnalysisResult | null;
  startAnalysisJob: (url: string) => Promise<void>;
  reset: () => void;
}

// 轮询配置
const POLL_INTERVAL = 2000; // 2秒
const MAX_POLL_ERRORS = 5; // 最大连续错误次数
const MAX_POLL_DURATION = 300000; // 最大轮询时长 5分钟

export function useAnalysis(): UseAnalysisReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [repoInfo, setRepoInfo] = useState<RepoInfo | null>(null);
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const errorCountRef = useRef(0);
  const startTimeRef = useRef(0);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    errorCountRef.current = 0;
  }, []);

  const pollStatus = useCallback(
    (id: string) => {
      startTimeRef.current = Date.now();
      errorCountRef.current = 0;

      pollingRef.current = setInterval(async () => {
        // 检查轮询超时
        if (Date.now() - startTimeRef.current > MAX_POLL_DURATION) {
          stopPolling();
          setError("分析超时，请重试");
          setIsLoading(false);
          return;
        }

        try {
          const res = await getAnalysisStatus(id);

          if (res.code === 0 && res.data) {
            errorCountRef.current = 0; // 重置错误计数
            setStatus(res.data);

            if (res.data.status === "completed") {
              stopPolling();
              const resultRes = await getAnalysisResult(id);
              if (resultRes.code === 0 && resultRes.data) {
                setResult(resultRes.data);
                setIsLoading(false);
              } else {
                setError("获取分析结果失败");
                setIsLoading(false);
              }
            } else if (res.data.status === "failed") {
              stopPolling();
              setError("分析任务失败，请重试");
              setIsLoading(false);
            }
          } else {
            // API返回错误
            errorCountRef.current += 1;
            if (errorCountRef.current >= MAX_POLL_ERRORS) {
              stopPolling();
              setError("网络请求失败，请检查网络后重试");
              setIsLoading(false);
            }
          }
        } catch {
          // 网络异常
          errorCountRef.current += 1;
          if (errorCountRef.current >= MAX_POLL_ERRORS) {
            stopPolling();
            setError("网络连接异常，请检查后端服务是否运行");
            setIsLoading(false);
          }
        }
      }, POLL_INTERVAL);
    },
    [stopPolling]
  );

  const startAnalysisJob = useCallback(
    async (url: string) => {
      setIsLoading(true);
      setError(null);
      setResult(null);
      setStatus(null);
      setAnalysisId(null);
      setRepoInfo(null);
      stopPolling();

      try {
        const res = await startAnalysis(url);
        if (res.code === 0 && res.data) {
          setAnalysisId(res.data.id);
          setRepoInfo(res.data.repo_info);

          // 如果是已存在的项目，直接获取结果
          if (res.data.is_existing) {
            const resultRes = await getAnalysisResult(res.data.id);
            if (resultRes.code === 0 && resultRes.data) {
              setResult(resultRes.data);
              setIsLoading(false);
              return;
            }
          }

          pollStatus(res.data.id);
        } else {
          setError(res.message || "分析请求失败");
          setIsLoading(false);
        }
      } catch {
        setError("网络请求失败，请检查后端服务是否运行");
        setIsLoading(false);
      }
    },
    [pollStatus, stopPolling]
  );

  const reset = useCallback(() => {
    stopPolling();
    setIsLoading(false);
    setError(null);
    setAnalysisId(null);
    setRepoInfo(null);
    setStatus(null);
    setResult(null);
  }, [stopPolling]);

  return {
    isLoading,
    error,
    analysisId,
    repoInfo,
    status,
    result,
    startAnalysisJob,
    reset,
  };
}
