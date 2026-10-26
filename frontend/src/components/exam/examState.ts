import { BODY_SITES } from "@/lib/format";
import type { DataSource, Drug, EncounterDetail, ExamPayload, ProcedureMaster } from "@/types";

export interface PhysicalState {
  checked: boolean;
  finding: string;
  source?: DataSource;
}
export type PhysicalMap = Record<string, PhysicalState>;

export interface DiagnosisRow {
  icd_code: string | null;
  name: string;
  source: DataSource;
}
export interface MedicationRow {
  drug: Drug;
  quantity: number;
  source: DataSource;
}
export interface ProcedureRow {
  procedure: ProcedureMaster;
  source: DataSource;
}

export interface ExamState {
  anamnesis: string;
  education: string;
  physical: PhysicalMap;
  diagnoses: DiagnosisRow[];
  medications: MedicationRow[];
  procedures: ProcedureRow[];
}

export const NORMAL_TEXT = "Normal";

export function emptyPhysical(): PhysicalMap {
  return Object.fromEntries(
    BODY_SITES.map((site) => [site, { checked: false, finding: NORMAL_TEXT }]),
  );
}

/** Bangun state form dari data kunjungan yang tersimpan. */
export function stateFromEncounter(encounter: EncounterDetail): ExamState {
  const physical = emptyPhysical();
  for (const item of encounter.physical_exam) {
    if (item.body_site in physical) {
      physical[item.body_site] = { checked: true, finding: item.finding, source: item.source };
    }
  }
  return {
    anamnesis: encounter.anamnesis,
    education: encounter.education,
    physical,
    diagnoses: encounter.diagnoses.map((d) => ({
      icd_code: d.icd_code,
      name: d.name,
      source: d.source,
    })),
    medications: encounter.medications
      .filter((m) => m.drug_id !== null)
      .map((m) => ({
        drug: {
          id: m.drug_id as number,
          name: m.name,
          unit: m.unit ?? "",
          price: m.unit_price,
        },
        quantity: m.quantity,
        source: m.source,
      })),
    procedures: encounter.procedures
      .filter((p) => p.procedure_id !== null)
      .map((p) => ({
        procedure: { id: p.procedure_id as number, name: p.name, price: p.price },
        source: p.source,
      })),
  };
}

/** Ubah state form menjadi payload API (Bagian 8). Hanya organ yang dicentang yang dikirim. */
export function toPayload(state: ExamState): ExamPayload {
  return {
    anamnesis: state.anamnesis.trim(),
    physical_exam: BODY_SITES.filter(
      (site) => state.physical[site]?.checked && state.physical[site].finding.trim(),
    ).map((site) => ({ body_site: site, finding: state.physical[site].finding.trim() })),
    diagnoses: state.diagnoses.map((d) => ({
      icd_code: d.icd_code,
      name: d.name,
      source: d.source,
    })),
    medications: state.medications.map((m) => ({
      drug_id: m.drug.id,
      quantity: m.quantity,
      source: m.source,
    })),
    procedures: state.procedures.map((p) => ({
      procedure_id: p.procedure.id,
      source: p.source,
    })),
    education: state.education.trim(),
  };
}
