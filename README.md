# Projet de scraping immobilier — Crawl4AI + PostgreSQL

<div>
<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" />
<img src="https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white" />
<img src="https://img.shields.io/badge/fastapi-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
</div>

Projet de scraping, nettoyage et scoring d'annonces immobilières (sources : Bienici, SeLoger, PAP, Leboncoin, LogicImmo, Espaces Atypiques, AvoVentes).
On utilise [Crawl4AI](https://github.com/unclecode/crawl4ai) pour parcourir les différents sites et extraire les données, enrichies avec les données DVF (Demandes de Valeurs Foncières) pour calculer un score d'opportunité par annonce.

## Fonctionnalités

- Scrapers multi-sources dans `scrapers/immobilier/` (7 sources supportées)
- Scraping des avis de décès Libramemoria dans `scrapers/scrape_libramemoria.py`
- Normalisation et nettoyage des champs (prix, surface, code postal) dans `utils/cleaning.py`
- Rotation de proxies et randomisation des User-Agents dans `utils/config.py`
- Import et agrégation des données DVF (prix médian au m² par code postal, type de bien, année)
- Système de scoring des annonces basé sur l'écart au prix marché DVF (`services/deals.py`)
- Enrichissement cadastre et urbanisme (API Adresse, API Carto Cadastre, GPU) dans `services/enrichment/`
- API REST FastAPI exposant les annonces scorées (`apps/api/`)
- Tests unitaires avec pytest dans `tests/`

## Prérequis

- Python 3.9+
- PostgreSQL avec PostGIS installe sur le serveur qui execute la base
- Git (optionnel)

PostGIS est necessaire pour les enrichissements geographiques (`geometry`,
`geography`, `ST_DWithin`, index GiST). Sur Windows, installez PostGIS via Stack
Builder pour la meme version majeure de PostgreSQL que votre serveur. Sur
Debian/Ubuntu, installez par exemple `postgresql-XX-postgis-3` et
`postgresql-XX-postgis-3-scripts` en remplacant `XX` par la version PostgreSQL.

## Structure du dépôt

```
.
├── apps/
│   ├── api/
│   │   ├── main.py              # Point d'entrée FastAPI
│   │   └── routes/annonces.py   # Route GET /api/annonces
│   └── database/
│       └── annonces_repo.py     # Requête de fetch des annonces scorées
├── database/
│   ├── connection.py            # Connexion PostgreSQL via .env
│   ├── create_tables.py         # Création des tables (annonces, dvf_raw, dvf_stats, …)
│   ├── db.py                    # Insertion / mise à jour des annonces
│   ├── import_dvf.py            # Import d'un fichier DVF dans dvf_raw (staging)
│   ├── import_all_dvf.py        # Orchestration : import + agrégation de tous les fichiers DVF
│   ├── aggregate_dvf.py         # Agrégation DVF par année et multi-années
│   ├── score_annonce.py         # Calcul et écriture du score sur chaque annonce
│   ├── stats_nb_transactions.py # Calcul des quartiles de nb_transactions
│   ├── reset_db.py              # Suppression des annonces de plus de 14 jours
│   └── reset_tables.py          # Suppression de toutes les tables
├── models/
│   └── annonces.py              # Modèle Pydantic Annonce
├── scrapers/
│   ├── immobilier/
│   │   ├── scrape_atypiques.py
│   │   ├── scrape_avoventes.py
│   │   ├── scrape_bienici.py
│   │   ├── scrape_leboncoin.py
│   │   ├── scrape_logicimmo.py
│   │   ├── scrape_pap.py
│   │   └── scrape_seloger.py
│   └── scrape_libramemoria.py
├── schema/                      # Schémas JSON CSS pour chaque source (Crawl4AI)
├── services/
│   └── deals.py                 # Algorithme de scoring (écart au médian DVF + bonus quartile)
├── tests/
│   ├── test_cleaning.py
│   └── test_db.py
├── utils/
│   ├── cleaning.py              # extract_number, normalization, filter_annonces
│   └── config.py                # BrowserConfig, proxies Webshare, user-agents
├── main_immo.py                 # Script principal : scraping + insertion + scoring
├── main_libra.py                # Script scraping Libramemoria → JSON + CSV
└── requirements.txt
```

## Installation

```bash
pip install -r requirements.txt
crawl4ai-setup   # Installe les navigateurs Playwright
```

Créer un fichier `.env` à la racine :

```env
APP_ENV=development
PG_DB=nom_de_la_base
PG_USER=utilisateur
PG_PASSWORD=mot_de_passe
PG_HOST=localhost
PG_PORT=5432

# Optionnel : proxies Webshare pour les sites anti-bot
PROXIES=http://user:pass@host:port,...

# Dashboard prive
JWT_SECRET=une-cle-longue-et-aleatoire-de-32-caracteres-minimum
AUTH_COOKIE_SECURE=false
CSRF_COOKIE_NAME=csrf_token
ALLOWED_HOSTS=127.0.0.1,localhost
API_CORS_ORIGINS=http://127.0.0.1:5173
FRONTEND_BASE_URL=http://127.0.0.1:5173
PASSWORD_RESET_BASE_URL=http://127.0.0.1:5173
PASSWORD_RESET_TTL_MINUTES=60

# Envoi des emails de réinitialisation
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=notification@example.com
SMTP_PASSWORD=mot_de_passe_smtp
SMTP_FROM=notification@example.com
SMTP_USE_TLS=true
```

Copier `.env.example` pour obtenir la liste complète des variables. En production, `APP_ENV=production`, `AUTH_COOKIE_SECURE=true`, `FORCE_HTTPS=true`, `ALLOWED_HOSTS` et `API_CORS_ORIGINS` doivent être renseignés explicitement. L'API refuse de démarrer avec le secret JWT par défaut en production.

## Utilisation

### 1. Créer les tables PostgreSQL

```bash
python database/create_tables.py
```

Si PostgreSQL repond que l'extension `postgis` n'est pas disponible, installez
PostGIS cote serveur, puis activez-la dans la base :

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

### 2. Importer les données DVF

Placer les fichiers `ValeursFoncieres-AAAA.txt` dans `data/dvf/`, puis :

```bash
python database/import_all_dvf.py
```

Cette commande importe, agrège par année et calcule les statistiques multi-années (prix médian, Q1, Q3 par code postal et type de bien) ainsi que les quartiles de transactions.

### 3. Lancer le scraping immobilier

```bash
python main_immo.py
```

Cela scrape les sources configurées dans `main_immo.py`, insère les annonces en base et calcule leur score d'opportunité.

### 4. Lancer le scraping Libramemoria

```bash
python main_libra.py
```

Génère `data/avis_deces.json` et `data/avis_deces.csv`.

### 5. Enrichir les annonces avec cadastre et urbanisme

```bash
python -m services.enrichment.run --limit 100
```

Cette commande traite les annonces non enrichies ou anciennes, géocode la localisation via le service de géocodage Géoplateforme, rattache l'annonce à une parcelle cadastrale via l'API Carto Cadastre, puis interroge le Géoportail de l'Urbanisme pour récupérer le zonage, les prescriptions et les servitudes. Pappers n'est pas utilisé dans cette V1.

Chaque enrichissement stocke aussi un diagnostic par étape (`geocode_status`, `cadastre_status`, `gpu_status`, score de géocodage, type de résultat, message métier) pour expliquer les résultats partiels.

Variables optionnelles si les endpoints publics changent :

```env
ADDRESS_API_URL=https://data.geopf.fr/geocodage/search
CADASTRE_API_URL=https://apicarto.ign.fr/api/cadastre/parcelle
GPU_API_BASE_URL=https://apicarto.ign.fr/api/gpu
MIN_GEOCODE_SCORE=0.45
```

Les résultats sont stockés dans les tables `parcelles` et `annonce_enrichments`.

### 6. Automatisation V2 sous Windows

L'orchestrateur V2 lance en une seule commande :

- creation/mise a jour des tables techniques
- application des migrations SQL en attente
- scraping des sources activees
- insertion ou mise a jour des annonces
- scoring DVF
- enrichissement cadastre et urbanisme
- archivage puis nettoyage des annonces non revues depuis 30 jours
- ecriture d'un log dans `logs/`
- stockage du statut du run dans la table `automation_runs`

Test manuel :

```powershell
.\scripts\run_automation.ps1 -MaxPages 1 -EnrichmentLimit 100
```

Commande Python equivalente :

```bash
python -m services.jobs.run_automation --max-pages 1 --enrichment-limit 100
```

Installer la tache planifiee Windows toutes les 6 heures :

```powershell
.\scripts\install_windows_task.ps1 -FrequencyHours 6 -StartTime "06:00"
```

Desinstaller la tache :

```powershell
.\scripts\uninstall_windows_task.ps1
```

Le dernier resume JSON est ecrit dans `data/automation/latest_run.json`. Les derniers runs sont aussi disponibles via l'API protegee :

```http
GET /api/jobs/runs?limit=20
```

### 6 bis. Migrations et sauvegardes

Les migrations SQL versionnees sont placees dans `database/migrations/` et suivies dans la table `schema_migrations`.
Chaque nouvelle migration doit etre commit avec le code qui l'utilise, afin qu'un deploiement ou une nouvelle installation retrouve exactement le meme schema.

Application manuelle :

```bash
python -m database.migrations
```

Sauvegarde PostgreSQL au format custom :

```powershell
.\scripts\backup_database.ps1
```

Sauvegarde chiffrée avec rétention et ACL restreinte :

```powershell
.\scripts\backup_database.ps1 -GpgRecipient ops@example.com -RetentionDays 30 -RestrictAcl
```

Restauration depuis une sauvegarde :

```powershell
.\scripts\restore_database.ps1 -BackupPath .\data\backups\nom_du_dump.dump
```

Les fichiers `.dump.gpg` sont déchiffrés temporairement pendant la restauration puis supprimés.

Par defaut, les annonces non revues depuis 30 jours sont copiees dans `annonces_archive` avec un snapshot JSONB de leur enrichissement, puis supprimees de `annonces`.

### 7. Demarrer l'API

```bash
uvicorn apps.api.main:app --reload
```

Créer un utilisateur pour le dashboard privé :

```bash
python database/create_user.py utilisateur@example.com motdepasse
```

L'endpoint `GET /api/annonces` est protégé par authentification et retourne les annonces filtrées sous forme paginée.
Les routes d'exploitation comme `GET /api/jobs/runs` sont protégées par authentification.

Réinitialisation de mot de passe utilisateur :

- L'utilisateur clique sur `Mot de passe oublié ?` depuis l'ecran de connexion.
- Il renseigne son email.
- Si le compte existe, l'API genere un token a usage unique et envoie un lien par SMTP.
- Le lien ouvre le dashboard avec `?reset_token=...` et affiche le formulaire de nouveau mot de passe.
- Le token est stocke uniquement sous forme de hash, expire par defaut apres 60 minutes et devient invalide apres usage.

Ajout d'un acces depuis le dashboard :

- Tout utilisateur connecte peut renseigner une adresse e-mail dans le panneau `Membres`.
- L'API `POST /api/auth/members` cree le compte si l'e-mail n'existe pas encore, avec un mot de passe temporaire aleatoire stocke uniquement sous forme de hash bcrypt.
- Le nouveau membre recoit un lien a usage unique pour choisir lui-meme son mot de passe ; le mot de passe final n'est jamais envoye par e-mail ni stocke en clair.
- Si le compte existe deja, aucun doublon n'est cree et une nouvelle invitation est envoyee.
- Le dashboard recharge la liste des comptes apres invitation pour confirmer visuellement la creation ou l'existence du membre.
- La creation, l'envoi d'invitation, les echecs d'e-mail et la definition du mot de passe sont journalises dans `audit_events`.

Un script de secours existe pour generer un token manuellement en cas d'incident SMTP :

```bash
python database/create_password_reset_token.py utilisateur@example.com --ttl-minutes 60 --created-by-email support@example.com
```

### 7 bis. Sécurité applicative

- Authentification par JWT signé stocké en cookie `HttpOnly`.
- Cookie CSRF séparé et en-tête `X-CSRF-Token` requis sur les routes API mutantes hors login.
- Cookies `Secure` activés automatiquement en production, avec refus des secrets JWT faibles ou par défaut.
- Headers sécurité HTTP : CSP minimale, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, HSTS si HTTPS forcé.
- Hôtes et origines CORS configurables via `ALLOWED_HOSTS` et `API_CORS_ORIGINS`.
- Journal d'audit en base (`audit_events`) pour connexions, échecs, consultations sensibles et automatisations.
- Réinitialisation de mot de passe par email, avec token a usage unique, expirant et audité.
- Dépendances frontend et Python épinglées ; lancer `npm run audit` côté `apps/web` et un scan de secrets avant livraison.

### 8. Demarrer le dashboard web

```bash
cd apps/web
npm install
npm run dev
```

L'interface React est disponible sur `http://127.0.0.1:5173` et proxifie les appels `/api` vers FastAPI.

## Système de scoring

Le score (0–100) est calculé dans `services/deals.py` selon trois critères :

- **Écart au prix médian DVF** : plus l'annonce est décotée par rapport au marché local, plus le score est élevé.
- **Position dans l'interquartile** : bonus si l'annonce se situe sous le Q1 des prix du secteur.
- **Fiabilité de la référence** : pondération selon le nombre de transactions DVF disponibles sur la zone (plus il y en a, plus le score est fiable).

Les données DVF utilisées couvrent les départements 06, 13 et 83, et excluent automatiquement les valeurs aberrantes (prix au m² hors de la plage 500–20 000 €, surfaces hors 10–500 m²).

## Nettoyage et normalisation

Fonctions principales dans `utils/cleaning.py` :

- `extract_number(text)` — convertit une chaîne en float, gère les formats européens/US, les suffixes `k`/`K`/`m`/`M` et les unités (`m²`, `€`).
- `normalisation_language(text)` — normalise les séparateurs décimaux et de milliers.
- `filter_annonces(annonces)` — appelle `normalization()` sur toutes les annonces (prix, surface, prix/m², rooms, département).

## Tests

```bash
pytest -v
```

Les tests couvrent `extract_number`, `normalisation_language` (formats variés) et les interactions base de données (connexion, création de tables, insertion, gestion des erreurs) via mocks.

## Maintenance

Supprimer les annonces non vues depuis plus de 14 jours :

```bash
python database/reset_db.py
```

Supprimer toutes les tables :

```bash
python database/reset_tables.py
```
