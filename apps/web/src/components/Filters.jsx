import React from "react";
import { propertyTypeOptions, sourceOptions } from "../constants";

export function Filters({ filters, onChange, onSubmit, onReset }) {
  function update(name, value) {
    onChange({ ...filters, [name]: value });
  }

  return (
    <form className="filters" onSubmit={onSubmit}>
      <input placeholder="Rechercher" value={filters.query} onChange={(event) => update("query", event.target.value)} />
      <input placeholder="Ville" value={filters.city} onChange={(event) => update("city", event.target.value)} />
      <input placeholder="Code postal" value={filters.zip_code} onChange={(event) => update("zip_code", event.target.value)} />
      <input placeholder="Departement" value={filters.department} onChange={(event) => update("department", event.target.value)} />
      <select value={filters.type_bien} onChange={(event) => update("type_bien", event.target.value)}>
        {propertyTypeOptions.map((option) => (
          <option key={option.value || "all"} value={option.value}>{option.label}</option>
        ))}
      </select>
      <select value={filters.source_site} onChange={(event) => update("source_site", event.target.value)}>
        {sourceOptions.map((option) => (
          <option key={option.value || "all"} value={option.value}>{option.label}</option>
        ))}
      </select>
      <input placeholder="Zonage" value={filters.zonage} onChange={(event) => update("zonage", event.target.value)} />
      <input type="number" placeholder="Prix min" value={filters.price_min} onChange={(event) => update("price_min", event.target.value)} />
      <input type="number" placeholder="Prix max" value={filters.price_max} onChange={(event) => update("price_max", event.target.value)} />
      <input type="number" placeholder="Surface min" value={filters.surface_min} onChange={(event) => update("surface_min", event.target.value)} />
      <input type="number" placeholder="Surface max" value={filters.surface_max} onChange={(event) => update("surface_max", event.target.value)} />
      <input type="number" placeholder="Score min" value={filters.score_min} onChange={(event) => update("score_min", event.target.value)} />
      <select value={filters.enrichment_status} onChange={(event) => update("enrichment_status", event.target.value)}>
        <option value="">Tous enrichissements</option>
        <option value="success">Enrichi</option>
        <option value="partial">Partiel</option>
        <option value="not_found">Introuvable</option>
        <option value="failed">Erreur</option>
        <option value="pending">En attente</option>
      </select>
      <select value={filters.sort} onChange={(event) => update("sort", event.target.value)}>
        <option value="score">Score</option>
        <option value="price">Prix</option>
        <option value="surface">Surface</option>
        <option value="price_m2">Prix/m2</option>
        <option value="last_seen">Derniere vue</option>
        <option value="zonage">Zonage</option>
      </select>
      <select value={filters.direction} onChange={(event) => update("direction", event.target.value)}>
        <option value="desc">Decroissant</option>
        <option value="asc">Croissant</option>
      </select>
      <button type="submit">Filtrer</button>
      <button type="button" className="secondary" onClick={onReset}>Reinitialiser</button>
    </form>
  );
}
