export function formatMoney(value) {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatScore(value) {
  if (value === null || value === undefined || value === "") return "-";
  const score = Number(value);
  if (!Number.isFinite(score)) return "-";
  return new Intl.NumberFormat("fr-FR", {
    maximumFractionDigits: 1,
  }).format(score);
}

export function getScoreLevel(value) {
  const score = Number(value);
  if (!Number.isFinite(score)) return "unknown";
  if (score >= 70) return "high";
  if (score >= 50) return "medium";
  return "low";
}
