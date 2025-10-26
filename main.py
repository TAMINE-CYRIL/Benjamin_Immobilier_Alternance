from scraper.scrape_atypiques import scrape_atypiques 
from scraper.scrape_bienici import scrape_bienici
from scraper.scrape_pap import scrape_pap
import asyncio


async def main():
    print("Démarrage du scraping...")

    scrapers = [scrape_atypiques(), scrape_bienici(), scrape_pap()]

    results = await asyncio.gather(*scrapers, return_exceptions=True)

    all_annonces = []
    for res in results:
        if isinstance(res, Exception):
            print(f"Erreur lors du scraping : {res}")
            continue
        all_annonces.extend(res)

    print(f"{len(all_annonces)} annonces récupérées")

if __name__ == "__main__":
    asyncio.run(main())
