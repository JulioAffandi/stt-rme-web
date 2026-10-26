import { Activity, ArrowRight, CalendarDays, CheckCircle2, Mic, PlayCircle, Users } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useMe } from "@/hooks/useAuth";
import { usePipelineMetrics } from "@/hooks/usePipelineLogs";
import { useDashboardSummary } from "@/hooks/useRme";

function StatCard({
  title,
  value,
  hint,
  icon: Icon,
  accentClass,
}: {
  title: string;
  value: string;
  hint: string;
  icon: typeof Users;
  accentClass: string;
}) {
  return (
    <Card className="shadow-xs">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-slate-600">{title}</CardTitle>
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${accentClass}`}>
          <Icon className="h-5 w-5 text-white" />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold text-slate-800">{value}</p>
        <CardDescription className="mt-1 text-xs">{hint}</CardDescription>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const { data: user } = useMe();
  const { data: summary } = useDashboardSummary();
  const { data: metrics } = usePipelineMetrics();

  const pipelineMetricText =
    metrics?.avg_wer !== null && metrics?.avg_wer !== undefined
      ? `WER ${(metrics.avg_wer * 100).toFixed(1)}%`
      : "Siap Uji";

  const pipelineHint =
    metrics?.avg_soap_f1 !== null && metrics?.avg_soap_f1 !== undefined
      ? `SOAP F1: ${(metrics.avg_soap_f1 * 100).toFixed(1)}% · NER F1: ${(metrics.avg_ner_f1 ? metrics.avg_ner_f1 * 100 : 0).toFixed(1)}%`
      : "Buka menu Log Pipeline untuk evaluasi benchmark";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <p className="text-sm text-slate-500">
          Selamat datang{user ? `, ${user.full_name}` : ""}. Ringkasan aktivitas klinik demo & evaluasi STT-NLP.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Jumlah Pasien"
          value={summary ? String(summary.patient_count) : "—"}
          hint="Total pasien terdaftar di klinik"
          icon={Users}
          accentClass="bg-emerald-600"
        />
        <StatCard
          title="Kunjungan Hari Ini"
          value={summary ? String(summary.encounters_today) : "—"}
          hint="Kunjungan rawat jalan aktif"
          icon={CalendarDays}
          accentClass="bg-orange-500"
        />
        <StatCard
          title="Metrik Pipeline"
          value={pipelineMetricText}
          hint={pipelineHint}
          icon={Activity}
          accentClass="bg-cyan-600"
        />
      </div>

      {/* Aksi Cepat Demo Sidang */}
      <Card className="border-emerald-200 bg-emerald-50/30 shadow-xs">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-emerald-900">
            Aksi Cepat Demonstrasi Sidang Proyek Akhir
          </CardTitle>
          <CardDescription className="text-xs text-emerald-700">
            Pintasan cepat untuk mendemonstrasikan otomatisasi rekam medis di hadapan dosen penguji.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Link to="/patients">
            <Button className="bg-emerald-600 text-white hover:bg-emerald-700">
              <Mic className="mr-1.5 h-4 w-4" /> Buka Pemeriksaan Pasien (Dikte Suara)
            </Button>
          </Link>
          <Link to="/pipeline-logs">
            <Button variant="outline" className="border-emerald-300 text-emerald-800 hover:bg-emerald-100">
              <PlayCircle className="mr-1.5 h-4 w-4" /> Buka Log & Evaluasi Benchmark
              <ArrowRight className="ml-1.5 h-4 w-4" />
            </Button>
          </Link>
        </CardContent>
      </Card>

      {/* Ringkasan Status Pipeline */}
      <Card className="shadow-xs">
        <CardHeader>
          <CardTitle>Status Integrasi Pipeline RME</CardTitle>
          <CardDescription>
            Seluruh komponen utama pada dokumen rancangan telah aktif dan siap diuji coba.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-slate-700">
          <div className="grid gap-2 sm:grid-cols-2">
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <div>
                <span className="font-semibold">Speech-to-Text:</span> Whisper fine-tuned (WAV 16 kHz mono)
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <div>
                <span className="font-semibold">Klasifikasi SOAP:</span> Ekstraksi kalimat Subjektif, Objektif, Asesmen, Plan
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <div>
                <span className="font-semibold">Medical NER & Assertion:</span> Gejala, Tanda Fisik, Diagnosa ICD, Obat & Negasi
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <div>
                <span className="font-semibold">Supervisi Klinis:</span> Panel Review interaktif sebelum mengisi formulir RME
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
