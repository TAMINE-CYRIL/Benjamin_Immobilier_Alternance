import React from "react";
import { businessStatusLabels, enrichmentStatusLabels } from "../constants";
import { formatDistance, formatMoney, formatScore, getScoreLevel } from "../utils";

/**
 * Vérifie si une annonce a des coordonnées valides.
 * @param {*} annonce 
 * @returns true si l'annonce a des coordonnées valides, false sinon.
 */
function hasValidCoords(annonce) {
  const rawLatitude = annonce.enrichment?.latitude;
  const rawLongitude = annonce.enrichment?.longitude;
  if (rawLatitude === null || rawLatitude === undefined || rawLatitude === "") return false;
  if (rawLongitude === null || rawLongitude === undefined || rawLongitude === "") return false;

  const latitude = Number(rawLatitude);
  const longitude = Number(rawLongitude);
  return Number.isFinite(latitude) && Number.isFinite(longitude);
}

/**
 * Composant représentant la liste des annonces.
 * @param {*} annonces, selectedId, onSelect 
 * @returns Une liste d'annonces avec leurs informations principales, leur score et leur statut d'enrichissement. Permet de sélectionner une annonce pour voir plus de détails.
 */
export function AnnoncesList({ annonces, selectedId, onSelect }) {
  if (!annonces.length) {
    return <div className="empty">Aucune annonce ne correspond aux filtres.</div>;
  }

  return (
    <div className="annonces-list">
      {annonces.map((annonce) => {
        const located = hasValidCoords(annonce);
        const selected = annonce.id === selectedId;

        return (
          <article className={`annonce-card${selected ? " annonce-card-selected" : ""}`} key={annonce.id}>
            <button type="button" className="annonce-card-button" onClick={() => onSelect(annonce.id)}>
              <span className={`score-pill score-${getScoreLevel(annonce.score)}`}>
                <strong>{formatScore(annonce.score)}</strong>
                <span>Score</span>
              </span>
              <span className="annonce-card-main">
                <strong>{annonce.title || "Annonce sans titre"}</strong>
                <span>{[annonce.city, annonce.zip_code].filter(Boolean).join(" ") || "Localisation inconnue"}</span>
              </span>
              <span className="annonce-card-meta">
                <span>{formatMoney(annonce.price)}</span>
                <span>{annonce.surface ? `${annonce.surface} m2` : "Surface inconnue"}</span>
                <span>{annonce.price_m2 ? `${Math.round(annonce.price_m2)} EUR/m2` : "Prix/m2 inconnu"}</span>
                {annonce.distance_m !== undefined ? <span>{formatDistance(annonce.distance_m)}</span> : null}
              </span>
              <span className="annonce-card-badges">
                {annonce.is_favorite ? <span className="favorite-pill" title="Favori">♥</span> : null}
                <span className={`business-pill business-${annonce.business_status || "new"}`}>
                  {businessStatusLabels[annonce.business_status] || "Nouveau"}
                </span>
                <span className={`status-pill status-${annonce.enrichment?.status || "pending"}`}>
                  {enrichmentStatusLabels[annonce.enrichment?.status] || "En attente"}
                </span>
              </span>
            </button>
          </article>
        );
      })}
    </div>
  );
}
