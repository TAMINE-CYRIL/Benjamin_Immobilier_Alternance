import React from "react";
import { businessStatusLabels, businessStatusOptions, enrichmentStatusLabels } from "../constants";
import { formatDate, formatDistance, formatMoney } from "../utils";


function isUsefulValue(value) {
  return value !== null && value !== undefined && value !== "";
}

/**
 * Composant de panneau de détails pour afficher les informations d'une annonce.
 * @param {*} annonce, loading, onClose 
 * @returns 
 */
export function DetailPanel({ annonce, loading, onClose, onTrackingChange, trackingLoading = false }) {
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
          <section className="tracking-panel">
            <button
              type="button"
              className={annonce.is_favorite ? "favorite-icon-button active" : "favorite-icon-button"}
              disabled={trackingLoading}
              aria-label={annonce.is_favorite ? "Retirer des favoris" : "Ajouter aux favoris"}
              title={annonce.is_favorite ? "Retirer des favoris" : "Ajouter aux favoris"}
              onClick={() => onTrackingChange?.({ is_favorite: !annonce.is_favorite })}
            >
              {annonce.is_favorite ? "♥" : "♡"}
            </button>
            <label>
              <span>Statut commercial</span>
              <select
                value={annonce.business_status || "new"}
                disabled={trackingLoading}
                onChange={(event) => onTrackingChange?.({ business_status: event.target.value })}
              >
                {businessStatusOptions
                  .filter((option) => option.value)
                  .map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
              </select>
            </label>
          </section>
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
            <dl className="compact-dl">
              <dt>Statut</dt>
              <dd><span className={`status-pill status-${enrichment.status || "pending"}`}>{enrichmentStatusLabels[enrichment.status] || "En attente"}</span></dd>
              {enrichment.diagnostic_message ? <><dt>Diagnostic</dt><dd>{enrichment.diagnostic_message}</dd></> : null}
              {isUsefulValue(enrichment.parcel_key) ? <><dt>Parcelle</dt><dd>{enrichment.parcel_key}</dd></> : null}
              {isUsefulValue(enrichment.parcel_surface) ? <><dt>Surface parcelle</dt><dd>{enrichment.parcel_surface} m2</dd></> : null}
              {isUsefulValue(enrichment.zonage) ? <><dt>Zonage</dt><dd>{enrichment.zonage}</dd></> : null}
              {isUsefulValue(enrichment.latitude) && isUsefulValue(enrichment.longitude) ? (
                <><dt>Coordonnées</dt><dd>{`${Number(enrichment.latitude).toFixed(5)}, ${Number(enrichment.longitude).toFixed(5)}`}</dd></>
              ) : null}
            </dl>
          </section>
          {annonce.url ? <a className="source-link" href={annonce.url} target="_blank" rel="noreferrer">Ouvrir la source</a> : null}
        </>
      )}
    </aside>
  );
}
