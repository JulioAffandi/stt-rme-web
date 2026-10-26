import { LogOut, Menu } from "lucide-react";

import { useLogout, useMe } from "@/hooks/useAuth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function Topbar({ onMenuClick }: { onMenuClick: () => void }) {
  const { data: user } = useMe();
  const logout = useLogout();

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between gap-3 border-b bg-white px-4 md:px-6">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={onMenuClick}
          aria-label="Buka menu"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <div>
          <p className="text-sm font-semibold text-slate-800">Klinik Demo</p>
          <p className="text-xs text-slate-500">Pencatatan rekam medis elektronik</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {user && (
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium text-slate-800">{user.full_name}</p>
            <Badge variant="secondary" className="mt-0.5 capitalize">
              {user.role === "doctor" ? "Dokter" : "Admin"}
            </Badge>
          </div>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={() => logout.mutate()}
          disabled={logout.isPending}
        >
          <LogOut className="h-4 w-4" />
          Keluar
        </Button>
      </div>
    </header>
  );
}
