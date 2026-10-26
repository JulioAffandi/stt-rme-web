import { Mic } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function AnamnesisField({
  value,
  onChange,
  onOpenDictation,
}: {
  value: string;
  onChange: (value: string) => void;
  onOpenDictation?: () => void;
}) {
  return (
    <section className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <Label htmlFor="exam-anamnesis" className="text-base font-semibold">
          Anamnesa
        </Label>
        <Button
          type="button"
          onClick={onOpenDictation}
          title="Buka perekam suara dan transkripsi Whisper STT"
          className="bg-blue-600 text-white shadow-xs hover:bg-blue-700 active:scale-95"
        >
          <Mic className="mr-1.5 h-4 w-4" /> Pencatatan Suara
        </Button>
      </div>
      <Textarea
        id="exam-anamnesis"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        maxLength={5000}
        placeholder="Keluhan utama, riwayat penyakit sekarang..."
        className="min-h-28 text-sm"
      />
    </section>
  );
}
