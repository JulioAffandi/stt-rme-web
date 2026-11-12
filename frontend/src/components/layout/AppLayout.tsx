import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar, Topbar } from "@/components/layout";
import { MockEngineBanner } from "@/components/feedback/MockEngineBanner";

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar open={mobileOpen} onClose={() => setMobileOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col overflow-y-auto">
        <Topbar onMenuClick={() => setMobileOpen(true)} />
        <MockEngineBanner />
        <main className="flex-1 p-4 md:p-6">
          <Outlet />
        </main>
        <footer className="border-t bg-white px-4 py-3 text-center text-xs text-slate-500 md:px-6">
          Data demo, bukan data pasien sebenarnya. &middot; RME STT-NLP &middot; Fase 2
        </footer>
      </div>
    </div>
  );
}
