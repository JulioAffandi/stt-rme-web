import { Plus, Sparkles, Trash2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useDrugSearch, useIcd10Search, useProcedureSearch } from "@/hooks/useRme";
import { formatRupiah } from "@/lib/format";
import type { DataSource } from "@/types";

import type { DiagnosisRow, MedicationRow, ProcedureRow } from "./examState";
import { PickerModal } from "./PickerModal";

const th = "px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600";
const td = "px-3 py-2 text-sm";

function AiMark({ source }: { source: DataSource }) {
  if (source !== "ai") return null;
  return (
    <span
      title="Terisi otomatis oleh AI — verifikasi dokter"
      className="ml-1 inline-flex align-middle text-emerald-600"
    >
      <Sparkles className="h-3.5 w-3.5" />
    </span>
  );
}

function SectionHeader({
  title,
  onAdd,
  addLabel,
}: {
  title: string;
  onAdd: () => void;
  addLabel: string;
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      <Button type="button" onClick={onAdd} className="bg-blue-600 text-white hover:bg-blue-700">
        <Plus /> {addLabel}
      </Button>
    </div>
  );
}

function RemoveButton({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <Button type="button" variant="ghost" size="icon" onClick={onClick} aria-label={label}>
      <Trash2 className="h-4 w-4 text-red-600" />
    </Button>
  );
}

function EmptyRow({ colSpan }: { colSpan: number }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-3 py-6 text-center text-sm text-slate-500">
        Belum ada data
      </td>
    </tr>
  );
}

