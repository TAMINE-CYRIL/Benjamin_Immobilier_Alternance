import React from "react";

export function Filters({ filters, onChange, onSubmit, onReset }) {
  function update(name, value) {
    onChange({ ...filters, [name]: value });
  }

  return (
    <form className="filters" onSubmit={onSubmit}>
      <input placeholder="Ville" value={filters.city} onChange={(event) => update("city", event.target.value)} />
      <input placeholder="Code postal" value={filters.zip_code} onChange={(event) => update("zip_code", event.target.value)} />
      <input placeholder="Departement" value={filters.department} onChange={(event) => update("department", event.target.value)} />
      <input placeholder="Type de bien" value={filters.type_bien} onChange={(event) => update("type_bien", event.target.value)} />
      <input placeholder="Source" value={filters.source_site} onChange={(event) => update("source_site", event.target.value)} />
      <input type="number" placeholder="Prix min" value={filters.price_min} onChange={(event) => update("price_min", event.target.value)} />
      <input type="number" placeholder="Prix max" value={filters.price_max} onChange={(event) => update("price_max", event.target.value)} />
      <input type="number" placeholder="Surface min" value={filters.surface_min} onChange={(event) => update("surface_min", event.target.value)} />
      <input type="number" placeholder="Surface max" value={filters.surface_max} onChange={(event) => update("surface_max", event.target.value)} />
      <input type="number" placeholder="Score min" value={filters.score_min} onChange={(event) => update("score_min", event.target.value)} />
      <select value={filters.sort} onChange={(event) => update("sort", event.target.value)}>
        <option value="score">Score</option>
        <option value="price">Prix</option>
        <option value="surface">Surface</option>
        <option value="price_m2">Prix/m2</option>
        <option value="last_seen">Derniere vue</option>
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
