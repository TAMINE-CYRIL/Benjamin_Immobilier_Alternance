# main_obits.py
import asyncio, os, json, datetime
from scraper.scrape_libramemoria import scrape_libramemoria
# ou si tu n'as pas encore déplacé le fichier :
# from scraper.scrape_libramemoria import scrape_libramemoria


async def main():
    print("Démarrage du scraping Libramemoria...")

    os.makedirs("data", exist_ok=True)

    start_time = datetime.datetime.now()
    print("Début :", start_time)

    try:
        avis = await scrape_libramemoria()
        if not avis:
            print("Aucun avis récupéré.")
            return

        print(f"{len(avis)} avis récupérés.")

        output_path = os.path.join("data", "avis_deces.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(avis, f, ensure_ascii=False, indent=4)

        print(f"Données sauvegardées dans {output_path}")

    except Exception as e:
        print(f"Erreur lors du scraping Libramemoria : {e}")

    end_time = datetime.datetime.now()
    print("Fin :", end_time)
    print("Durée totale :", end_time - start_time)


if __name__ == "__main__":
    asyncio.run(main())