export function DiagnosisTable({
  rows,
  onChange,
}: {
  rows: DiagnosisRow[];
  onChange: (rows: DiagnosisRow[]) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <section className="space-y-2">
      <SectionHeader title="Diagnosa" addLabel="Input Diagnosa" onAdd={() => setOpen(true)} />
      <div className="overflow-x-auto rounded-md border">
        <table className="w-full">
          <thead className="bg-slate-50">
            <tr>
              <th className={th}>No</th>
              <th className={th}>Kode ICD</th>
              <th className={th}>Nama Diagnosa</th>
              <th className={th}>
                <span className="sr-only">Aksi</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.length === 0 && <EmptyRow colSpan={4} />}
            {rows.map((row, i) => (
              <tr key={`${row.icd_code}-${i}`}>
                <td className={td}>{i + 1}</td>
                <td className={td}>{row.icd_code ?? "-"}</td>
                <td className={td}>
                  {row.name}
                  <AiMark source={row.source} />
                </td>
                <td className={`${td} text-right`}>
                  <RemoveButton
                    label={`Hapus diagnosa ${row.name}`}
                    onClick={() => onChange(rows.filter((_, idx) => idx !== i))}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <PickerModal
        open={open}
        title="Cari Diagnosa (ICD-10)"
        placeholder="Ketik kode atau nama diagnosa"
        useSearch={useIcd10Search}
        getKey={(item) => item.code}
        renderItem={(item) => (
          <>
            <span>{item.name}</span>
            <span className="font-mono text-xs text-slate-500">{item.code}</span>
          </>
        )}
        onPick={(item) => {
          if (!rows.some((r) => r.icd_code === item.code)) {
            onChange([...rows, { icd_code: item.code, name: item.name, source: "manual" }]);
          }
          setOpen(false);
        }}
        onClose={() => setOpen(false)}
      />
    </section>
  );
}

export function MedicationTable({
  rows,
  doctorName,
  onChange,
}: {
  rows: MedicationRow[];
  doctorName: string | null;
  onChange: (rows: MedicationRow[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const total = rows.reduce((sum, r) => sum + r.drug.price * r.quantity, 0);

  function setQuantity(index: number, raw: string) {
    const quantity = Math.min(9999, Math.max(1, Math.floor(Number(raw)) || 1));
    onChange(rows.map((r, i) => (i === index ? { ...r, quantity } : r)));
  }

  return (
    <section className="space-y-2">
      <SectionHeader title="Obat" addLabel="Input Obat" onAdd={() => setOpen(true)} />
      <div className="overflow-x-auto rounded-md border">
        <table className="w-full">
          <thead className="bg-slate-50">
            <tr>
              <th className={th}>No</th>
              <th className={th}>Nama Obat</th>
              <th className={th}>Dokter</th>
              <th className={th}>Harga</th>
              <th className={th}>Jumlah</th>
              <th className={th}>Subtotal</th>
              <th className={th}>
                <span className="sr-only">Aksi</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.length === 0 && <EmptyRow colSpan={7} />}
            {rows.map((row, i) => (
              <tr key={row.drug.id}>
                <td className={td}>{i + 1}</td>
                <td className={td}>
                  {row.drug.name}
                  <AiMark source={row.source} />
                </td>
                <td className={td}>{doctorName ?? "-"}</td>
                <td className={td}>{formatRupiah(row.drug.price)}</td>
                <td className={td}>
                  <input
                    type="number"
                    min={1}
                    max={9999}
                    aria-label={`Jumlah ${row.drug.name}`}
                    value={row.quantity}
                    onChange={(e) => setQuantity(i, e.target.value)}
                    className="h-8 w-20 rounded-md border border-input px-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
                  />
                </td>
                <td className={td}>{formatRupiah(row.drug.price * row.quantity)}</td>
                <td className={`${td} text-right`}>
                  <RemoveButton
                    label={`Hapus obat ${row.drug.name}`}
                    onClick={() => onChange(rows.filter((_, idx) => idx !== i))}
                  />
                </td>
              </tr>
            ))}
          </tbody>
          {rows.length > 0 && (
            <tfoot className="bg-slate-50">
              <tr>
                <td colSpan={5} className={`${td} text-right font-semibold`}>
                  Total Obat
                </td>
                <td colSpan={2} className={`${td} font-semibold`}>
                  {formatRupiah(total)}
                </td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
      <PickerModal
        open={open}
        title="Cari Obat"
        placeholder="Ketik nama obat"
        useSearch={useDrugSearch}
        getKey={(item) => item.id}
        renderItem={(item) => (
          <>
            <span>
              {item.name} <span className="text-xs text-slate-500">({item.unit})</span>
            </span>
            <span className="text-xs text-slate-500">{formatRupiah(item.price)}</span>
          </>
        )}
        onPick={(item) => {
          if (!rows.some((r) => r.drug.id === item.id)) {
            onChange([...rows, { drug: item, quantity: 1, source: "manual" }]);
          }
          setOpen(false);
        }}
        onClose={() => setOpen(false)}
      />
    </section>
  );
}

export function ProcedureTable({
  rows,
  onChange,
}: {
  rows: ProcedureRow[];
  onChange: (rows: ProcedureRow[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const total = rows.reduce((sum, r) => sum + r.procedure.price, 0);
  return (
    <section className="space-y-2">
      <SectionHeader title="Tindakan" addLabel="Input Tindakan" onAdd={() => setOpen(true)} />
      <div className="overflow-x-auto rounded-md border">
        <table className="w-full">
          <thead className="bg-slate-50">
            <tr>
              <th className={th}>No</th>
              <th className={th}>Nama Tindakan</th>
              <th className={th}>Biaya</th>
              <th className={th}>
                <span className="sr-only">Aksi</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {rows.length === 0 && <EmptyRow colSpan={4} />}
            {rows.map((row, i) => (
              <tr key={row.procedure.id}>
                <td className={td}>{i + 1}</td>
                <td className={td}>
                  {row.procedure.name}
                  <AiMark source={row.source} />
                </td>
                <td className={td}>{formatRupiah(row.procedure.price)}</td>
                <td className={`${td} text-right`}>
                  <RemoveButton
                    label={`Hapus tindakan ${row.procedure.name}`}
                    onClick={() => onChange(rows.filter((_, idx) => idx !== i))}
                  />
                </td>
              </tr>
            ))}
          </tbody>
          {rows.length > 0 && (
            <tfoot className="bg-slate-50">
              <tr>
                <td colSpan={2} className={`${td} text-right font-semibold`}>
                  Total Tindakan
                </td>
                <td colSpan={2} className={`${td} font-semibold`}>
                  {formatRupiah(total)}
                </td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
      <PickerModal
        open={open}
        title="Cari Tindakan"
        placeholder="Ketik nama tindakan"
        useSearch={useProcedureSearch}
        getKey={(item) => item.id}
        renderItem={(item) => (
          <>
            <span>{item.name}</span>
            <span className="text-xs text-slate-500">{formatRupiah(item.price)}</span>
          </>
        )}
        onPick={(item) => {
          if (!rows.some((r) => r.procedure.id === item.id)) {
            onChange([...rows, { procedure: item, source: "manual" }]);
          }
          setOpen(false);
        }}
        onClose={() => setOpen(false)}
      />
    </section>
  );
}
