import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { calcAge, formatDate, genderLabel, initials } from "@/lib/format";
import type { Patient } from "@/types";

/** Kartu pasien (kolom kiri Formulir Pemeriksaan) — avatar inisial, bukan foto. */
export function PatientCard({ patient }: { patient: Patient }) {
  return (
    <div className="space-y-4 rounded-lg border bg-white p-4 shadow-sm">
      <div className="flex flex-col items-center gap-2 text-center">
        <div
          className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 text-2xl font-bold text-emerald-700"
          aria-hidden="true"
        >
          {initials(patient.full_name)}
        </div>
        <p className="text-lg font-semibold text-slate-800">{patient.full_name}</p>
      </div>

      <dl className="space-y-2 text-sm">
        <Row label="No. RM" value={patient.medical_record_no} />
        <Row label="Tgl Lahir" value={formatDate(patient.birth_date)} />
        <Row label="Umur" value={`${calcAge(patient.birth_date)} tahun`} />
        <Row label="Jenis Kelamin" value={genderLabel(patient.gender)} />
      </dl>

      <div className="flex flex-col gap-2">
        <Button asChild className="bg-orange-500 text-white hover:bg-orange-600">
          <Link to={`/patients/${patient.id}`}>Lihat Riwayat Kunjungan</Link>
        </Button>
        {["Buat Janji Kunjungan", "Buat Resep Dokter", "Buat Surat"].map((label, i) => (
          <Button
            key={label}
            type="button"
            disabled
            title="Belum tersedia pada fase ini"
            className={i === 2 ? "bg-yellow-500 text-white" : "bg-cyan-600 text-white"}
          >
            {label}
          </Button>
        ))}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-right font-medium text-slate-800">{value}</dd>
    </div>
  );
}
