import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-50 p-4 text-center">
      <p className="text-6xl font-bold text-emerald-600">404</p>
      <h1 className="text-xl font-semibold text-slate-800">Halaman tidak ditemukan</h1>
      <p className="text-sm text-slate-500">Alamat yang Anda buka tidak tersedia.</p>
      <Link
        to="/"
        className="mt-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        Kembali ke Dashboard
      </Link>
    </div>
  );
}
