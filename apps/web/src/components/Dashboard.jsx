import React, { useEffect, useMemo, useState } from "react";
import { getAnnonce, logout, searchAnnonces } from "../api";
import { emptyFilters } from "../constants";
import { AnnoncesTable } from "./AnnoncesTable";
import { DetailPanel } from "./DetailPanel";
import { Filters } from "./Filters";
import AnnoncesMap from "./AnnoncesMap";

export function Dashboard({ user, onLogout }) {
  const [filters, setFilters] = useState(emptyFilters);
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 25 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const totalPages = useMemo(() => Math.max(Math.ceil(data.total / data.page_size), 1), [data]);

  console.log("Dashboard render", { filters, page, data, loading, error, selected });
  async function load(nextPage = page, nextFilters = filters) {
    setLoading(true);
    setError("");
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

  async function handleSelect(id) {
    setDetailLoading(true);
    setSelected({});
    try {
      setSelected(await getAnnonce(id));
    } catch (err) {
      setError(err.message);
      setSelected(null);
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleLogout() {
    await logout();
    onLogout();
  }

  function submitFilters(event) {
    event.preventDefault();
    setPage(1);
    load(1, filters);
  }

  function resetFilters() {
    setFilters(emptyFilters);
    setPage(1);
    load(1, emptyFilters);
  }

  function goToPage(nextPage) {
    setPage(nextPage);
    load(nextPage, filters);
  }

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>Opportunites immobilieres</h1>
        </div>
        <div className="user-box">
          <span>{user.email}</span>
          <button className="secondary" onClick={handleLogout}>Deconnexion</button>
        </div>
      </header>

      <Filters filters={filters} onChange={setFilters} onSubmit={submitFilters} onReset={resetFilters} />

      <section className="results-head">
        <strong>{data.total} annonce(s)</strong>
        {loading ? <span>Chargement...</span> : null}
        {error ? <span className="error">{error}</span> : null}
      </section>

      {data.items.length ? (
        <AnnoncesTable annonces={data.items} onSelect={handleSelect} />
      ) : (
        <div className="empty">Aucune annonce ne correspond aux filtres.</div>
      )}

      <AnnoncesMap annonces={data.items} />
      

      <nav className="pagination">
        <button className="secondary" disabled={page <= 1} onClick={() => goToPage(page - 1)}>Precedent</button>
        <span>Page {page} / {totalPages}</span>
        <button className="secondary" disabled={page >= totalPages} onClick={() => goToPage(page + 1)}>Suivant</button>
      </nav>

      <DetailPanel annonce={selected} loading={detailLoading} onClose={() => setSelected(null)} />
    </main>
  );
}
