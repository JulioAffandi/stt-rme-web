import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { PipelineLogsListResponse, PipelineMetricsSummary } from "@/types";

export function usePipelineLogs(limit = 50, offset = 0) {
  return useQuery({
    queryKey: ["pipeline-logs", limit, offset],
    queryFn: async () => {
      const resp = await api.get<PipelineLogsListResponse>("/pipeline-logs", {
        params: { limit, offset },
      });
      return resp.data;
    },
  });
}

export function usePipelineMetrics() {
  return useQuery({
    queryKey: ["pipeline-metrics"],
    queryFn: async () => {
      const resp = await api.get<PipelineMetricsSummary>("/pipeline-logs/metrics");
      return resp.data;
    },
  });
}

export function useRunEvaluation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const resp = await api.post<{
        message: string;
        evaluated: number;
        results: Array<{
          title: string;
          wer: number | null;
          soap_f1: number | null;
          ner_f1: number | null;
          latency_ms: Record<string, number>;
        }>;
      }>("/evaluation/run");
      return resp.data;
    },
    onSuccess: () => {
      // Invalidate queries agar tabel dan metrik langsung ter-refresh otomatis
      queryClient.invalidateQueries({ queryKey: ["pipeline-logs"] });
      queryClient.invalidateQueries({ queryKey: ["pipeline-metrics"] });
    },
  });
}
