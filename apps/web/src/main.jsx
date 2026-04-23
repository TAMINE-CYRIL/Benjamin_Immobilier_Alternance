import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { getAnnonce, getMe, login, logout, searchAnnonces } from "./api";
import "./styles.css";

const emptyFilters = {
  city: "",
  zip_code: "",
  department: "",
  price_min: "",
  price_max: "",
  surface_min: "",
  surface_max: "",
  type_bien: "",
  score_min: "",
  source_site: "",
  sort: "score",
  direction: "desc",
};

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await login(email, password);
      onLogin(result.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-shell">
      <form className="login-panel" onSubmit={handleSubmit}>
        <div>
          <p className="eyebrow">Acces prive</p>
          <h1>Benjamin Immobilier</h1>
        </div>

        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" />
        </label>

        <label>
          Mot de passe
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            autoComplete="current-password"
          />
        </label>

        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={loading}>{loading ? "Connexion..." : "Se connecter"}</button>
      </form>
    </main>
  );
}

function Filters({ filters, onChange, onSubmit, onReset }) {
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

function formatMoney(value) {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

function AnnoncesTable({ annonces, onSelect }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Score</th>
            <th>Annonce</th>
            <th>Ville</th>
            <th>Prix</th>
            <th>Surface</th>
            <th>Prix/m2</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {annonces.map((annonce) => (
            <tr key={annonce.id} onClick={() => onSelect(annonce.id)}>
              <td><strong>{annonce.score ?? "-"}</strong></td>
              <td>{annonce.title || "Sans titre"}</td>
              <td>{[annonce.city, annonce.zip_code].filter(Boolean).join(" ") || "-"}</td>
              <td>{formatMoney(annonce.price)}</td>
              <td>{annonce.surface ? `${annonce.surface} m2` : "-"}</td>
              <td>{annonce.price_m2 ? `${Math.round(annonce.price_m2)} EUR` : "-"}</td>
              <td>{annonce.source_site || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DetailPanel({ annonce, loading, onClose }) {
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

function Dashboard({ user, onLogout }) {
  const [filters, setFilters] = useState(emptyFilters);
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 25 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const totalPages = useMemo(() => Math.max(Math.ceil(data.total / data.page_size), 1), [data]);

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
          <p className="eyebrow">Dashboard prive</p>
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

      <nav className="pagination">
        <button className="secondary" disabled={page <= 1} onClick={() => goToPage(page - 1)}>Precedent</button>
        <span>Page {page} / {totalPages}</span>
        <button className="secondary" disabled={page >= totalPages} onClick={() => goToPage(page + 1)}>Suivant</button>
      </nav>

      <DetailPanel annonce={selected} loading={detailLoading} onClose={() => setSelected(null)} />
    </main>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    getMe()
      .then((result) => setUser(result.user))
      .catch(() => setUser(null))
      .finally(() => setChecking(false));
  }, []);

  if (checking) return <main className="loading-page">Chargement...</main>;
  if (!user) return <LoginPage onLogin={setUser} />;
  return <Dashboard user={user} onLogout={() => setUser(null)} />;
}

createRoot(document.getElementById("root")).render(<App />);
