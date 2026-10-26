import { CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { DictationModal } from "@/components/dictation/DictationModal";
import { AnamnesisField } from "@/components/exam/AnamnesisField";
import { stateFromEncounter, toPayload, type ExamState } from "@/components/exam/examState";
import { DiagnosisTable, MedicationTable, ProcedureTable } from "@/components/exam/ExamTables";
import { PhysicalExamList } from "@/components/exam/PhysicalExamList";
import { PatientCard } from "@/components/patient/PatientCard";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useEncounter, useSaveExam } from "@/hooks/useRme";
import { getApiErrorMessage } from "@/lib/api";
import { formatDateTime, formatRupiah } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { EncounterDetail, MappedFormResult } from "@/types";

const TABS = ["Pemeriksaan", "Tanda Tanda Vital", "Riwayat Alergi dan Penyakit"] as const;
type Tab = (typeof TABS)[number];

export function ExamFormPage() {
  const { id } = useParams();
  const encounterId = Number(id);
  const { data, isLoading, isError, error } = useEncounter(encounterId);

  if (isLoading) return <p className="text-sm text-slate-500">Memuat kunjungan...</p>;
  if (isError || !data) {
    return (
      <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
        {getApiErrorMessage(error, "Kunjungan tidak ditemukan")}
      </p>
    );
  }
  // key = id agar state form di-reset saat berpindah kunjungan
  return <ExamForm key={data.id} encounter={data} />;
}

