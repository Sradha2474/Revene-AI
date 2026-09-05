import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatInr(n: number | string | null | undefined) {
  const v = Number(n || 0);
  return `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}

export function shortId(id: string | number | null | undefined) {
  if (id == null) return "—";
  const s = String(id);
  return s.length > 12 ? `${s.slice(0, 8)}…` : s;
}
