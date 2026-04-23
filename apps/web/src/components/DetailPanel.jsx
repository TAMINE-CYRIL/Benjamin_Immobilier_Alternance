import React from "react";
import { formatMoney } from "../utils";

export function DetailPanel({ annonce, loading, onClose }) {
  if (!annonce && !loading) return null;

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
          </dl>
          {annonce.url ? <a className="source-link" href={annonce.url} target="_blank" rel="noreferrer">Ouvrir la source</a> : null}
        </>
      )}
    </aside>
  );
}
