import React, { useEffect, useMemo, useState } from "react";
import { getAnnonce, searchAnnonces } from "../api";
import { emptyFilters } from "../constants";
import { AnnoncesList } from "./AnnoncesList";
import AnnoncesMap from "./AnnoncesMap";
import { DetailPanel } from "./DetailPanel";
import { Filters } from "./Filters";

export function AnnoncesPage() {
  const [filters, setFilters] = useState(emptyFilters);
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 25 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const totalPages = useMemo(() => Math.max(Math.ceil(data.total / data.page_size), 1), [data]);

  /**
   * Charge les annonces selon la page et les filtres spécifiés.
   * @param {*} nextPage
   * @param {*} nextFilters
   */
  async function load(nextPage = page, nextFilters = filters) {
    setLoading(true);
    setError("");
    setSelectedId(null);
    setSelected(null);
    try {
      const result = await searchAnnonces({ ...nextFilters, page: nextPage, page_size: 25 });
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(1, filters);
  }, []);

  /**
   * Gère la sélection d'une annonce et charge ses détails.
   * @param {*} id
   */
  async function handleSelect(id) {
    const listAnnonce = data.items.find((annonce) => annonce.id === id);
    setSelectedId(id);
    setDetailLoading(true);
    setSelected(listAnnonce || {});
    try {
      const detail = await getAnnonce(id);
      setSelected({
        ...detail,
        ...(listAnnonce?.distance_m !== undefined ? { distance_m: listAnnonce.distance_m } : {}),
      });
    } catch (err) {
      setError(err.message);
      setSelected(null);
    } finally {
      setDetailLoading(false);
    }
  }

  /**
   * Initialise la recherche avec les filtres actuels lors de la soumission du formulaire de filtres.
   * @param {*} event
   */
  function submitFilters(event) {
    event.preventDefault();
    setPage(1);
    load(1, filters);
  }

  /**
   * Réinitialise les filtres à leur état initial et recharge les annonces.
   */
  function resetFilters() {
    setFilters(emptyFilters);
    setPage(1);
    load(1, emptyFilters);
  }

  /**
   * Fonction pour se rendre à la page spécifiée avec les filtres actuels.
   * @param {*} nextPage
   */
  function goToPage(nextPage) {
    setPage(nextPage);
    load(nextPage, filters);
  }

  return (
    <>
      <section className="results-head">
        <strong>{data.total} annonce(s)</strong>
        {loading ? <span>Chargement...</span> : null}
        {error ? <span className="error">{error}</span> : null}
      </section>

      <section className="search-workspace">
        <aside className="search-sidebar">
          <p className="eyebrow">Recherche</p>
          <h2>Filtres</h2>
          <Filters filters={filters} onChange={setFilters} onSubmit={submitFilters} onReset={resetFilters} />
        </aside>

        <section className="search-results">
          <AnnoncesMap annonces={data.items} selectedId={selectedId} onSelect={handleSelect} />
          <div className="list-panel">
            <div className="list-head">
              <div>
                <p className="eyebrow">Résultats</p>
                <h2>Annonces</h2>
              </div>
              <span>{data.items.length} sur cette page</span>
            </div>
            <AnnoncesList annonces={data.items} selectedId={selectedId} onSelect={handleSelect} />
          </div>
        </section>
      </section>

      <nav className="pagination">
        <button className="secondary" disabled={page <= 1} onClick={() => goToPage(page - 1)}>Précédent</button>
        <span>Page {page} / {totalPages}</span>
        <button className="secondary" disabled={page >= totalPages} onClick={() => goToPage(page + 1)}>Suivant</button>
      </nav>

      <DetailPanel
        annonce={selected}
        loading={detailLoading}
        onClose={() => {
          setSelected(null);
          setSelectedId(null);
        }}
      />
    </>
  );
}
