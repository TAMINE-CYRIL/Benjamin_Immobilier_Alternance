import React from "react";
import { enrichmentStatusLabels } from "../constants";
import { formatDate, formatDistance, formatMoney } from "../utils";


/**
 * Composant de panneau de détails pour afficher les informations d'une annonce.
 * @param {*} annonce, loading, onClose 
 * @returns 
 */
export function DetailPanel({ annonce, loading, onClose }) {
  if (!annonce && !loading) return null;
  const enrichment = annonce?.enrichment || {};
  const scoring = annonce?.score_details || {};
  const components = scoring.components || {};
  const componentLabels = {
    market_discount: "Prix et décote",
    land_potential: "Potentiel foncier",
    liquidity: "Liquidité",
    listing_signals: "Signaux de l’annonce",
    energy: "Énergie",
  };

  return (
    <aside className="detail-panel">
      <button className="icon-button" onClick={onClose} aria-label="Fermer">x</button>
      {loading ? (
        <p>Chargement...</p>
      ) : (
        <>
          <p className="eyebrow">{annonce.source_site || "Annonce"}</p>
          <h2>{annonce.title || "Sans titre"}</h2>
          <dl>
            <dt>Score</dt><dd>{annonce.score ?? "-"}</dd>
            <dt>Prix</dt><dd>{formatMoney(annonce.price)}</dd>
            <dt>Surface</dt><dd>{annonce.surface ? `${annonce.surface} m2` : "-"}</dd>
            <dt>Pièces</dt><dd>{annonce.rooms ?? "-"}</dd>
            <dt>Prix/m2</dt><dd>{annonce.price_m2 ? `${Math.round(annonce.price_m2)} EUR` : "-"}</dd>
            <dt>Localisation</dt><dd>{[annonce.city, annonce.zip_code, annonce.department].filter(Boolean).join(" - ") || "-"}</dd>
            <dt>Type</dt><dd>{annonce.type_bien || "-"}</dd>
            <dt>DPE</dt><dd>{annonce.energy_class || "-"}</dd>
            <dt>Agence</dt><dd>{annonce.agency || "-"}</dd>
            <dt>Première détection</dt><dd>{formatDate(annonce.first_seen)}</dd>
            <dt>Dernière détection</dt><dd>{formatDate(annonce.last_seen)}</dd>
            {annonce.distance_m !== undefined ? <><dt>Distance</dt><dd>{formatDistance(annonce.distance_m)}</dd></> : null}
          </dl>
          <section className="detail-section score-explanation">
            <p className="eyebrow">Justification du score</p>
            <div className="score-summary">
              <strong>{annonce.score ?? "-"} / 100</strong>
              <span>Confiance : {annonce.score_confidence ?? 0} %</span>
              <span className={`risk-pill risk-${annonce.score_risk_level || "medium"}`}>
                Risque {annonce.score_risk_level === "low" ? "faible" : annonce.score_risk_level === "high" ? "élevé" : "moyen"}
              </span>
            </div>
            <div className="score-components">
              {Object.entries(componentLabels).map(([key, label]) => (
                <div className="score-component" key={key}>
                  <span>{label}</span>
                  <strong>{components[key] ?? "-"} / {{
                    market_discount: 40,
                    land_potential: 30,
                    liquidity: 10,
                    listing_signals: 15,
                    energy: 5,
                  }[key]}</strong>
                </div>
              ))}
            </div>
            {scoring.reasons?.length ? (
              <>
                <h3>Éléments favorables et constats</h3>
                <ul className="score-reasons">
                  {scoring.reasons.map((reason, index) => <li key={`${reason}-${index}`}>{reason}</li>)}
                </ul>
              </>
            ) : null}
            {scoring.risks?.length ? (
              <>
                <h3>Points de vigilance</h3>
                <ul className="score-risks">
                  {scoring.risks.map((risk, index) => <li key={`${risk}-${index}`}>{risk}</li>)}
                </ul>
              </>
            ) : null}
          </section>
          <section className="detail-section">
            <p className="eyebrow">Enrichissement foncier</p>
            <dl>
              <dt>Statut</dt>
              <dd><span className={`status-pill status-${enrichment.status || "pending"}`}>{enrichmentStatusLabels[enrichment.status] || "En attente"}</span></dd>
              <dt>Diagnostic</dt><dd>{enrichment.diagnostic_message || "-"}</dd>
              <dt>Géocodage</dt>
              <dd>{[enrichment.geocode_status, enrichment.geocode_score ? `score ${Number(enrichment.geocode_score).toFixed(2)}` : null, enrichment.geocode_type].filter(Boolean).join(" - ") || "-"}</dd>
              <dt>Requête</dt><dd>{enrichment.geocode_query || "-"}</dd>
              <dt>Cadastre</dt><dd>{enrichment.cadastre_status || "-"}</dd>
              <dt>Coordonnées</dt>
              <dd>{enrichment.latitude && enrichment.longitude ? `${enrichment.latitude}, ${enrichment.longitude}` : "-"}</dd>
              <dt>Parcelle</dt><dd>{enrichment.parcel_key || "-"}</dd>
              <dt>Surface parcelle</dt><dd>{enrichment.parcel_surface ? `${enrichment.parcel_surface} m2` : "-"}</dd>
              <dt>Commune cadastre</dt><dd>{enrichment.parcel_commune_code || "-"}</dd>
              <dt>Erreur</dt><dd>{enrichment.error || "-"}</dd>
              <dt>Mis à jour</dt><dd>{enrichment.enriched_at || "-"}</dd>
            </dl>
          </section>
          {annonce.url ? <a className="source-link" href={annonce.url} target="_blank" rel="noreferrer">Ouvrir la source</a> : null}
        </>
      )}
    </aside>
  );
}
