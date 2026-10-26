import { CheckCircle2, Circle, Loader2 } from "lucide-react";

interface JobProgressStepperProps {
  status: "queued" | "processing" | "done" | "error";
  step?: string | null;
  error?: string | null;
}

export function JobProgressStepper({ status, step, error }: JobProgressStepperProps) {
  const steps = [
    { id: "upload", label: "Unggah Audio" },
    { id: "convert", label: "Konversi WAV 16 kHz" },
    { id: "stt", label: "Transkripsi Whisper STT" },
    { id: "done", label: "Hasil Transkrip" },
  ];

  function getStepState(index: number) {
    if (status === "error") {
      return index === 2 ? "error" : "done";
    }
    if (status === "done") {
      return "completed";
    }
    if (status === "processing") {
      if (step === "stt") {
        if (index < 2) return "completed";
        if (index === 2) return "current";
        return "upcoming";
      }
      if (index === 0) return "completed";
      if (index === 1) return "current";
      return "upcoming";
    }
    // queued
    if (index === 0) return "current";
    return "upcoming";
  }

  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {steps.map((s, idx) => {
          const state = getStepState(idx);
          return (
            <div
              key={s.id}
              className={`flex items-center gap-2 rounded-lg border p-2 text-xs font-medium transition-colors ${
                state === "completed"
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : state === "current"
                    ? "border-blue-300 bg-blue-50 text-blue-900 shadow-xs"
                    : state === "error"
                      ? "border-red-200 bg-red-50 text-red-800"
                      : "border-slate-200 bg-white text-slate-400"
              }`}
            >
              {state === "completed" ? (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
              ) : state === "current" ? (
                <Loader2 className="h-4 w-4 shrink-0 animate-spin text-blue-600" />
              ) : (
                <Circle className="h-4 w-4 shrink-0 text-slate-300" />
              )}
              <span className="truncate">{s.label}</span>
            </div>
          );
        })}
      </div>

      {status === "processing" && (
        <div className="flex items-center justify-center gap-2 text-xs text-slate-600">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-emerald-600" />
          <span>Sedang mentranskripsikan audio lisan menggunakan Whisper fine-tuned...</span>
        </div>
      )}

      {status === "error" && error && (
        <div className="rounded-lg bg-red-50 p-3 text-xs text-red-700">
          <span className="font-semibold">Error transkripsi: </span>
          {error}
        </div>
      )}
    </div>
  );
}
