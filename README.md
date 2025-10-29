# Projet de scraping à l'aide de Crawl4AI
<div>
<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" />
<img src="https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white" />
</div>
Projet de scraping et de nettoyage d'annonces immobilières (sources : Bienici, SeLoger, PAP, etc.).
On utilise l'outil open-source Crawl4AI afin de parcourir les différents sites et extraire les données.
Objectif : extraire, normaliser (prix, surface) et produire des jeux de données prêts pour analyse ou ingestion.

## Fonctionnalités
- Scrapers pour plusieurs sources dans `scraper/`
- Normalisation et nettoyage des champs (prix, surface) dans `utils/cleaning.py`
- Scripts d'exécution : `main.py`, `appllm.py`, `llm.py`
- Tests unitaires avec pytest dans `tests/`
- Génération d'un fichier JSON contenant les éléments extraits dans `data/`
- Création et insertion au sein d'une base de données PostgreSQL.

## Prérequis
- Python 3.9+
- (Optionnel) Git

## Architecture
Le projet est organisé en couches pour séparer ingestion, traitement et persistance.

Composants principaux
- `scrapers/` — couche d'ingestion
  - Scrapers spécialisés par source (bienici, seloger, pap, atypiques).
  - Responsabilité : récupérer les annonces brutes (HTML/JSON) et retourner une liste de dicts "bruts".
- `utils/` — utilitaires et traitement
  - `cleaning.py` : normalisation (extract_number, normalization, filter_annonces).
  - `db.py` : abstraction de persistance (fichiers, base, ES).
  - `config.py` : paramètres et variables d'environnement.
- `schema/` — contrats et validation
  - Schémas JSON par source pour documenter et valider les champs attendus (ex. jsonschema).
- `data/` — exemples et sorties
  - Exemples d'annonces, exports JSON pour tests/QA.
- `tests/` — validation automatisée
  - pytest pour couvrir parsing et normalisation.
- `/` — Dossier racine
  - Scripts principaux lançant le scraping.
  - Fichier requirements permettant d'installer toutes les dépendances.

## Installation
Installer les dépendances :
   ```
   pip install -r requirements.txt
   ```

## Utilisation
- Exécuter le script principal :
  ```
  python main.py
  ```
  
- Lancer le scraping avec LLM :
  ```
  python appllm.py
  python llm.py
  ```

## Nettoyage et normalisation
- Fonctions principales : `extract_number`, `normalization`, `filter_annonces` dans `utils/cleaning.py`.
- Gère différents formats : séparateurs européens/us, suffixes (k, K, m, M), unités (`m2`, `m²`, `€`), valeurs manquantes.

## Tests
- Exécuter tous les tests :
  ```
  pytest -v
  ```

## Structure du dépôt
- `scraper/` — scripts de scraping par source
- `utils/` — fonctions utilitaires (nettoyage, config, db)
- `data/` — exemples / sorties, dossier crée grâce au fichier `main.py`.
- `schema/` — schémas JSON pour chaque source
- `tests/` — tests unitaires


