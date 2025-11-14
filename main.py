from scraper.scrape_atypiques import scrape_atypiques 
from scraper.scrape_bienici import scrape_bienici
from scraper.scrape_seloger import scrape_seloger
from scraper.scrape_pap import scrape_pap
from scraper.scrape_leboncoin import scrape_leboncoin
from scraper.scrape_logicimmo import scrape_logicimmo
from scraper.scrape_avoventes import scrape_avoventes 
from utils.cleaning import filter_annonces
from utils.db import create_tables, insert_annonces
import asyncio, os, json, time, random, datetime



async def main():
    """
    Fonction principale asynchrone pour lancer le scraping de plusieurs sites immobiliers
    et sauvegarder les résultats dans un fichier JSON.
    """

    create_tables()
    print("Démarrage du scraping...")

    os.mkdir("data") if not os.path.exists("data") else None

    print(datetime.datetime.now())

    # La liste des COROUTINES, mais exécution séquentielle
    scrapers = [
        scrape_avoventes(),
        scrape_bienici(),
        scrape_pap(),
        scrape_logicimmo(),
        scrape_leboncoin(),
        scrape_seloger(),
        
    ]

    all_annonces = []

    for scraper in scrapers:
        try:
            res = await scraper  # attendre le résultat du scraper
            await asyncio.sleep(random.uniform(6, 12))  # pause anti-bot

            if res:
                res = filter_annonces(res)
                all_annonces.extend(res)

        except Exception as e:
            print(f"Erreur lors du scraping : {e}")

    print(f"{len(all_annonces)} annonces récupérées")
    insert_annonces(all_annonces)

    # Sauvegarde des données dans un fichier JSON
    f = os.path.join("data", "annonces.json")
    with open(f, "w", encoding="utf-8") as outfile:
        json.dump(all_annonces, outfile, ensure_ascii=False, indent=4)

    print(f"Données sauvegardées dans {f}") 
    print(datetime.datetime.now())



if __name__ == "__main__":
    asyncio.run(main())
