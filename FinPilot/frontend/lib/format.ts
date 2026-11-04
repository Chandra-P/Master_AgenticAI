export function currency(value: string | number | null | undefined, cents = false): string {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return 'Not available';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: cents ? 2 : 0 }).format(Number(value));
}
export function validateScenario(values: Record<string, string>): string | null {
  for (const [key, raw] of Object.entries(values)) {
    const n = Number(raw);
    if (!raw.trim() || !Number.isFinite(n) || n < 0) return 'Enter a valid nonnegative amount for each change.';
    if (key === 'income_reduction_pct' && n > 100) return 'Income reduction must be between 0 and 100%.';
  }
  return null;
}
export function month(value: string) { return new Date(`${value}T12:00:00`).toLocaleDateString('en-US',{month:'short'}); }
