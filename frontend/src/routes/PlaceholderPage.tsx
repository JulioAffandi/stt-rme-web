import { Construction } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

/** Halaman cadangan untuk rute yang diimplementasikan pada fase berikutnya. */
export function PlaceholderPage({
  title,
  phase,
  description,
}: {
  title: string;
  phase: string;
  description?: string;
}) {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">{title}</h1>
        <p className="text-sm text-slate-500">Bagian dari alur Kunjungan Rawat Jalan.</p>
      </div>

      <Card className="border-dashed">
        <CardHeader className="flex flex-row items-center gap-3 space-y-0">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-200">
            <Construction className="h-5 w-5 text-slate-600" />
          </div>
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            <CardDescription>
              Dikerjakan pada <strong>{phase}</strong>
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="text-sm text-slate-600">
          {description ??
            "Halaman ini akan diisi lengkap (form, tabel, dan aksi) pada fase tersebut. Rancangan & kontrak API sudah disiapkan sejak Fase 1."}
        </CardContent>
      </Card>
    </div>
  );
}