function ExamForm({ encounter }: { encounter: EncounterDetail }) {
  const navigate = useNavigate();
  const save = useSaveExam(encounter.id);
  const [tab, setTab] = useState<Tab>("Pemeriksaan");
  const [state, setState] = useState<ExamState>(() => stateFromEncounter(encounter));
  const [saved, setSaved] = useState(false);
  const [dictationOpen, setDictationOpen] = useState(false);

  function patch(change: Partial<ExamState>) {
    setSaved(false);
    setState((prev) => ({ ...prev, ...change }));
  }

  function handleSave() {
    save.mutate(toPayload(state), { onSuccess: () => setSaved(true) });
  }

  function handleApplyMapped(mapped: MappedFormResult, transcript: string) {
    // 1. Anamnesa
    const newAnamnesis = state.anamnesis
      ? `${state.anamnesis}\n\n${mapped.anamnesis || transcript}`
      : mapped.anamnesis || transcript;

    // 2. Pemeriksaan Fisik: Organ abnormal terisi & tercentang dengan source: ai
    const newPhysical = { ...state.physical };
    for (const item of mapped.physical_exam) {
      if (!item.is_normal && item.body_site in newPhysical) {
        newPhysical[item.body_site] = {
          checked: true,
          finding: item.finding,
          source: "ai",
        };
      }
    }

    // 3. Diagnosa dari AI
    const existingDiagNames = new Set(state.diagnoses.map((d) => d.name.toLowerCase()));
    const newDiagnoses = [...state.diagnoses];
    for (const d of mapped.diagnoses) {
      if (!existingDiagNames.has(d.name.toLowerCase())) {
        newDiagnoses.push({
          icd_code: d.icd_code,
          name: d.name,
          source: "ai",
        });
        existingDiagNames.add(d.name.toLowerCase());
      }
    }

    // 4. Obat dari AI
    const existingMedNames = new Set(state.medications.map((m) => m.drug.name.toLowerCase()));
    const newMedications = [...state.medications];
    for (const m of mapped.medications) {
      if (!existingMedNames.has(m.name.toLowerCase())) {
        newMedications.push({
          drug: {
            id: m.drug_id ?? Math.floor(Math.random() * 9000 + 1000),
            name: m.name,
            unit: "tablet",
            price: 1500,
          },
          quantity: m.quantity,
          source: "ai",
        });
        existingMedNames.add(m.name.toLowerCase());
      }
    }

    // 5. Edukasi
    const newEducation = mapped.education
      ? state.education
        ? `${state.education}\n${mapped.education}`
        : mapped.education
      : state.education;

    patch({
      anamnesis: newAnamnesis,
      physical: newPhysical,
      diagnoses: newDiagnoses,
      medications: newMedications,
      education: newEducation,
    });
  }

  const total =
    state.medications.reduce((s, m) => s + m.drug.price * m.quantity, 0) +
    state.procedures.reduce((s, p) => s + p.procedure.price, 0);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Formulir Hasil Pemeriksaan Dokter</h1>
        <p className="text-sm text-slate-500">
          Kunjungan #{encounter.id} · {formatDateTime(encounter.started_at)} ·{" "}
          {encounter.practitioner?.full_name ?? "Dokter belum ditentukan"}
          {encounter.status === "completed" && " · Selesai"}
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[18rem_1fr]">
        <aside>
          <PatientCard patient={encounter.patient} />
        </aside>

        <div className="min-w-0 space-y-4 rounded-lg border bg-white p-4 shadow-sm">
          <div
            role="tablist"
            aria-label="Bagian formulir"
            className="flex flex-wrap gap-1 border-b"
          >
            {TABS.map((name) => (
              <button
                key={name}
                role="tab"
                type="button"
                aria-selected={tab === name}
                onClick={() => setTab(name)}
                className={cn(
                  "-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                  tab === name
                    ? "border-emerald-600 text-emerald-700"
                    : "border-transparent text-slate-500 hover:text-slate-800",
                )}
              >
                {name}
              </button>
            ))}
          </div>

          {tab === "Pemeriksaan" ? (
            <div className="space-y-6">
              <AnamnesisField
                value={state.anamnesis}
                onChange={(anamnesis) => patch({ anamnesis })}
                onOpenDictation={() => setDictationOpen(true)}
              />
              <PhysicalExamList
                value={state.physical}
                onChange={(physical) => patch({ physical })}
              />
              <DiagnosisTable
                rows={state.diagnoses}
                onChange={(diagnoses) => patch({ diagnoses })}
              />
              <MedicationTable
                rows={state.medications}
                doctorName={encounter.practitioner?.full_name ?? null}
                onChange={(medications) => patch({ medications })}
              />
              <ProcedureTable
                rows={state.procedures}
                onChange={(procedures) => patch({ procedures })}
              />

              <section className="space-y-2">
                <Label htmlFor="exam-education" className="text-base font-semibold">
                  Edukasi
                </Label>
                <Textarea
                  id="exam-education"
                  value={state.education}
                  onChange={(e) => patch({ education: e.target.value })}
                  maxLength={5000}
                  placeholder="Edukasi / anjuran untuk pasien..."
                />
              </section>

              <p className="text-right text-sm text-slate-600">
                Total biaya obat + tindakan: <strong>{formatRupiah(total)}</strong>
              </p>

              {save.isError && (
                <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                  {getApiErrorMessage(save.error, "Gagal menyimpan hasil pemeriksaan")}
                </p>
              )}
              {saved && (
                <p
                  role="status"
                  className="flex items-center gap-2 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800"
                >
                  <CheckCircle2 className="h-4 w-4" /> Hasil pemeriksaan berhasil disimpan.
                </p>
              )}

              <div className="flex flex-wrap gap-2 border-t pt-4">
                <Button
                  type="button"
                  onClick={handleSave}
                  disabled={save.isPending}
                  className="bg-emerald-600 text-white hover:bg-emerald-700"
                >
                  {save.isPending ? "Menyimpan..." : "Simpan Hasil Pemeriksaan"}
                </Button>
                <Button
                  type="button"
                  onClick={() => navigate(`/patients/${encounter.patient.id}`)}
                  className="bg-red-600 text-white hover:bg-red-700"
                >
                  Kembali
                </Button>
              </div>

              <DictationModal
                open={dictationOpen}
                onClose={() => setDictationOpen(false)}
                encounterId={encounter.id}
                onApplyMappedForm={handleApplyMapped}
              />
            </div>
          ) : (
            <p className="py-10 text-center text-sm text-slate-500">
              Belum ada data. Bagian ini belum termasuk cakupan Fase 2.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
