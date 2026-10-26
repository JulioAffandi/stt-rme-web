import { Pencil } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { PatientCard } from "@/components/patient/PatientCard";
import { PatientForm } from "@/components/patient/PatientForm";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useCreateEncounter,
  usePatient,
  usePatientEncounters,
  useUpdatePatient,
} from "@/hooks/useRme";
import { getApiErrorMessage } from "@/lib/api";
import { formatDateTime } from "@/lib/format";

export function PatientDetailPage() {
  const { id } = useParams();
  const patientId = Number(id);
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);

  const { data: patient, isLoading, isError, error } = usePatient(patientId);
  const encounters = usePatientEncounters(patientId);
  const update = useUpdatePatient(patientId);
  const createEncounter = useCreateEncounter();

  if (isLoading) return <p className="text-sm text-slate-500">Memuat data pasien...</p>;
  if (isError || !patient) {
    return (
      <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
        {getApiErrorMessage(error, "Pasien tidak ditemukan")}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Detail Pasien</h1>
          <p className="text-sm text-slate-500">Biodata dan riwayat kunjungan.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setEditing((v) => !v)}>
            <Pencil /> {editing ? "Tutup Ubah Data" : "Ubah Data"}
          </Button>
          <Button
            disabled={createEncounter.isPending}
            onClick={() =>
              createEncounter.mutate(
                { patient_id: patient.id },
                { onSuccess: (enc) => navigate(`/encounters/${enc.id}/exam`) },
              )
            }
            className="bg-emerald-600 text-white hover:bg-emerald-700"
          >
            Mulai Kunjungan Baru
          </Button>
        </div>
      </div>

      {createEncounter.isError && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {getApiErrorMessage(createEncounter.error, "Gagal membuat kunjungan")}
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-[18rem_1fr]">
        <aside>
          <PatientCard patient={patient} />
        </aside>

        <div className="min-w-0 space-y-4">
          {editing && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Ubah Biodata</CardTitle>
              </CardHeader>
              <CardContent>
                <PatientForm
                  initial={patient}
                  submitLabel="Simpan Perubahan"
                  submitting={update.isPending}
                  error={
                    update.isError ? getApiErrorMessage(update.error, "Gagal menyimpan") : null
                  }
                  onSubmit={(input) => update.mutate(input, { onSuccess: () => setEditing(false) })}
                  onCancel={() => setEditing(false)}
                />
              </CardContent>
            </Card>
          )}

          {!editing && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Biodata</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-2 text-sm sm:grid-cols-2">
                <p>
                  <span className="text-slate-500">Alamat: </span>
                  {patient.address ?? "-"}
                </p>
                <p>
                  <span className="text-slate-500">Telepon: </span>
                  {patient.phone_number ?? "-"}
                </p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Riwayat Kunjungan</CardTitle>
            </CardHeader>
            <CardContent>
              {encounters.isLoading && <p className="text-sm text-slate-500">Memuat...</p>}
              {encounters.isError && (
                <p role="alert" className="text-sm text-red-600">
                  Gagal memuat riwayat kunjungan.
                </p>
              )}
              {encounters.data?.length === 0 && (
                <p className="py-4 text-center text-sm text-slate-500">Belum ada data</p>
              )}
              <ul className="divide-y">
                {encounters.data?.map((e) => (
                  <li key={e.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                    <div className="text-sm">
                      <p className="font-medium text-slate-800">
                        {formatDateTime(e.started_at)}{" "}
                        <Badge
                          variant={e.status === "completed" ? "default" : "secondary"}
                          className={e.status === "completed" ? "bg-emerald-600" : ""}
                        >
                          {e.status === "completed" ? "Selesai" : "Berjalan"}
                        </Badge>
                      </p>
                      <p className="text-slate-500">
                        {e.practitioner?.full_name ?? "-"} ·{" "}
                        {e.diagnoses.length ? e.diagnoses.join(", ") : "Belum ada diagnosa"}
                      </p>
                    </div>
                    <Button asChild size="sm" variant="outline">
                      <Link to={`/encounters/${e.id}/exam`}>
                        {e.status === "completed" ? "Lihat / Ubah" : "Lanjutkan"}
                      </Link>
                    </Button>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
