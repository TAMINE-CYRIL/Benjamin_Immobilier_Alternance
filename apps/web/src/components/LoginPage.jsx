import React, { useMemo, useState } from "react";
import { confirmPasswordReset, login, requestPasswordReset } from "../api";


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
  const initialResetToken = useMemo(() => new URLSearchParams(window.location.search).get("reset_token") || "", []);
  const [mode, setMode] = useState(initialResetToken ? "reset" : "login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [resetToken, setResetToken] = useState(initialResetToken);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
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

  async function handleRequestReset(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);

    try {
      await requestPasswordReset(email);
      setMessage("Si un compte existe pour cette adresse, un lien de réinitialisation vient d'être envoyé.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirmReset(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (newPassword !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }

    setLoading(true);
    try {
      await confirmPasswordReset(resetToken, newPassword);
      window.history.replaceState({}, "", window.location.pathname);
      setPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setResetToken("");
      setMode("login");
      setMessage("Votre mot de passe a été mis à jour. Vous pouvez vous connecter.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
    setMessage("");
  }

  const title = mode === "login" ? "Bonjour" : mode === "forgot" ? "Mot de passe oublie" : "Nouveau mot de passe";
  const intro = mode === "login"
    ? "Connectez-vous pour accéder a votre espace."
    : mode === "forgot"
      ? "Renseignez votre adresse e-mail pour recevoir un lien sécurisé."
      : "Choisissez un nouveau mot de passe pour votre compte.";

  return (
    <main className="login-shell">
      <section className="login-hero" aria-hidden="true">
        <div className="login-hero-grid" />
        <div className="login-brand">
          <h1>
            Benjamin
            <span>Immobilier</span>
          </h1>
          <p>Pôle développement</p>
        </div>
      </section>

      <section className="login-side">
        <form
          className="login-panel"
          onSubmit={mode === "login" ? handleSubmit : mode === "forgot" ? handleRequestReset : handleConfirmReset}
        >
          <div className="login-copy">
            <h2>{title}</h2>
            <p className="login-intro">{intro}</p>
          </div>

          {mode !== "reset" ? (
            <LoginField
              label="Adresse e-mail"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              icon={<MailIcon />}
            />
          ) : null}

          {mode === "login" ? (
            <>
              <LoginField
                label="Mot de passe"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                icon={<LockIcon />}
              />
              <button className="text-button" type="button" onClick={() => switchMode("forgot")}>
                Mot de passe oublie ?
              </button>
            </>
          ) : null}

          {mode === "reset" ? (
            <>
              <LoginField
                label="Nouveau mot de passe"
                type="password"
                autoComplete="new-password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                icon={<LockIcon />}
              />
              <LoginField
                label="Confirmer le mot de passe"
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                icon={<LockIcon />}
              />
            </>
          ) : null}

          {error ? <p className="error">{error}</p> : null}
          {message ? <p className="success-message">{message}</p> : null}

          <button className="login-submit" type="submit" disabled={loading}>
            {loading ? "Traitement..." : mode === "login" ? "Se connecter" : mode === "forgot" ? "Envoyer le lien" : "Mettre à jour"}
            <span aria-hidden="true">→</span>
          </button>

          {mode !== "login" ? (
            <button className="text-button centered" type="button" onClick={() => switchMode("login")}>
              Retour à la connexion
            </button>
          ) : null}

          <p className="login-footnote">© 2026 Benjamin Immobilier</p>
        </form>
      </section>
    </main>
  );
}
