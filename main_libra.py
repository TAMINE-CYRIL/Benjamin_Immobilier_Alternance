import asyncio, os, csv, json
from scrapers.scrape_libramemoria import scrape_libramemoria


async def main():
    """
    Programme principal pour scraper les avis de décès sur Libramemoria et 
    sauvegarder les résultats en JSON et CSV."""
    print("Démarrage du scraping Libramemoria...")

    os.makedirs("data", exist_ok=True)


    try:
        avis = await scrape_libramemoria()
        if not avis:
            print("Aucun avis récupéré.")
            return

        print(f"{len(avis)} avis récupérés.")


        output_path = os.path.join("data", "avis_deces.json")
        with open(output_path, "w", encoding="utf-8") as outfile:
            json.dump(avis, outfile, ensure_ascii=False, indent=4)

        output_path = os.path.join("data", "avis_deces.csv")


        fieldnames = [
            "full_name",
            "age",
            "commune",
            "departement",
            "publication_date"
            
        ]    

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                quoting=csv.QUOTE_ALL,
                delimiter=";", 
            )
            writer.writeheader()

            for item in avis:
                # Si certaines valeurs sont des listes (ex: plusieurs communes), on les joint
                row = item.copy()
                writer.writerow(row)

    except Exception as e:
        print(f"Erreur lors du scraping Libramemoria : {e}")


if __name__ == "__main__":
    asyncio.run(main())
