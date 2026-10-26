import { Search } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import type { UseQueryResult } from "@tanstack/react-query";

import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";

function useDebounced<T>(value: T, delay = 250): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

/** Modal pencarian master data (ICD-10 / obat / tindakan). */
export function PickerModal<T>({
  open,
  title,
  placeholder,
  useSearch,
  getKey,
  renderItem,
  onPick,
  onClose,
}: {
  open: boolean;
  title: string;
  placeholder: string;
  useSearch: (q: string) => UseQueryResult<T[]>;
  getKey: (item: T) => string | number;
  renderItem: (item: T) => ReactNode;
  onPick: (item: T) => void;
  onClose: () => void;
}) {
  const [q, setQ] = useState("");
  const debounced = useDebounced(q);
  const { data, isLoading, isError } = useSearch(debounced);

  useEffect(() => {
    if (!open) setQ("");
  }, [open]);

  return (
    <Modal open={open} title={title} onClose={onClose}>
      <div className="relative mb-3">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
        <Input
          autoFocus
          aria-label={placeholder}
          placeholder={placeholder}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="pl-9"
        />
      </div>
      {isLoading && <p className="py-6 text-center text-sm text-slate-500">Memuat...</p>}
      {isError && (
        <p role="alert" className="py-6 text-center text-sm text-red-600">
          Gagal memuat data.
        </p>
      )}
      {data && data.length === 0 && (
        <p className="py-6 text-center text-sm text-slate-500">Belum ada data</p>
      )}
      <ul className="divide-y rounded-md border">
        {data?.map((item) => (
          <li key={getKey(item)}>
            <button
              type="button"
              onClick={() => onPick(item)}
              className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-emerald-50 focus-visible:bg-emerald-50 focus-visible:outline-none"
            >
              {renderItem(item)}
            </button>
          </li>
        ))}
      </ul>
    </Modal>
  );
}
