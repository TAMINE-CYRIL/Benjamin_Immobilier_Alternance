import asyncio, os, json, random, datetime
from scraper.immobilier.scrape_atypiques import scrape_atypiques
from scraper.immobilier.scrape_bienici import scrape_bienici
from scraper.immobilier.scrape_seloger import scrape_seloger
from scraper.immobilier.scrape_pap import scrape_pap
from scraper.immobilier.scrape_leboncoin import scrape_leboncoin
from scraper.immobilier.scrape_logicimmo import scrape_logicimmo
from scraper.scrape_libramemoria import scrape_libramemoria
from scraper.immobilier.scrape_avoventes import scrape_avoventes
from utils.cleaning import filter_annonces
from utils.db import create_tables, insert_annonces


async def main():
    """
    Fonction principale asynchrone pour lancer le scraping de plusieurs sites immobiliers
    et sauvegarder les résultats dans un fichier JSON.
    """

    create_tables()
    print("Démarrage du scraping...")

    os.makedirs("data", exist_ok=True)

    start_time = datetime.datetime.now()
    print("Début :", start_time)

    # Liste des scrapers à lancer (tu peux en commenter certains pendant les tests)
    scrapers = [
        ("Leboncoin", scrape_leboncoin(max_pages=4, use_proxies=True)),
        ("SeLoger", scrape_seloger(max_pages=2, use_proxies=True)),    
        ("Bienici", scrape_bienici()),
        ("Espaces Atypiques", scrape_atypiques()),
        ("PAP", scrape_pap()),
        ("LogicImmo", scrape_logicimmo(max_pages=2, use_proxies=True)),
        ("Avoventes", scrape_avoventes()),
        #("LibraMemoria", scrape_libramemoria())
    ]

    all_annonces = []

    for name, scraper_coro in scrapers:
        print(f"\n===== Lancement scraper : {name} =====")
        try:
            res = await scraper_coro
            await asyncio.sleep(random.uniform(6, 12))

            if res:
                res = filter_annonces(res)
                print(f"{len(res)} annonces gardées après filtrage pour {name}")
                all_annonces.extend(res)
            else:
                print(f"Aucune annonce retournée par {name}")

        except Exception as e:
            print(f"Erreur lors du scraping {name} : {e}")

    print(f"\nTotal {len(all_annonces)} annonces récupérées (tous sites confondus)")

    #insert_annonces(all_annonces) 

    # Sauvegarde des données dans un fichier JSON
    output_path = os.path.join("data", "annonces.json")
    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(all_annonces, outfile, ensure_ascii=False, indent=4)

    print(f"Données sauvegardées dans {output_path}")

    end_time = datetime.datetime.now()
    print("Fin :", end_time)
    print("Durée totale :", end_time - start_time)


if __name__ == "__main__":
    asyncio.run(main())
