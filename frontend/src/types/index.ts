export type Role = "doctor" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface HealthInfo {
  status: string;
  app: string;
  nlp_engine: string;
}

export interface ApiErrorBody {
  detail: string;
  code?: string;
}

export type Gender = "M" | "F";
export type DataSource = "manual" | "ai";

export interface Patient {
  id: number;
  medical_record_no: string;
  full_name: string;
  birth_date: string;
  gender: Gender;
  address: string | null;
  phone_number: string | null;
  created_at: string;
}

export interface PatientListResponse {
  items: Patient[];
  total: number;
}

export interface PatientInput {
  full_name: string;
  birth_date: string;
  gender: Gender;
  address: string | null;
  phone_number: string | null;
}

export interface Icd10 {
  code: string;
  name: string;
}

export interface Drug {
  id: number;
  name: string;
  unit: string;
  price: number;
}

export interface ProcedureMaster {
  id: number;
  name: string;
  price: number;
}

export interface Practitioner {
  id: number;
  full_name: string;
}

export interface PhysicalExamItem {
  body_site: string;
  finding: string;
  source: DataSource;
  verified_by_doctor: boolean;
}

export interface DiagnosisItem {
  id: number;
  icd_code: string | null;
  name: string;
  assertion_status: string;
  source: DataSource;
  verified_by_doctor: boolean;
}

export interface MedicationItem {
  id: number;
  drug_id: number | null;
  name: string;
  doctor: string | null;
  unit: string | null;
  quantity: number;
  unit_price: number;
  subtotal: number;
  source: DataSource;
  verified_by_doctor: boolean;
}

export interface ProcedureItem {
  id: number;
  procedure_id: number | null;
  name: string;
  price: number;
  source: DataSource;
  verified_by_doctor: boolean;
}

export interface EncounterDetail {
  id: number;
  status: string;
  reason: string | null;
  started_at: string;
  patient: Patient;
  practitioner: Practitioner | null;
  anamnesis: string;
  education: string;
  physical_exam: PhysicalExamItem[];
  diagnoses: DiagnosisItem[];
  medications: MedicationItem[];
  procedures: ProcedureItem[];
  total_cost: number;
}

export interface EncounterSummary {
  id: number;
  status: string;
  reason: string | null;
  started_at: string;
  practitioner: Practitioner | null;
  diagnoses: string[];
}

export interface DashboardSummary {
  patient_count: number;
  encounters_today: number;
}

/** Payload POST /encounters/{id}/exam (Bagian 8 rancangan). */
export interface ExamPayload {
  anamnesis: string;
  physical_exam: { body_site: string; finding: string }[];
  diagnoses: { icd_code: string | null; name: string; source: DataSource }[];
  medications: { drug_id: number; quantity: number; source: DataSource }[];
  procedures: { procedure_id: number; source: DataSource }[];
  education: string;
}

export interface DictationSample {
  id: string;
  title: string;
  description: string;
  filename: string;
  duration_sec: number;
  transcript: string;
}

export interface DictationSegment {
  start: number | null;
  end: number | null;
  text: string;
}

export interface DictationSentence {
  idx: number;
  text: string;
  soap: string;
}

export interface DictationEntity {
  text: string;
  label: string;
  start: number;
  end: number;
  sentence_idx: number;
  assertion: string;
}

export interface DictationTimings {
  stt: number;
  soap: number;
  ner: number;
  assertion: number;
}

export interface MappedPhysicalExam {
  body_site: string;
  finding: string;
  is_normal: boolean;
  source: string;
}

export interface MappedDiagnosis {
  icd_code: string | null;
  name: string;
  assertion: string;
  source: string;
}

export interface MappedMedication {
  drug_id: number | null;
  name: string;
  quantity: number;
  source: string;
}

export interface MappedProcedure {
  procedure_id: number | null;
  name: string;
  source: string;
}

export interface MappedFormResult {
  anamnesis: string;
  physical_exam: MappedPhysicalExam[];
  diagnoses: MappedDiagnosis[];
  medications: MappedMedication[];
  procedures: MappedProcedure[];
  education: string;
  summary_text: string;
}

export interface DictationResult {
  transcript: string;
  sentences: DictationSentence[];
  entities: DictationEntity[];
  timings_ms: DictationTimings;
  segments: DictationSegment[];
  mapped_form?: MappedFormResult;
}

export interface DictationJobStatus {
  id: number;
  encounter_id: number;
  audio_id: number | null;
  status: "queued" | "processing" | "done" | "error";
  step: string | null;
  result: DictationResult | null;
  error: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PipelineLogItem {
  id: number;
  encounter_id: number | null;
  model_version: string | null;
  wer_value: number | null;
  soap_f1: number | null;
  ner_f1: number | null;
  latency_ms: {
    stt?: number;
    soap?: number;
    ner?: number;
    assertion?: number;
    [key: string]: number | undefined;
  } | null;
  notes: string | null;
  created_at: string | null;
}

export interface PipelineLogsListResponse {
  items: PipelineLogItem[];
  total: number;
}

export interface PipelineMetricsSummary {
  total_runs: number;
  avg_wer: number | null;
  avg_soap_f1: number | null;
  avg_ner_f1: number | null;
  avg_total_latency_ms: number;
  active_nlp_engine: string;
  whisper_device: string;
}
