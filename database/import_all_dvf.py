from pathlib import Path
import re

from import_dvf import import_dvf_with_staging
from aggregate_dvf import aggregate_dvf, aggregate_dvf_multi_years
from stats_nb_transactions import compute_nb_transactions_quartiles


BASE_DIR = Path(__file__).resolve().parent.parent
DVF_DIR = BASE_DIR / "data" / "dvf"


def extract_year(filename: str) -> int:
    """
    Extrait l'année depuis le nom du fichier DVF.
    Exemple : ValeursFoncieres-2023.txt -> 2023
    Args:
        filename: Nom du fichier DVF.
    Returns:
        L'année extraite en tant qu'entier.
    """
    match = re.search(r"\b(20\d{2})\b", filename)
    if not match:
        raise ValueError(f"Impossible d'extraire l'année depuis {filename}")
    return int(match.group(1))


def import_all_dvf():
    """
    Importe et agrège tous les fichiers DVF présents dans le dossier data/dvf.
    1. Pour chaque fichier DVF, importe les données dans la table dvf_raw
    2. Agrège les données importées dans la table dvf_stats (par année)
    3. Calcule la moyenne multi-années sur toutes les années disponibles
    4. Nettoie la table dvf_raw après traitement
    
    """
    # Si on ne trouve pas le dossier DVF, on lève une erreur
    if not DVF_DIR.exists():
        raise FileNotFoundError(f"Dossier DVF introuvable : {DVF_DIR}")

    files = sorted(DVF_DIR.glob("ValeursFoncieres-*.txt"))

    if not files:
        raise FileNotFoundError("Aucun fichier DVF trouvé")

    print(f"{len(files)} fichiers DVF détectés")

    # Liste pour stocker toutes les années importées
    years_imported = []

    # Étape 1 : Import et agrégation par année
    for dvf_file in files:
        year = extract_year(dvf_file.name)
        years_imported.append(year)

        print(f"Traitement du fichier {dvf_file.name}")
        print(f"Année détectée : {year}")

        # Import DVF → dvf_raw
        import_dvf_with_staging(dvf_file, year)

        # Agrégation DVF → dvf_stats (une ligne par année)
        aggregate_dvf(year)

    # Étape 2 : Calcul de la moyenne multi-années
    if len(years_imported) > 0:
        print(f"Calcul de la moyenne sur {len(years_imported)} année(s)")
        print(f"Années concernées : {', '.join(map(str, sorted(years_imported)))}")
        aggregate_dvf_multi_years(years=years_imported)
    


    # Étape 3 : Nettoyage
    """
    print("Import et agrégation DVF multi-années terminés")
    print("Nettoyage de la table dvf_raw")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE dvf_raw;")
    conn.commit()
    cur.close()
    conn.close()
    
    print("Processus terminé avec succès")
    """
    compute_nb_transactions_quartiles()

if __name__ == "__main__":
    import_all_dvf()