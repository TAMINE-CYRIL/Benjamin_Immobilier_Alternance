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

## Structure du dépôt
- `scraper/` — scripts de scraping par source
- `utils/` — fonctions utilitaires (nettoyage, config, db)
- `data/` — exemples / sorties, dossier crée grâce au fichier `main.py`.
- `schema/` — schémas JSON pour chaque source
- `tests/` — tests unitaires
  
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




