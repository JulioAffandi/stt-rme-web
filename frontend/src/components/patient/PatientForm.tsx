import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Gender, Patient, PatientInput } from "@/types";

/** Form biodata pasien (dipakai untuk pendaftaran baru & ubah data). */
export function PatientForm({
  initial,
  submitLabel,
  submitting,
  error,
  onSubmit,
  onCancel,
}: {
  initial?: Patient;
  submitLabel: string;
  submitting: boolean;
  error: string | null;
  onSubmit: (input: PatientInput) => void;
  onCancel: () => void;
}) {
  const [fullName, setFullName] = useState(initial?.full_name ?? "");
  const [birthDate, setBirthDate] = useState(initial?.birth_date ?? "");
  const [gender, setGender] = useState<Gender>(initial?.gender ?? "F");
  const [address, setAddress] = useState(initial?.address ?? "");
  const [phone, setPhone] = useState(initial?.phone_number ?? "");
  const [localError, setLocalError] = useState<string | null>(null);

  const today = new Date().toISOString().slice(0, 10);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!fullName.trim()) return setLocalError("Nama lengkap wajib diisi");
    if (!birthDate) return setLocalError("Tanggal lahir wajib diisi");
    if (birthDate > today) return setLocalError("Tanggal lahir tidak boleh di masa depan");
    setLocalError(null);
    onSubmit({
      full_name: fullName.trim(),
      birth_date: birthDate,
      gender,
      address: address.trim() || null,
      phone_number: phone.trim() || null,
    });
  }

  const message = localError ?? error;

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {initial && (
        <div className="space-y-1.5">
          <Label htmlFor="patient-mrn">No. RM</Label>
          <Input id="patient-mrn" value={initial.medical_record_no} disabled readOnly />
        </div>
      )}
      <div className="space-y-1.5">
        <Label htmlFor="patient-name">Nama Lengkap</Label>
        <Input
          id="patient-name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          maxLength={255}
          required
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="patient-birth">Tanggal Lahir</Label>
          <Input
            id="patient-birth"
            type="date"
            max={today}
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="patient-gender">Jenis Kelamin</Label>
          <select
            id="patient-gender"
            value={gender}
            onChange={(e) => setGender(e.target.value as Gender)}
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
          >
            <option value="F">Perempuan</option>
            <option value="M">Laki-laki</option>
          </select>
        </div>
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="patient-phone">No. Telepon</Label>
        <Input
          id="patient-phone"
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          maxLength={30}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="patient-address">Alamat</Label>
        <Textarea
          id="patient-address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          maxLength={500}
          className="min-h-20"
        />
      </div>

      {message && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {message}
        </p>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-700">
          {submitting ? "Menyimpan..." : submitLabel}
        </Button>
        <Button type="button" variant="destructive" onClick={onCancel} className="bg-red-600">
          Batal
        </Button>
      </div>
    </form>
  );
}
