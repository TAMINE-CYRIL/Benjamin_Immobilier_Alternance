import asyncio
from scrape_atypiques import scrape_atypiques 

async def main():
    print("🚀 Démarrage du scraping...")

    scrapers = [scrape_atypiques()]

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
