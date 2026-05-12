#!/usr/bin/env python3
"""
Script d'initialisation pour la Phase 1 : Full-Text Search PostgreSQL

Ce script :
1. Crée/met à jour la colonne search_vector
2. Crée le trigger et la fonction PostgreSQL
3. Remplit search_vector pour les annonces existantes
"""

import sys
import time

try:
    from database.connection import get_connection
    from database.create_tables import create_fulltext_search_trigger, populate_fulltext_search_vector
except ImportError:
    from connection import get_connection
    sys.path.insert(0, '.')
    from create_tables import create_fulltext_search_trigger, populate_fulltext_search_vector


def main():
    print("=" * 70)
    print("PHASE 1 : INITIALISATION FULL-TEXT SEARCH POSTGRESQL")
    print("=" * 70)
    
    try:
        # Étape 1 : Créer/mettre à jour colonne et trigger
        print("\n[1/2] Création de la colonne search_vector et du trigger...")
        start = time.time()
        create_fulltext_search_trigger()
        elapsed = time.time() - start
        print(f"✓ Colonne et trigger créés en {elapsed:.2f}s")
        
        # Étape 2 : Remplir les données existantes
        print("\n[2/2] Remplissage du search_vector pour les annonces existantes...")
        start = time.time()
        count = populate_fulltext_search_vector()
        elapsed = time.time() - start
        print(f"✓ {count} annonces mises à jour en {elapsed:.2f}s")
        
        print("\n" + "=" * 70)
        print("✓ PHASE 1 COMPLÉTÉE AVEC SUCCÈS")
        print("=" * 70)
        print("\nÉtapes suivantes :")
        print("  - Phase 2 : Ajouter géométrie PostGIS et index spatial")
        print("  - Phase 3 : Créer index trigramme et multi-colonnes")
        print("  - Phase 4 : Intégrer pertinence dans tri et requêtes")
        print("\nVérification rapide :")
        print("  SELECT COUNT(*) FROM annonces WHERE search_vector IS NOT NULL;")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ ERREUR : {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
