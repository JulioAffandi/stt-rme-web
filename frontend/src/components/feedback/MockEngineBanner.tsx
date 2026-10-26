import { useQuery } from "@tanstack/react-query";
import { FlaskConical } from "lucide-react";

import { api } from "@/lib/api";
import type { HealthInfo } from "@/types";

/**
 * Banner mode demo: tampil bila backend melaporkan NLP_ENGINE=mock
 * (Bagian 6 rancangan — modul NLP berupa aturan sederhana).
 */
export function MockEngineBanner() {
  const { data } = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data } = await api.get<HealthInfo>("/health");
      return data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  if (!data || data.nlp_engine !== "mock") {
    return null;
  }

  return (
    <div className="flex items-center gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-900 md:px-6">
      <FlaskConical className="h-4 w-4 shrink-0" />
      <span>
        <strong>Mode demo:</strong> modul NLP menggunakan aturan sederhana
      </span>
    </div>
  );
}
