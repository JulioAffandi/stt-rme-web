import { FileAudio, PlayCircle, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDictationSamples } from "@/hooks/useDictation";
import type { DictationSample } from "@/types";

interface SamplePickerProps {
  onSelectSample: (sample: DictationSample) => void;
  disabled?: boolean;
}

export function SamplePicker({ onSelectSample, disabled }: SamplePickerProps) {
  const { data: samples, isLoading, isError } = useDictationSamples();

  if (isLoading) {
    return <p className="py-4 text-center text-xs text-slate-500">Memuat contoh audio...</p>;
  }

  if (isError || !samples || samples.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-4 text-center text-xs text-slate-500">
        Belum ada contoh audio demo di server.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-1.5 text-xs font-medium text-slate-600">
        <Sparkles className="h-4 w-4 text-emerald-600" />
        <span>Pilih contoh rekaman klinis untuk demonstrasi sidang tanpa merekam lisan:</span>
      </div>

      <div className="grid gap-2.5">
        {samples.map((s) => (
          <div
            key={s.id}
            className="flex flex-col justify-between gap-2 rounded-lg border border-slate-200 bg-white p-3 shadow-xs transition-all hover:border-emerald-500 hover:shadow-sm sm:flex-row sm:items-center"
          >
            <div className="min-w-0 space-y-1">
              <div className="flex items-center gap-2">
                <FileAudio className="h-4 w-4 shrink-0 text-emerald-600" />
                <h4 className="truncate text-sm font-semibold text-slate-800">{s.title}</h4>
                <Badge variant="outline" className="text-[10px]">
                  {s.duration_sec.toFixed(0)}s
                </Badge>
              </div>
              <p className="line-clamp-2 text-xs text-slate-500">{s.description}</p>
            </div>

            <Button
              type="button"
              size="sm"
              disabled={disabled}
              onClick={() => onSelectSample(s)}
              className="shrink-0 bg-emerald-600 text-white hover:bg-emerald-700"
            >
              <PlayCircle className="mr-1 h-4 w-4" />
              Pakai Sampel Ini
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
