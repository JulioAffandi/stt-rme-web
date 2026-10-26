import { useNavigate } from "react-router-dom";

import { PatientForm } from "@/components/patient/PatientForm";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreatePatient } from "@/hooks/useRme";
import { getApiErrorMessage } from "@/lib/api";

export function PatientNewPage() {
  const navigate = useNavigate();
  const create = useCreatePatient();

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Pendaftaran Pasien Baru</h1>
        <p className="text-sm text-slate-500">
          No. RM dibuat otomatis. Gunakan data fiktif untuk demo.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Biodata Pasien</CardTitle>
          <CardDescription>Semua kolom bertanda wajib harus diisi.</CardDescription>
        </CardHeader>
        <CardContent>
          <PatientForm
            submitLabel="Simpan Pasien"
            submitting={create.isPending}
            error={
              create.isError ? getApiErrorMessage(create.error, "Gagal menyimpan pasien") : null
            }
            onSubmit={(input) =>
              create.mutate(input, { onSuccess: (patient) => navigate(`/patients/${patient.id}`) })
            }
            onCancel={() => navigate("/patients")}
          />
        </CardContent>
      </Card>
    </div>
  );
}
