import type { DictationEntity } from "@/types";

interface EntityBadgeProps {
  entity: DictationEntity;
  onClick?: () => void;
  interactive?: boolean;
}

export function EntityBadge({ entity, onClick, interactive = false }: EntityBadgeProps) {
  const labelColor = getLabelColor(entity.label);
  const isAbsent = entity.assertion === "ABSENT";
  const isPossible = entity.assertion === "POSSIBLE";

  return (
    <span
      onClick={interactive ? onClick : undefined}
      title={`Label: ${entity.label} | Status: ${entity.assertion}${interactive ? " (Klik untuk ubah)" : ""}`}
      className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-xs font-medium transition-all ${labelColor} ${
        interactive ? "cursor-pointer hover:ring-2 hover:ring-emerald-400" : ""
      }`}
    >
      <span className={isAbsent ? "line-through opacity-70" : ""}>{entity.text}</span>

      {/* Indikator Assertion (+, -, ?) */}
      <span
        className={`inline-flex h-3.5 w-3.5 items-center justify-center rounded-full text-[10px] font-bold ${
          isAbsent
            ? "bg-red-500 text-white"
            : isPossible
              ? "bg-amber-500 text-white"
              : "bg-emerald-600 text-white"
        }`}
      >
        {isAbsent ? "−" : isPossible ? "?" : "+"}
      </span>

      <span className="text-[10px] uppercase opacity-60">[{entity.label}]</span>
    </span>
  );
}

export function getLabelColor(label: string): string {
  switch (label.toUpperCase()) {
    case "GEJALA":
      return "bg-amber-100 text-amber-900 border-amber-300";
    case "TANDA":
      return "bg-cyan-100 text-cyan-900 border-cyan-300";
    case "DIAGNOSIS":
      return "bg-emerald-100 text-emerald-900 border-emerald-300";
    case "OBAT":
      return "bg-blue-100 text-blue-900 border-blue-300";
    case "TINDAKAN":
      return "bg-purple-100 text-purple-900 border-purple-300";
    case "PENUNJANG":
      return "bg-slate-100 text-slate-800 border-slate-300";
    default:
      return "bg-slate-100 text-slate-700 border-slate-200";
  }
}
