# Projet de scraping immobilier — Crawl4AI + PostgreSQL

<div>
<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" />
<img src="https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white" />
<img src="https://img.shields.io/badge/fastapi-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
</div>

Projet de scraping, nettoyage et scoring d'annonces immobilières (sources : Bienici, SeLoger, PAP, Leboncoin, Logic Immo, Espaces Atypiques, AvoVentes).
On utilise [Crawl4AI](https://github.com/unclecode/crawl4ai) pour parcourir les différents sites et extraire les données, enrichies avec les données DVF (Demandes de Valeurs Foncières) pour calculer un score d'opportunité par annonce.

## Fonctionnalités

- Scrapers multi-sources dans `scrapers/immobilier/` (7 sources supportées)
- Scraping des avis de décès Libramemoria dans `scrapers/scrape_libramemoria.py`
- Normalisation et nettoyage des champs (prix, surface, code postal) dans `utils/cleaning.py`
- Rotation de proxies et randomisation des User-Agents dans `utils/config.py`
- Import et agrégation des données DVF (prix médian au m² par code postal, type de bien, année)
- Système de scoring des annonces basé sur l'écart au prix marché DVF (`services/deals.py`)
- API REST FastAPI exposant les annonces scorées (`apps/api/`)
- Tests unitaires avec pytest dans `tests/`

## Prérequis

- Python 3.9+
- PostgreSQL
- Git (optionnel)

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
PG_DB=nom_de_la_base
PG_USER=utilisateur
PG_PASSWORD=mot_de_passe
PG_HOST=localhost
PG_PORT=5432

# Optionnel : proxies Webshare pour les sites anti-bot
PROXIES=http://user:pass@host:port,...
```

## Utilisation

### 1. Créer les tables PostgreSQL

```bash
python database/create_tables.py
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

### 5. Démarrer l'API

```bash
uvicorn apps.api.main:app --reload
```

L'endpoint `GET /api/annonces` retourne toutes les annonces triées par score décroissant.

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
