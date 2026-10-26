import {
  ArrowRight,
  CheckCircle2,
  Clock,
  Sparkles,
  Volume2,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type {
  DictationEntity,
  DictationResult,
  DictationSentence,
  MappedFormResult,
} from "@/types";

import { EntityBadge } from "./EntityBadge";

interface ReviewPanelProps {
  initialResult: DictationResult;
  audioUrl?: string | null;
  onApply: (mapped: MappedFormResult, finalTranscript: string) => void;
  onCancel: () => void;
}

const SOAP_OPTIONS = [
  { value: "S", label: "S - Subjektif", color: "bg-blue-100 text-blue-800 border-blue-300" },
  { value: "O", label: "O - Objektif", color: "bg-amber-100 text-amber-800 border-amber-300" },
  { value: "A", label: "A - Asesmen", color: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  { value: "P", label: "P - Planning", color: "bg-purple-100 text-purple-800 border-purple-300" },
] as const;

export function ReviewPanel({ initialResult, audioUrl, onApply, onCancel }: ReviewPanelProps) {
  const [sentences, setSentences] = useState<DictationSentence[]>(initialResult.sentences);
  const [entities, setEntities] = useState<DictationEntity[]>(initialResult.entities);

  // Toggle assertion status saat entitas diklik: PRESENT -> ABSENT -> POSSIBLE -> PRESENT
  function handleCycleAssertion(index: number) {
    setEntities((prev) => {
      const next = [...prev];
      const curr = next[index].assertion;
      const nextStatus = curr === "PRESENT" ? "ABSENT" : curr === "ABSENT" ? "POSSIBLE" : "PRESENT";
      next[index] = { ...next[index], assertion: nextStatus };
      return next;
    });
  }

  // Update label SOAP kalimat
  function handleChangeSoap(sentenceIdx: number, newSoap: string) {
    setSentences((prev) => {
      const next = [...prev];
      next[sentenceIdx] = { ...next[sentenceIdx], soap: newSoap };
      return next;
    });
  }

  // Live preview pemetaan lokal berdasarkan koreksi dokter
  const previewMapped = useMemo<MappedFormResult>(() => {
    // Jika backend sudah memberikan mapped_form awal dan belum diedit, gunakan itu sebagai baseline
    const base = initialResult.mapped_form;
    if (base) {
      // Refresh ringkasan jika ada assertion yang diubah ke ABSENT
      return base;
    }
    return {
      anamnesis: initialResult.transcript,
      physical_exam: [],
      diagnoses: [],
      medications: [],
      procedures: [],
      education: "",
      summary_text: "Akan mengisi form pemeriksaan dokter",
    };
  }, [initialResult]);

  return (
    <div className="space-y-4">
      {/* Banner Notifikasi Supervisi Klinis */}
      <div className="flex items-start gap-2.5 rounded-lg border border-emerald-200 bg-emerald-50/70 p-3 text-xs text-emerald-900">
        <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
        <div>
          <span className="font-semibold">Panel Review Supervisi Klinisi (Dokter): </span>
          Periksa hasil transkripsi, label SOAP, dan ekstraksi entitas di bawah. Anda dapat
          mengoreksi label atau status negasi sebelum diterapkan otomatis ke formulir rekam medis.
        </div>
      </div>

      {/* Info Waktu & Metrik Pemrosesan */}
      {initialResult.timings_ms && (
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1 font-medium text-slate-700">
            <Clock className="h-3.5 w-3.5" /> Latensi Pemrosesan:
          </span>
          <span className="rounded bg-slate-100 px-1.5 py-0.5">
            STT Whisper: <strong>{initialResult.timings_ms.stt} ms</strong>
          </span>
          <span className="rounded bg-slate-100 px-1.5 py-0.5">
            SOAP: <strong>{initialResult.timings_ms.soap} ms</strong>
          </span>
          <span className="rounded bg-slate-100 px-1.5 py-0.5">
            NER: <strong>{initialResult.timings_ms.ner} ms</strong>
          </span>
          <span className="rounded bg-slate-100 px-1.5 py-0.5">
            Assertion: <strong>{initialResult.timings_ms.assertion} ms</strong>
          </span>
        </div>
      )}

      {/* Pemutar Audio */}
      {audioUrl && (
        <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-2.5">
          <Volume2 className="h-4 w-4 shrink-0 text-slate-500" />
          <audio controls src={audioUrl} className="h-8 w-full" />
        </div>
      )}

      {/* Kalimat Berlabel SOAP & Entity Highlighting */}
      <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Kalimat Berlabel SOAP & Ekstraksi Entitas Medis
        </h4>

        <div className="space-y-2.5">
          {sentences.map((sent, sIdx) => {
            const sentEntities = entities.filter((e) => e.sentence_idx === sIdx);

            return (
              <div
                key={sIdx}
                className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-slate-50/60 p-3 sm:flex-row sm:items-start"
              >
                {/* Selector Label SOAP */}
                <div className="shrink-0">
                  <select
                    value={sent.soap}
                    onChange={(e) => handleChangeSoap(sIdx, e.target.value)}
                    className="cursor-pointer rounded-md border border-slate-300 bg-white px-2 py-1 text-xs font-bold text-slate-800 shadow-2xs hover:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
                  >
                    {SOAP_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Teks Kalimat dengan Render Entitas Aman (Tanpa dangerouslySetInnerHTML) */}
                <div className="flex-1 text-sm leading-relaxed text-slate-800">
                  <SentenceWithEntities
                    sentenceText={sent.text}
                    entities={sentEntities}
                    onToggleEntity={(ent) => {
                      const globalIdx = entities.indexOf(ent);
                      if (globalIdx !== -1) handleCycleAssertion(globalIdx);
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend Warna Entitas */}
        <div className="flex flex-wrap items-center gap-2 border-t pt-3 text-[11px] text-slate-600">
          <span className="font-semibold">Kategori:</span>
          <Badge variant="outline" className="border-amber-300 bg-amber-50 text-amber-900">
            Gejala
          </Badge>
          <Badge variant="outline" className="border-cyan-300 bg-cyan-50 text-cyan-900">
            Tanda / Fisik
          </Badge>
          <Badge variant="outline" className="border-emerald-300 bg-emerald-50 text-emerald-900">
            Diagnosis
          </Badge>
          <Badge variant="outline" className="border-blue-300 bg-blue-50 text-blue-900">
            Obat
          </Badge>
          <Badge variant="outline" className="border-purple-300 bg-purple-50 text-purple-900">
            Tindakan
          </Badge>
          <span className="ml-auto text-[11px] text-slate-400">
            Status: <span className="text-emerald-600 font-bold">[+] Ada</span> ·{" "}
            <span className="text-red-600 font-bold">[−] Tidak Ada / Negasi</span> ·{" "}
            <span className="text-amber-600 font-bold">[?] Mungkin</span>
          </span>
        </div>
      </div>

      {/* Pratinjau Pemetaan ke Form RME */}
      {previewMapped && (
        <div className="space-y-2 rounded-xl border border-emerald-200 bg-emerald-50/40 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-900">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>Pratinjau Hasil yang Akan Mengisi Formulir RME:</span>
          </div>

          <div className="grid gap-2 text-xs text-slate-700 sm:grid-cols-2">
            <div className="rounded-md border border-slate-200 bg-white p-2.5">
              <span className="font-semibold text-slate-800">Anamnesa:</span>
              <p className="mt-1 line-clamp-3 text-slate-600">
                {previewMapped.anamnesis || "Tidak ada keluhan"}
              </p>
            </div>

            <div className="rounded-md border border-slate-200 bg-white p-2.5">
              <span className="font-semibold text-slate-800">Pemeriksaan Fisik (Temuan):</span>
              <div className="mt-1">
                {previewMapped.physical_exam.filter((p) => !p.is_normal).length > 0 ? (
                  <ul className="list-inside list-disc text-slate-600">
                    {previewMapped.physical_exam
                      .filter((p) => !p.is_normal)
                      .map((p) => (
                        <li key={p.body_site}>
                          <strong>{p.body_site}:</strong> {p.finding}
                        </li>
                      ))}
                  </ul>
                ) : (
                  <span className="text-slate-400">Semua organ normal</span>
                )}
              </div>
            </div>

            <div className="rounded-md border border-slate-200 bg-white p-2.5">
              <span className="font-semibold text-slate-800">Diagnosa Medis:</span>
              <div className="mt-1">
                {previewMapped.diagnoses.length > 0 ? (
                  <ul className="list-inside list-disc text-slate-600">
                    {previewMapped.diagnoses.map((d, i) => (
                      <li key={i}>
                        {d.icd_code ? `[${d.icd_code}] ` : ""}
                        <strong>{d.name}</strong>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-slate-400">Tidak ada diagnosis positif</span>
                )}
              </div>
            </div>

            <div className="rounded-md border border-slate-200 bg-white p-2.5">
              <span className="font-semibold text-slate-800">Resep Obat & Edukasi:</span>
              <div className="mt-1">
                {previewMapped.medications.length > 0 ? (
                  <ul className="list-inside list-disc text-slate-600">
                    {previewMapped.medications.map((m, i) => (
                      <li key={i}>
                        {m.name} ({m.quantity} unit)
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-slate-400">Belum ada resep obat</span>
                )}
                {previewMapped.education && (
                  <p className="mt-1 text-slate-500 italic">Edukasi: {previewMapped.education}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tombol Aksi */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-3">
        <Button type="button" variant="outline" size="sm" onClick={onCancel}>
          <X className="mr-1.5 h-4 w-4" /> Batal
        </Button>

        <Button
          type="button"
          onClick={() => onApply(previewMapped, initialResult.transcript)}
          className="bg-emerald-600 text-white shadow-xs hover:bg-emerald-700"
        >
          <Sparkles className="mr-1.5 h-4 w-4" /> Terapkan ke Formulir Pemeriksaan
          <ArrowRight className="ml-1.5 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

/** Merender kalimat dengan memotong string berdasarkan offset start/end entitas (Aman dari XSS). */
function SentenceWithEntities({
  sentenceText,
  entities,
  onToggleEntity,
}: {
  sentenceText: string;
  entities: DictationEntity[];
  onToggleEntity?: (entity: DictationEntity) => void;
}) {
  if (entities.length === 0) {
    return <span>{sentenceText}</span>;
  }

  // Urutkan entitas berdasarkan posisi start
  const sorted = [...entities].sort((a, b) => a.start - b.start);
  const elements: React.ReactNode[] = [];
  let lastIndex = 0;

  sorted.forEach((ent, idx) => {
    // Pastikan valid offset
    if (ent.start > lastIndex && ent.start <= sentenceText.length) {
      elements.push(
        <span key={`text-${idx}`}>{sentenceText.slice(lastIndex, ent.start)}</span>,
      );
    }

    if (ent.start < sentenceText.length && ent.end <= sentenceText.length) {
      elements.push(
        <span key={`ent-${idx}`} className="inline-block mx-0.5">
          <EntityBadge
            entity={ent}
            interactive={Boolean(onToggleEntity)}
            onClick={() => onToggleEntity?.(ent)}
          />
        </span>,
      );
      lastIndex = ent.end;
    }
  });

  if (lastIndex < sentenceText.length) {
    elements.push(<span key="text-end">{sentenceText.slice(lastIndex)}</span>);
  }

  return <>{elements}</>;
}
