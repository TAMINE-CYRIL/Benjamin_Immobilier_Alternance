from scraper.scrape_atypiques import scrape_atypiques 
from scraper.scrape_bienici import scrape_bienici
from scraper.scrape_pap import scrape_pap
from utils.cleaning import filter_annonces
import asyncio, os, json

async def main():
    print("Démarrage du scraping...")

    scrapers = [scrape_atypiques(), scrape_bienici(), scrape_pap()]

    results = await asyncio.gather(*scrapers, return_exceptions=True)

    all_annonces = []
    for res in results:
        if isinstance(res, Exception):
            print(f"Erreur lors du scraping : {res}")
            continue
        res = filter_annonces(res)
        all_annonces.extend(res)

    print(f"{len(all_annonces)} annonces récupérées")

    f = os.path.join("data", "annonces.json")
    with open(f, "w", encoding="utf-8") as outfile:
        json.dump(all_annonces, outfile, ensure_ascii=False, indent=4)
    print(f"Données sauvegardées dans {f}") 
    


if __name__ == "__main__":
    asyncio.run(main())
