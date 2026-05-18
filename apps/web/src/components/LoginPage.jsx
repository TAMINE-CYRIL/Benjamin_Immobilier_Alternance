import React, { useState } from "react";
import { login } from "../api";


/**
 * Fonction qui retourne un composant SVG représentant une icône de mail.
 * @returns Un SVG qui représente l'icone de mail
 */
function MailIcon() {
  return (
    <svg viewBox="0 0 24 24" role="presentation">
      <path d="M4 7.75A2.75 2.75 0 0 1 6.75 5h10.5A2.75 2.75 0 0 1 20 7.75v8.5A2.75 2.75 0 0 1 17.25 19H6.75A2.75 2.75 0 0 1 4 16.25z" />
      <path d="m5.5 7 6.5 5 6.5-5" />
    </svg>
  );
}

/**
 * Fonction qui retourne un composant SVG représentant une icône de verrou.
 * @returns Un SVG qui représente l'icone de verrou
 */
function LockIcon() {
  return (
    <svg viewBox="0 0 24 24" role="presentation">
      <path d="M8 10V7.5a4 4 0 1 1 8 0V10" />
      <rect x="5" y="10" width="14" height="10" rx="2" />
    </svg>
  );
}

/**
 * Fonction qui retourne un composant représentant un champ de saisie.
 * @param {string} label - Le libellé du champ.
 * @param {string} type - Le type du champ (par défaut "text").
 * @param {string} autoComplete - L'attribut autocomplete pour le champ.
 * @param {string} value - La valeur du champ.
 * @param {function} onChange - La fonction de gestion du changement de valeur.
 * @param {React.ReactNode} icon - L'icône à afficher dans le champ.
 * @returns Un composant React pour le champ de saisie.
 */
function LoginField({ label, type = "text", autoComplete, value, onChange, icon }) {
  return (
    <label className="field">
      <span>{label}</span>
      <div className="input-wrap">
        <span className="input-icon" aria-hidden="true">{icon}</span>
        <input value={value} onChange={onChange} autoComplete={autoComplete} type={type} />
      </div>
    </label>
  );
}


/**
 * Composant de page de connexion.
 * @param {*} param0 
 * @returns 
 */
export function LoginPage({ onLogin }) {
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
      <section className="login-hero" aria-hidden="true">
        <div className="login-hero-grid" />
        <div className="login-brand">
          <p className="login-brand-kicker">Benjamin</p>
          <h1>Immobilier</h1>
          <span>Pole developpement</span>
        </div>
      </section>

      <section className="login-side">
        <form className="login-panel" onSubmit={handleSubmit}>
          <div className="login-copy">
            <h2>Bonjour</h2>
            <p className="login-intro">Connectez-vous pour acceder a votre espace.</p>
          </div>

          <LoginField
            label="Adresse e-mail"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            icon={<MailIcon />}
          />

          <LoginField
            label="Mot de passe"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            icon={<LockIcon />}
          />

          {error ? <p className="error">{error}</p> : null}

          <button className="login-submit" type="submit" disabled={loading}>
            {loading ? "Connexion..." : "Se connecter"}
            <span aria-hidden="true">→</span>
          </button>

          <p className="login-footnote">© 2026 Benjamin Immobilier</p>
        </form>
      </section>
    </main>
  );
}
