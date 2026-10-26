import { Plus, Search } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateEncounter, usePatients } from "@/hooks/useRme";
import { getApiErrorMessage } from "@/lib/api";
import { calcAge, formatDate, genderLabel } from "@/lib/format";

/**
 * Tabel pasien + pencarian. Mode `exam` dipakai menu "Pemeriksaan Dokter":
 * tombol aksi per baris membuat kunjungan baru lalu membuka formulir pemeriksaan.
 */
export function PatientsPage({ mode = "list" }: { mode?: "list" | "exam" }) {
  const [q, setQ] = useState("");
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = usePatients(q.trim());
  const createEncounter = useCreateEncounter();

  function startExam(patientId: number) {
    createEncounter.mutate(
      { patient_id: patientId },
      { onSuccess: (enc) => navigate(`/encounters/${enc.id}/exam`) },
    );
  }

  const isExam = mode === "exam";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            {isExam ? "Pemeriksaan Dokter" : "Data Pasien"}
          </h1>
          <p className="text-sm text-slate-500">
            {isExam
              ? "Pilih pasien untuk membuka Formulir Hasil Pemeriksaan Dokter."
              : "Cari pasien lama atau daftarkan pasien baru."}
          </p>
        </div>
        <Button asChild className="bg-emerald-600 text-white hover:bg-emerald-700">
          <Link to="/patients/new">
            <Plus /> Pasien Baru
          </Link>
        </Button>
      </div>

      <div className="relative max-w-md">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
        <Input
          aria-label="Cari pasien"
          placeholder="Cari nama atau No. RM"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="pl-9"
        />
      </div>

      {createEncounter.isError && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {getApiErrorMessage(createEncounter.error, "Gagal membuat kunjungan")}
        </p>
      )}

      <div className="overflow-x-auto rounded-lg border bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
            <tr>
              <th className="px-3 py-2">No. RM</th>
              <th className="px-3 py-2">Nama</th>
              <th className="px-3 py-2">Tgl Lahir</th>
              <th className="px-3 py-2">Umur</th>
              <th className="px-3 py-2">JK</th>
              <th className="px-3 py-2 text-right">Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-3 py-8 text-center text-slate-500">
                  Memuat...
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={6} role="alert" className="px-3 py-8 text-center text-red-600">
                  {getApiErrorMessage(error, "Gagal memuat data pasien")}
                </td>
              </tr>
            )}
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-8 text-center text-slate-500">
                  Belum ada data
                </td>
              </tr>
            )}
            {data?.items.map((p) => (
              <tr key={p.id} className="hover:bg-slate-50">
                <td className="px-3 py-2 font-mono text-xs">{p.medical_record_no}</td>
                <td className="px-3 py-2 font-medium text-slate-800">{p.full_name}</td>
                <td className="px-3 py-2">{formatDate(p.birth_date)}</td>
                <td className="px-3 py-2">{calcAge(p.birth_date)} th</td>
                <td className="px-3 py-2">{genderLabel(p.gender)}</td>
                <td className="px-3 py-2">
                  <div className="flex justify-end gap-2">
                    <Button asChild size="sm" variant="outline">
                      <Link to={`/patients/${p.id}`}>Detail</Link>
                    </Button>
                    {isExam && (
                      <Button
                        size="sm"
                        disabled={createEncounter.isPending}
                        onClick={() => startExam(p.id)}
                        className="bg-emerald-600 text-white hover:bg-emerald-700"
                      >
                        Mulai Pemeriksaan
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data && <p className="text-xs text-slate-500">Total: {data.total} pasien</p>}
    </div>
  );
}
