import {
  Activity,
  FileText,
  LayoutDashboard,
  Pill,
  Stethoscope,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface NavItemData {
  to: string;
  label: string;
  icon: typeof Activity;
  end: boolean;
}

const navSections: { label: string | null; items: NavItemData[] }[] = [
  {
    label: null,
    items: [{ to: "/", label: "Dashboard", icon: LayoutDashboard, end: true }],
  },
  {
    label: "Data Master",
    items: [
      { to: "/master/icd10", label: "Diagnosis ICD-10", icon: FileText, end: false },
      { to: "/master/drugs", label: "Obat", icon: Pill, end: false },
    ],
  },
  {
    label: "Kunjungan Rawat Jalan",
    items: [
      { to: "/patients/new", label: "Pendaftaran Pasien Baru", icon: UserPlus, end: false },
      { to: "/patients", label: "Pendaftaran Pasien Lama", icon: Users, end: true },
      { to: "/exam", label: "Pemeriksaan Dokter", icon: Stethoscope, end: false },
    ],
  },
  {
    label: "Evaluasi",
    items: [{ to: "/pipeline-logs", label: "Log Pipeline", icon: Activity, end: false }],
  },
];

function NavItem({
  to,
  label,
  icon: Icon,
  end,
  onNavigate,
}: NavItemData & { onNavigate?: () => void }) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
          isActive
            ? "bg-emerald-600 text-white shadow-sm"
            : "text-emerald-100/90 hover:bg-emerald-700/60 hover:text-white",
        )
      }
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span>{label}</span>
    </NavLink>
  );
}

export function Sidebar({
  open,
  onClose,
  className,
}: {
  open?: boolean;
  onClose?: () => void;
  className?: string;
}) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-emerald-900 text-white transition-transform duration-200",
          "md:static md:h-full md:shrink-0 md:z-auto md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
          className,
        )}
      >
        <div className="flex items-center justify-between gap-2 px-4 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600">
              <Stethoscope className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold leading-tight">Klinik Demo</p>
              <p className="text-xs text-emerald-200/80">RME STT-NLP</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="text-emerald-100 hover:bg-emerald-700 hover:text-white md:hidden"
            onClick={onClose}
            aria-label="Tutup menu"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <nav className="flex-1 space-y-5 overflow-y-auto px-3 pb-4">
          {navSections.map((section) => (
            <div key={section.label ?? "umum"}>
              {section.label && (
                <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-emerald-300/70">
                  {section.label}
                </p>
              )}
              <div className="space-y-1">
                {section.items.map((item) => (
                  <NavItem key={item.to} {...item} onNavigate={onClose} />
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-emerald-800 px-4 py-3 text-[11px] text-emerald-200/70">
          Data demo, bukan data pasien sebenarnya.
        </div>
      </aside>
    </>
  );
}
