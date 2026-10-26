import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  DashboardSummary,
  Drug,
  EncounterDetail,
  EncounterSummary,
  ExamPayload,
  Icd10,
  Patient,
  PatientInput,
  PatientListResponse,
  ProcedureMaster,
} from "@/types";

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => (await api.get<DashboardSummary>("/dashboard/summary")).data,
    retry: false,
  });
}

export function usePatients(q: string) {
  return useQuery({
    queryKey: ["patients", { q }],
    queryFn: async () =>
      (await api.get<PatientListResponse>("/patients", { params: { q: q || undefined } })).data,
    placeholderData: keepPreviousData,
  });
}

export function usePatient(id: number) {
  return useQuery({
    queryKey: ["patients", id],
    queryFn: async () => (await api.get<Patient>(`/patients/${id}`)).data,
    enabled: Number.isFinite(id),
    retry: false,
  });
}

export function usePatientEncounters(id: number) {
  return useQuery({
    queryKey: ["patients", id, "encounters"],
    queryFn: async () => (await api.get<EncounterSummary[]>(`/patients/${id}/encounters`)).data,
    enabled: Number.isFinite(id),
  });
}

export function useCreatePatient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: PatientInput) => (await api.post<Patient>("/patients", input)).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["patients"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdatePatient(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: PatientInput) =>
      (await api.put<Patient>(`/patients/${id}`, input)).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["patients"] });
    },
  });
}

export function useCreateEncounter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: { patient_id: number; reason?: string }) =>
      (await api.post<EncounterDetail>("/encounters", input)).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["patients"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useEncounter(id: number) {
  return useQuery({
    queryKey: ["encounters", id],
    queryFn: async () => (await api.get<EncounterDetail>(`/encounters/${id}`)).data,
    enabled: Number.isFinite(id),
    retry: false,
  });
}

export function useSaveExam(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ExamPayload) =>
      (await api.post<EncounterDetail>(`/encounters/${id}/exam`, payload)).data,
    onSuccess: (data) => {
      queryClient.setQueryData(["encounters", id], data);
      void queryClient.invalidateQueries({ queryKey: ["patients"] });
    },
  });
}

export function useIcd10Search(q: string, limit = 20) {
  return useQuery({
    queryKey: ["icd10", q, limit],
    queryFn: async () =>
      (await api.get<Icd10[]>("/icd10", { params: { q: q || undefined, limit } })).data,
    placeholderData: keepPreviousData,
  });
}

export function useDrugSearch(q: string, limit = 20) {
  return useQuery({
    queryKey: ["drugs", q, limit],
    queryFn: async () =>
      (await api.get<Drug[]>("/drugs", { params: { q: q || undefined, limit } })).data,
    placeholderData: keepPreviousData,
  });
}

export function useProcedureSearch(q: string, limit = 20) {
  return useQuery({
    queryKey: ["procedures", q, limit],
    queryFn: async () =>
      (await api.get<ProcedureMaster[]>("/procedures", { params: { q: q || undefined, limit } }))
        .data,
    placeholderData: keepPreviousData,
  });
}
