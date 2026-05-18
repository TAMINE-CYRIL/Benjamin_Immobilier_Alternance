/**
 * Formate l'affichage d'une valeur monétaire en euros.
 * @param {*} value La valeur à formater.
 * @returns Une chaîne de caractères représentant la valeur formatée en euros, ou "-" si la valeur est nulle ou indéfinie.
 */
export function formatMoney(value) {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Formate l'affichage d'un score.
 * @param {*} value La valeur à formater.
 * @returns Une chaîne de caractères représentant la valeur formatée, ou "-" si la valeur est nulle ou indéfinie.
 */
export function formatScore(value) {
  if (value === null || value === undefined || value === "") return "-";
  const score = Number(value);
  if (!Number.isFinite(score)) return "-";
  return new Intl.NumberFormat("fr-FR", {
    maximumFractionDigits: 1,
  }).format(score);
}

/**
 * Détermine le niveau d'un score.
 * @param {*} value La valeur du score.
 * @returns Une chaîne de caractères représentant le niveau du score, ou "unknown" si la valeur est nulle ou indéfinie.
 */
export function getScoreLevel(value) {
  const score = Number(value);
  if (!Number.isFinite(score)) return "unknown";
  if (score >= 70) return "high";
  if (score >= 50) return "medium";
  return "low";
}
