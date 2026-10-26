import { Sparkles } from "lucide-react";

import { Input } from "@/components/ui/input";
import { BODY_SITES } from "@/lib/format";

import { NORMAL_TEXT, type PhysicalMap } from "./examState";

/** 12 baris organ: checkbox + input. Tak dicentang => "Normal" & disabled. */
export function PhysicalExamList({
  value,
  onChange,
}: {
  value: PhysicalMap;
  onChange: (value: PhysicalMap) => void;
}) {
  function toggle(site: string, checked: boolean) {
    onChange({
      ...value,
      [site]: { checked, finding: checked ? "" : NORMAL_TEXT },
    });
  }

  function setFinding(site: string, finding: string) {
    onChange({ ...value, [site]: { ...value[site], finding } });
  }

  return (
    <section className="space-y-2">
      <h3 className="text-base font-semibold text-slate-800">Pemeriksaan Fisik</h3>
      <p className="text-xs text-slate-500">
        Centang organ untuk mengisi temuan abnormal. Tanpa centang dianggap Normal.
      </p>
      <div className="divide-y rounded-md border">
        {BODY_SITES.map((site) => {
          const row = value[site] ?? { checked: false, finding: NORMAL_TEXT };
          const inputId = `exam-physical-${site.replace(/\s+/g, "-").toLowerCase()}`;
          return (
            <div
              key={site}
              className="grid grid-cols-[1fr] items-center gap-2 px-3 py-2 sm:grid-cols-[12rem_1fr]"
            >
              <label
                htmlFor={`${inputId}-check`}
                className="flex items-center gap-2 text-sm font-medium"
              >
                <input
                  id={`${inputId}-check`}
                  type="checkbox"
                  checked={row.checked}
                  onChange={(e) => toggle(site, e.target.checked)}
                  className="h-4 w-4 accent-emerald-600"
                />
                <span>{site}</span>
                {row.source === "ai" && row.checked && (
                  <span
                    title="Terisi otomatis oleh AI — verifikasi dokter"
                    className="inline-flex items-center text-emerald-600"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                  </span>
                )}
              </label>
              <Input
                id={inputId}
                aria-label={`Temuan ${site}`}
                value={row.finding}
                disabled={!row.checked}
                onChange={(e) => setFinding(site, e.target.value)}
                maxLength={500}
                placeholder={row.checked ? "Tuliskan temuan..." : undefined}
              />
            </div>
          );
        })}
      </div>
    </section>
  );
}
