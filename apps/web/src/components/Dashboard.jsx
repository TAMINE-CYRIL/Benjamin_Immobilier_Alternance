import React, { useState } from "react";
import { logout } from "../api";
import { AnnoncesPage } from "./AnnoncesPage";
import { MembersPage } from "./MembersPage";

/**
 * Coquille du dashboard : navigation principale et session utilisateur.
 * @param {*} user, onLogout
 * @returns
 */
export function Dashboard({ user, onLogout }) {
  const [activeView, setActiveView] = useState("annonces");

  /**
   * Gère la déconnexion de l'utilisateur.
   */
  async function handleLogout() {
    await logout();
    onLogout();
  }

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>{activeView === "annonces" ? "Opportunites immobilieres" : "Gestion des membres"}</h1>
        </div>
        <div className="user-box">
          <span>{user.email}</span>
          <button className="secondary" onClick={handleLogout}>Deconnexion</button>
        </div>
      </header>

      <nav className="dashboard-tabs" aria-label="Navigation dashboard">
        <button
          type="button"
          className={activeView === "annonces" ? "active" : ""}
          aria-current={activeView === "annonces" ? "page" : undefined}
          onClick={() => setActiveView("annonces")}
        >
          Annonces
        </button>
        <button
          type="button"
          className={activeView === "membres" ? "active" : ""}
          aria-current={activeView === "membres" ? "page" : undefined}
          onClick={() => setActiveView("membres")}
        >
          Membres
        </button>
      </nav>

      {activeView === "annonces" ? <AnnoncesPage /> : <MembersPage />}
    </main>
  );
}
