import React, { useState } from "react";
import {
  enrichmentStatusOptions,
  propertyTypeOptions,
  sourceOptions,
} from "../constants";


/**
 * Composant de filtres pour la recherche de biens immobiliers.
 * @param {*} param0 
 * @returns 
 */
export function Filters({ filters, onChange, onSubmit, onReset }) {
  const [expanded, setExpanded] = useState(false);

  function update(name, value) {
    const nextFilters = { ...filters, [name]: value };
    if (name === "sort" && value === "distance") {
      nextFilters.direction = "asc";
    }
    if (name === "query" && !value.trim() && nextFilters.sort === "relevance") {
      nextFilters.sort = "score";
      nextFilters.direction = "desc";
    }
    onChange(nextFilters);
  }

  return (
    <>
      <button
        type="button"
        className="secondary filter-toggle"
        aria-expanded={expanded}
        onClick={() => setExpanded((value) => !value)}
      >
        {expanded ? "Masquer les filtres" : "Afficher les filtres"}
      </button>
      <form className={`filters${expanded ? " filters-expanded" : ""}`} onSubmit={onSubmit}>
        <fieldset>
          <legend>Localisation</legend>
          <input aria-label="Recherche" placeholder="Rechercher" value={filters.query} onChange={(event) => update("query", event.target.value)} />
          <input aria-label="Ville" placeholder="Ville" value={filters.city} onChange={(event) => update("city", event.target.value)} />
          <div className="filter-pair">
            <input aria-label="Code postal" placeholder="Code postal" value={filters.zip_code} onChange={(event) => update("zip_code", event.target.value)} />
            <input aria-label="Département" placeholder="Département" value={filters.department} onChange={(event) => update("department", event.target.value)} />
          </div>
          <div className="filter-pair">
            <input aria-label="Latitude centre" type="number" step="0.000001" placeholder="Latitude centre" value={filters.center_lat} onChange={(event) => update("center_lat", event.target.value)} />
            <input aria-label="Longitude centre" type="number" step="0.000001" placeholder="Longitude centre" value={filters.center_lon} onChange={(event) => update("center_lon", event.target.value)} />
          </div>
          <input aria-label="Rayon en kilomètres" type="number" min="0.1" step="0.1" placeholder="Rayon km" value={filters.radius_km} onChange={(event) => update("radius_km", event.target.value)} />
        </fieldset>

        <fieldset>
          <legend>Bien</legend>
          <select aria-label="Type de bien" value={filters.type_bien} onChange={(event) => update("type_bien", event.target.value)}>
            {propertyTypeOptions.map((option) => (
              <option key={option.value || "all"} value={option.value}>{option.label}</option>
            ))}
          </select>
          <select aria-label="Source" value={filters.source_site} onChange={(event) => update("source_site", event.target.value)}>
            {sourceOptions.map((option) => (
              <option key={option.value || "all"} value={option.value}>{option.label}</option>
            ))}
          </select>
          <div className="filter-pair">
            <input aria-label="Surface minimale" type="number" min="0" placeholder="Surface min" value={filters.surface_min} onChange={(event) => update("surface_min", event.target.value)} />
            <input aria-label="Surface maximale" type="number" min="0" placeholder="Surface max" value={filters.surface_max} onChange={(event) => update("surface_max", event.target.value)} />
          </div>
          <div className="filter-pair">
            <input aria-label="Nombre de pièces minimum" type="number" min="0" placeholder="Pièces min" value={filters.rooms_min} onChange={(event) => update("rooms_min", event.target.value)} />
            <input aria-label="Nombre de pièces maximum" type="number" min="0" placeholder="Pièces max" value={filters.rooms_max} onChange={(event) => update("rooms_max", event.target.value)} />
          </div>
          <select aria-label="Classe DPE" value={filters.energy_class} onChange={(event) => update("energy_class", event.target.value)}>
            <option value="">Tous les DPE</option>
            {"ABCDEFG".split("").map((value) => <option key={value} value={value}>DPE {value}</option>)}
          </select>
          <select aria-label="Ancienneté" value={filters.recent_days} onChange={(event) => update("recent_days", event.target.value)}>
            <option value="">Toute ancienneté</option>
            {[1, 3, 7, 14, 30].map((days) => <option key={days} value={days}>Détectée depuis {days} jour{days > 1 ? "s" : ""}</option>)}
          </select>
        </fieldset>

        <fieldset>
          <legend>Prix et score</legend>
          <div className="filter-pair">
            <input aria-label="Prix minimum" type="number" min="0" placeholder="Prix min" value={filters.price_min} onChange={(event) => update("price_min", event.target.value)} />
            <input aria-label="Prix maximum" type="number" min="0" placeholder="Prix max" value={filters.price_max} onChange={(event) => update("price_max", event.target.value)} />
          </div>
          <div className="filter-pair">
            <input aria-label="Prix au mètre carré minimum" type="number" min="0" placeholder="Prix/m² min" value={filters.price_m2_min} onChange={(event) => update("price_m2_min", event.target.value)} />
            <input aria-label="Prix au mètre carré maximum" type="number" min="0" placeholder="Prix/m² max" value={filters.price_m2_max} onChange={(event) => update("price_m2_max", event.target.value)} />
          </div>
          <div className="filter-pair">
            <input aria-label="Score minimum" type="number" min="0" max="100" placeholder="Score min" value={filters.score_min} onChange={(event) => update("score_min", event.target.value)} />
            <input aria-label="Score maximum" type="number" min="0" max="100" placeholder="Score max" value={filters.score_max} onChange={(event) => update("score_max", event.target.value)} />
          </div>
        </fieldset>

        <fieldset>
          <legend>Enrichissement</legend>
          <input aria-label="Zonage" placeholder="Zonage" value={filters.zonage} onChange={(event) => update("zonage", event.target.value)} />
          <select aria-label="Statut d’enrichissement" value={filters.enrichment_status} onChange={(event) => update("enrichment_status", event.target.value)}>
            {enrichmentStatusOptions.map((option) => (
              <option key={option.value || "all"} value={option.value}>{option.label}</option>
            ))}
          </select>
          <select aria-label="Présence d’une parcelle" value={filters.has_parcel} onChange={(event) => update("has_parcel", event.target.value)}>
            <option value="">Avec ou sans parcelle</option>
            <option value="true">Avec parcelle</option>
            <option value="false">Sans parcelle</option>
          </select>
          <div className="filter-pair">
            <input aria-label="Surface cadastrale minimale" type="number" min="0" placeholder="Parcelle min" value={filters.parcel_surface_min} onChange={(event) => update("parcel_surface_min", event.target.value)} />
            <input aria-label="Surface cadastrale maximale" type="number" min="0" placeholder="Parcelle max" value={filters.parcel_surface_max} onChange={(event) => update("parcel_surface_max", event.target.value)} />
          </div>
        </fieldset>

        <fieldset>
          <legend>Tri</legend>
          <select aria-label="Critère de tri" value={filters.sort} onChange={(event) => update("sort", event.target.value)}>
            <option value="score">Score</option>
            {filters.query.trim() ? <option value="relevance">Pertinence</option> : null}
            <option value="price">Prix</option>
            <option value="surface">Surface</option>
            <option value="price_m2">Prix/m²</option>
            <option value="last_seen">Dernière vue</option>
            <option value="zonage">Zonage</option>
            <option value="distance">Distance</option>
          </select>
          <select aria-label="Direction du tri" value={filters.direction} onChange={(event) => update("direction", event.target.value)}>
            <option value="desc">Décroissant</option>
            <option value="asc">Croissant</option>
          </select>
        </fieldset>

        <div className="filter-actions">
          <button type="submit">Filtrer</button>
          <button type="button" className="secondary" onClick={onReset}>Réinitialiser</button>
        </div>
      </form>
    </>
  );
}
