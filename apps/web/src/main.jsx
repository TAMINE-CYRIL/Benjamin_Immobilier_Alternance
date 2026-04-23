import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { getMe } from "./api";
import { Dashboard } from "./components/Dashboard";
import { LoginPage } from "./components/LoginPage";
import "./styles.css";

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
