import axios from "axios";

import type { ApiErrorBody } from "@/types";

/**
 * Client API. Base URL relatif — di dev lewat proxy Vite (/api -> backend),
 * di produksi bisa di-proxy oleh server static yang sama.
 * `withCredentials` agar httpOnly cookie JWT ikut terkirim.
 */
export const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

/** Ambil pesan error yang ramah dari respons API. */
export function getApiErrorMessage(error: unknown, fallback = "Terjadi kesalahan"): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiErrorBody | undefined;
    if (data && typeof data.detail === "string" && data.detail) {
      return data.detail;
    }
    if (error.code === "ERR_NETWORK") {
      return "Tidak dapat terhubung ke server. Pastikan backend berjalan.";
    }
  }
  return fallback;
}
