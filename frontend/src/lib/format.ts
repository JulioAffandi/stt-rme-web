const MONTHS_ID = [
  "Januari",
  "Februari",
  "Maret",
  "April",
  "Mei",
  "Juni",
  "Juli",
  "Agustus",
  "September",
  "Oktober",
  "November",
  "Desember",
];

/** Umur dalam tahun penuh dari tanggal lahir (YYYY-MM-DD). */
export function calcAge(birthDate: string, today: Date = new Date()): number {
  const [y, m, d] = birthDate.split("-").map(Number);
  let age = today.getFullYear() - y;
  const beforeBirthday =
    today.getMonth() + 1 < m || (today.getMonth() + 1 === m && today.getDate() < d);
  if (beforeBirthday) age -= 1;
  return Math.max(age, 0);
}

/** "1985-03-12" -> "12 Maret 1985". */
export function formatDate(value: string): string {
  const [y, m, d] = value.slice(0, 10).split("-").map(Number);
  if (!y || !m || !d) return value;
  return `${d} ${MONTHS_ID[m - 1]} ${y}`;
}

export function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("id-ID", { dateStyle: "medium", timeStyle: "short" });
}

export function formatRupiah(value: number): string {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function genderLabel(gender: "M" | "F"): string {
  return gender === "M" ? "Laki-laki" : "Perempuan";
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

/** 12 organ pemeriksaan fisik — harus sama dengan BODY_SITES di backend. */
export const BODY_SITES = [
  "Kepala",
  "Mata",
  "Telinga",
  "Leher",
  "Thorax",
  "Paru",
  "Jantung",
  "Abdomen",
  "Inguinal",
  "Ekstremitas Atas",
  "Ekstremitas Bawah",
  "Kulit",
] as const;
