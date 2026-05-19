/**
 * Effectue une requête API.
 * @param {*} path Le chemin de l'endpoint API à appeler.
 * @param {*} options Les options de la requête (méthode, corps, etc.).
 * @returns La réponse de l'API au format JSON.
 */
function readCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

async function request(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const csrfToken = method === "GET" || method === "HEAD" ? null : readCookie("csrf_token");
  const response = await fetch(path, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(csrfToken ? { "X-CSRF-Token": decodeURIComponent(csrfToken) } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Erreur API");
  }

  return response.json();
}

/**
 * Renvoie les informations de l'utilisateur actuellement connecté.
 * @returns Un objet contenant les informations de l'utilisateur connecté.
 */
export function getMe() {
  return request("/api/auth/me");
}

/**
 * Connecte un utilisateur.
 * @param {*} email l'email de l'utilisateur
 * @param {*} password le mot de passe de l'utilisateur
 * @returns Un objet contenant les informations de l'utilisateur connecté.
 */
export function login(email, password) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

/**
 * Déconnecte l'utilisateur actuellement connecté.
 * @returns Retourne une promesse qui se résout lorsque l'utilisateur est déconnecté avec succès.
 */
export function logout() {
  return request("/api/auth/logout", { method: "POST" });
}

export function requestPasswordReset(email) {
  return request("/api/auth/password-reset/request", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function confirmPasswordReset(token, newPassword) {
  return request("/api/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export function inviteMember(email) {
  return request("/api/auth/members", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function listMembers() {
  return request("/api/auth/members");
}

/**
 * Recherche les annonces selon les paramètres fournis.
 * @param {*} params Les critères de recherche.
 * @returns Une liste d'annonces correspondant aux critères.
 */
export function searchAnnonces(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  return request(`/api/annonces?${query.toString()}`);
}

/**
 * Renvoie une annonce selon son identifiant.
 * @param {*} id 
 * @returns Renvoie une annonce selon son identifiant
 */
export function getAnnonce(id) {
  return request(`/api/annonces/${id}`);
}
