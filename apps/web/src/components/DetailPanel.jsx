import React from "react";
import { formatDistance, formatMoney } from "../utils";


/**
 * Composant de panneau de détails pour afficher les informations d'une annonce.
 * @param {*} annonce, loading, onClose 
 * @returns 
 */
export function DetailPanel({ annonce, loading, onClose }) {
  if (!annonce && !loading) return null;
  const enrichment = annonce?.enrichment || {};

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
            <dt>Prix/m2</dt><dd>{annonce.price_m2 ? `${Math.round(annonce.price_m2)} EUR` : "-"}</dd>
            <dt>Localisation</dt><dd>{[annonce.city, annonce.zip_code, annonce.department].filter(Boolean).join(" - ") || "-"}</dd>
            <dt>Type</dt><dd>{annonce.type_bien || "-"}</dd>
            <dt>DPE</dt><dd>{annonce.energy_class || "-"}</dd>
            <dt>Agence</dt><dd>{annonce.agency || "-"}</dd>
            <dt>Derniere vue</dt><dd>{annonce.last_seen || "-"}</dd>
            {annonce.distance_m !== undefined ? <><dt>Distance</dt><dd>{formatDistance(annonce.distance_m)}</dd></> : null}
          </dl>
          <section className="detail-section">
            <p className="eyebrow">Enrichissement foncier</p>
            <dl>
              <dt>Statut</dt>
              <dd><span className={`status-pill status-${enrichment.status || "pending"}`}>{enrichment.status || "pending"}</span></dd>
              <dt>Diagnostic</dt><dd>{enrichment.diagnostic_message || "-"}</dd>
              <dt>Geocodage</dt>
              <dd>{[enrichment.geocode_status, enrichment.geocode_score ? `score ${Number(enrichment.geocode_score).toFixed(2)}` : null, enrichment.geocode_type].filter(Boolean).join(" - ") || "-"}</dd>
              <dt>Requete</dt><dd>{enrichment.geocode_query || "-"}</dd>
              <dt>Cadastre</dt><dd>{enrichment.cadastre_status || "-"}</dd>
              <dt>Urbanisme</dt><dd>{enrichment.gpu_status || "-"}</dd>
              <dt>Coordonnees</dt>
              <dd>{enrichment.latitude && enrichment.longitude ? `${enrichment.latitude}, ${enrichment.longitude}` : "-"}</dd>
              <dt>Parcelle</dt><dd>{enrichment.parcel_key || "-"}</dd>
              <dt>Surface parcelle</dt><dd>{enrichment.parcel_surface ? `${enrichment.parcel_surface} m2` : "-"}</dd>
              <dt>Commune cadastre</dt><dd>{enrichment.parcel_commune_code || "-"}</dd>
              <dt>Zonage PLU</dt><dd>{enrichment.zonage || "-"}</dd>
              <dt>Prescriptions</dt><dd>{enrichment.prescriptions?.length || 0}</dd>
              <dt>Servitudes</dt><dd>{enrichment.servitudes?.length || 0}</dd>
              <dt>Documents</dt><dd>{enrichment.documents?.length || 0}</dd>
              <dt>Erreur</dt><dd>{enrichment.error || "-"}</dd>
              <dt>Mis a jour</dt><dd>{enrichment.enriched_at || "-"}</dd>
            </dl>
          </section>
          {annonce.url ? <a className="source-link" href={annonce.url} target="_blank" rel="noreferrer">Ouvrir la source</a> : null}
        </>
      )}
    </aside>
  );
}
