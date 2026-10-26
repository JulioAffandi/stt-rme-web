import {
  Activity,
  CheckCircle,
  Clock,
  Cpu,
  FileText,
  Loader2,
  PlayCircle,
  Sparkles,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { usePipelineLogs, usePipelineMetrics, useRunEvaluation } from "@/hooks/usePipelineLogs";
import { formatDateTime } from "@/lib/format";

export function PipelineLogsPage() {
  const { data: logsData, isLoading: isLogsLoading } = usePipelineLogs(50, 0);
  const { data: metrics, isLoading: isMetricsLoading } = usePipelineMetrics();
  const runEvaluation = useRunEvaluation();

  function handleRunBenchmark() {
    runEvaluation.mutate();
  }

  return (
    <div className="space-y-6">
      {/* Header & Aksi Evaluasi */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Log & Evaluasi Pipeline</h1>
          <p className="text-sm text-slate-500">
            Pencatatan metrik evaluasi eksperimen offline dan inferensi lisan live (WER, SOAP F1,
            NER F1, dan latensi komputasi).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            onClick={handleRunBenchmark}
            disabled={runEvaluation.isPending}
            className="bg-emerald-600 text-white shadow-xs hover:bg-emerald-700"
          >
            {runEvaluation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Menjalankan Benchmark...
              </>
            ) : (
              <>
                <PlayCircle className="mr-2 h-4 w-4" />
                Jalankan Evaluasi Benchmark
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Pesan Sukses Benchmark */}
      {runEvaluation.isSuccess && (
        <div className="flex items-center gap-2 rounded-lg bg-emerald-50 p-3 text-xs text-emerald-800 border border-emerald-200">
          <CheckCircle className="h-4 w-4 text-emerald-600" />
          <span>
            {runEvaluation.data?.message ?? "Evaluasi benchmark selesai dijalankan dan log berhasil dicatat."}
          </span>
        </div>
      )}

      {/* Grid Kartu Metrik Utama */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Metrik 1: WER (Speech-to-Text) */}
        <Card className="border-l-4 border-l-emerald-500 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Word Error Rate (WER)
            </CardTitle>
            <Sparkles className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-800">
              {isMetricsLoading
                ? "..."
                : metrics?.avg_wer !== null && metrics?.avg_wer !== undefined
                  ? `${(metrics.avg_wer * 100).toFixed(1)}%`
                  : "—"}
            </div>
            <CardDescription className="mt-1 text-xs">
              Akurasi STT Whisper vs transkrip referensi
            </CardDescription>
          </CardContent>
        </Card>

        {/* Metrik 2: SOAP F1-Score */}
        <Card className="border-l-4 border-l-blue-500 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              SOAP Classifier F1
            </CardTitle>
            <FileText className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-800">
              {isMetricsLoading
                ? "..."
                : metrics?.avg_soap_f1 !== null && metrics?.avg_soap_f1 !== undefined
                  ? `${(metrics.avg_soap_f1 * 100).toFixed(1)}%`
                  : "—"}
            </div>
            <CardDescription className="mt-1 text-xs">
              Ketepatan klasifikasi kalimat S, O, A, P
            </CardDescription>
          </CardContent>
        </Card>

        {/* Metrik 3: NER F1-Score */}
        <Card className="border-l-4 border-l-purple-500 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Medical NER F1
            </CardTitle>
            <Zap className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-800">
              {isMetricsLoading
                ? "..."
                : metrics?.avg_ner_f1 !== null && metrics?.avg_ner_f1 !== undefined
                  ? `${(metrics.avg_ner_f1 * 100).toFixed(1)}%`
                  : "—"}
            </div>
            <CardDescription className="mt-1 text-xs">
              Ekstraksi Gejala, Tanda, Obat, Diagnosa
            </CardDescription>
          </CardContent>
        </Card>

        {/* Metrik 4: Latensi Total Rata-rata */}
        <Card className="border-l-4 border-l-amber-500 shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Rata-rata Latensi
            </CardTitle>
            <Clock className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-800">
              {isMetricsLoading
                ? "..."
                : metrics?.avg_total_latency_ms
                  ? `${metrics.avg_total_latency_ms} ms`
                  : "—"}
            </div>
            <CardDescription className="mt-1 text-xs">
              Durasi eksekusi pipeline lengkap
            </CardDescription>
          </CardContent>
        </Card>
      </div>

      {/* Info Konfigurasi Runtime */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 text-xs text-slate-600 shadow-2xs">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-slate-500" />
          <span>Device Komputasi:</span>
          <Badge variant="outline" className="font-mono text-[11px]">
            {metrics?.whisper_device ?? "auto"}
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-slate-500" />
          <span>Engine NLP Aktif:</span>
          <Badge
            variant="secondary"
            className={
              metrics?.active_nlp_engine === "real"
                ? "bg-emerald-100 text-emerald-800"
                : "bg-amber-100 text-amber-800"
            }
          >
            {metrics?.active_nlp_engine === "real" ? "Model Nyata (Fase 5)" : "Rule-Based Mock (Fase 4)"}
          </Badge>
        </div>

        <div className="text-slate-400">
          Total Rekaman Log: <strong>{metrics?.total_runs ?? 0}</strong>
        </div>
      </div>

      {/* Tabel Riwayat Log Pipeline */}
      <Card className="shadow-xs">
        <CardHeader>
          <CardTitle>Riwayat Inferensi & Evaluasi Model</CardTitle>
          <CardDescription>
            Data riwayat komputasi yang tercatat di tabel <code>pipeline_log</code> untuk keperluan
            evaluasi pada naskah proyek akhir.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 border-b">
                <tr>
                  <th className="px-3 py-3 font-semibold">No</th>
                  <th className="px-3 py-3 font-semibold">Waktu</th>
                  <th className="px-3 py-3 font-semibold">Versi Model</th>
                  <th className="px-3 py-3 font-semibold">WER</th>
                  <th className="px-3 py-3 font-semibold">SOAP F1</th>
                  <th className="px-3 py-3 font-semibold">NER F1</th>
                  <th className="px-3 py-3 font-semibold">Rincian Latensi</th>
                  <th className="px-3 py-3 font-semibold">Catatan Evaluasi</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {isLogsLoading ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400">
                      Memuat riwayat log pipeline...
                    </td>
                  </tr>
                ) : !logsData?.items || logsData.items.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400">
                      Belum ada data evaluasi. Klik tombol "Jalankan Evaluasi Benchmark" untuk memulai.
                    </td>
                  </tr>
                ) : (
                  logsData.items.map((log, index) => {
                    const lat = log.latency_ms;
                    return (
                      <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-3 py-3 font-medium text-slate-500">{index + 1}</td>
                        <td className="px-3 py-3 text-slate-600 whitespace-nowrap">
                          {log.created_at ? formatDateTime(log.created_at) : "—"}
                        </td>
                        <td className="px-3 py-3 font-mono text-[11px] text-slate-800">
                          {log.model_version ?? "—"}
                        </td>
                        <td className="px-3 py-3">
                          {log.wer_value !== null ? (
                            <span
                              className={`font-semibold ${
                                log.wer_value <= 0.1
                                  ? "text-emerald-600"
                                  : log.wer_value <= 0.15
                                    ? "text-amber-600"
                                    : "text-red-600"
                              }`}
                            >
                              {(log.wer_value * 100).toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="px-3 py-3 font-semibold text-blue-700">
                          {log.soap_f1 !== null ? `${(log.soap_f1 * 100).toFixed(1)}%` : "—"}
                        </td>
                        <td className="px-3 py-3 font-semibold text-purple-700">
                          {log.ner_f1 !== null ? `${(log.ner_f1 * 100).toFixed(1)}%` : "—"}
                        </td>
                        <td className="px-3 py-3">
                          {lat ? (
                            <div className="flex flex-wrap gap-1 font-mono text-[10px]">
                              {lat.stt !== undefined && (
                                <span className="rounded bg-slate-100 px-1 py-0.5 text-slate-700">
                                  STT: {lat.stt}ms
                                </span>
                              )}
                              {lat.soap !== undefined && (
                                <span className="rounded bg-blue-50 px-1 py-0.5 text-blue-700">
                                  SOAP: {lat.soap}ms
                                </span>
                              )}
                              {lat.ner !== undefined && (
                                <span className="rounded bg-purple-50 px-1 py-0.5 text-purple-700">
                                  NER: {lat.ner}ms
                                </span>
                              )}
                              {lat.assertion !== undefined && (
                                <span className="rounded bg-emerald-50 px-1 py-0.5 text-emerald-700">
                                  Assert: {lat.assertion}ms
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-slate-600 max-w-xs truncate" title={log.notes ?? ""}>
                          {log.notes ?? "—"}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
