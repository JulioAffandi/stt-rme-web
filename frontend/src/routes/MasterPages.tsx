import { Search } from "lucide-react";
import { useState } from "react";

import { Input } from "@/components/ui/input";
import { useDrugSearch, useIcd10Search } from "@/hooks/useRme";
import { formatRupiah } from "@/lib/format";

const th = "px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600";

function Shell({
  title,
  subtitle,
  q,
  setQ,
  children,
}: {
  title: string;
  subtitle: string;
  q: string;
  setQ: (v: string) => void;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">{title}</h1>
        <p className="text-sm text-slate-500">{subtitle}</p>
      </div>
      <div className="relative max-w-md">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
        <Input
          aria-label="Cari"
          placeholder="Cari..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="pl-9"
        />
      </div>
      <div className="overflow-x-auto rounded-lg border bg-white shadow-sm">{children}</div>
    </div>
  );
}

function Status({
  colSpan,
  loading,
  error,
  empty,
}: {
  colSpan: number;
  loading: boolean;
  error: boolean;
  empty: boolean;
}) {
  if (loading)
    return (
      <tr>
        <td colSpan={colSpan} className="px-3 py-8 text-center text-sm text-slate-500">
          Memuat...
        </td>
      </tr>
    );
  if (error)
    return (
      <tr>
        <td colSpan={colSpan} role="alert" className="px-3 py-8 text-center text-sm text-red-600">
          Gagal memuat data.
        </td>
      </tr>
    );
  if (empty)
    return (
      <tr>
        <td colSpan={colSpan} className="px-3 py-8 text-center text-sm text-slate-500">
          Belum ada data
        </td>
      </tr>
    );
  return null;
}

export function MasterIcd10Page() {
  const [q, setQ] = useState("");
  const { data, isLoading, isError } = useIcd10Search(q.trim(), 500);
  return (
    <Shell
      title="Master Diagnosis ICD-10"
      subtitle="Daftar kode diagnosis (data demo)."
      q={q}
      setQ={setQ}
    >
      <table className="w-full text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className={th}>Kode</th>
            <th className={th}>Nama Diagnosis</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          <Status colSpan={2} loading={isLoading} error={isError} empty={data?.length === 0} />
          {data?.map((row) => (
            <tr key={row.code}>
              <td className="px-3 py-2 font-mono text-xs">{row.code}</td>
              <td className="px-3 py-2">{row.name}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Shell>
  );
}

export function MasterDrugsPage() {
  const [q, setQ] = useState("");
  const { data, isLoading, isError } = useDrugSearch(q.trim(), 500);
  return (
    <Shell
      title="Master Obat"
      subtitle="Daftar obat, satuan, dan harga (ilustratif)."
      q={q}
      setQ={setQ}
    >
      <table className="w-full text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className={th}>Nama Obat</th>
            <th className={th}>Satuan</th>
            <th className={th}>Harga</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          <Status colSpan={3} loading={isLoading} error={isError} empty={data?.length === 0} />
          {data?.map((row) => (
            <tr key={row.id}>
              <td className="px-3 py-2">{row.name}</td>
              <td className="px-3 py-2">{row.unit}</td>
              <td className="px-3 py-2">{formatRupiah(row.price)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Shell>
  );
}
