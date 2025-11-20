####################################


############# Imports ##############

import json, os
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

###########################################################################


############# Ouverture des schémas et informations diverses ##############

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/libramemoria.json")

# On ouvre le schéma JSON pour AvoVentes
with open(schema_path, "r", encoding="utf-8") as f:
    schema_avoventes = json.load(f)

site = {
    "wait_for": "css:div.tableau_liste",
}


#################################################


############# Programme principal ###############

async def scrape_libramemoria() -> list:
    """
    Scrape la page principale de LibraMemoria avec Crawl4AI à partir du schéma JSON fourni.
    
    Returns:
        list: Liste des annonces extraites et formatées.
    """
    all_annonces = []

    # Config simple puisque tout fonctionne, pas besoin de proxies.
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for=site["wait_for"],
            extraction_strategy=JsonCssExtractionStrategy(schema=schema_avoventes),
            only_text=True
        )

        result = await crawler.arun(
            url="https://www.libramemoria.com/avis/bouches-du-rhone/13055-marseille",
            config=crawler_config
        )

        if not result or not result.extracted_content:
            print("Aucun titre extrait.")
            return []
        
        if result.status_code == 429:
            print(f"429 Too Many Requests reçu, arrêt du scraping.")
            return []
            
        if result.status_code == 403:
            print(f"403 Forbidden reçu, arrêt du scraping.")
            return []

        annonces = json.loads(result.extracted_content)           

        all_annonces.extend(annonces)

    return annonces
