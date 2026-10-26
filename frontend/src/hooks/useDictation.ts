import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { DictationJobStatus, DictationSample } from "@/types";

export function useDictationSamples() {
  return useQuery({
    queryKey: ["dictation-samples"],
    queryFn: async () => {
      const resp = await api.get<DictationSample[]>("/dictation/samples");
      return resp.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useUploadDictation(encounterId: number) {
  return useMutation({
    mutationFn: async ({
      file,
      filename = "recording.webm",
    }: {
      file: Blob | File;
      filename?: string;
    }) => {
      const formData = new FormData();
      formData.append("audio", file, filename);

      const resp = await api.post<{
        job_id: number;
        encounter_id: number;
        audio_id: number;
        status: string;
      }>(`/encounters/${encounterId}/dictation`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return resp.data;
    },
  });
}

export function useTriggerSampleDictation(encounterId: number) {
  return useMutation({
    mutationFn: async (sampleId: string) => {
      const resp = await api.post<{
        job_id: number;
        encounter_id: number;
        audio_id: number;
        status: string;
      }>(`/encounters/${encounterId}/dictation/sample/${sampleId}`);
      return resp.data;
    },
  });
}

export function useDictationJob(jobId: number | null) {
  return useQuery({
    queryKey: ["dictation-job", jobId],
    queryFn: async () => {
      if (!jobId) return null;
      const resp = await api.get<DictationJobStatus>(`/dictation-jobs/${jobId}`);
      return resp.data;
    },
    enabled: jobId !== null && jobId > 0,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 1500;
      if (data.status === "done" || data.status === "error") {
        return false;
      }
      return 1500; // Polling tiap 1,5 detik saat queued/processing sesuai spesifikasi
    },
  });
}
