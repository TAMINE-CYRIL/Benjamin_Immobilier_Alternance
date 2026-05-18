####################################
############# Imports ##############

import json
import os
import re
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

###########################################################################
############# Ouverture des schémas et informations diverses ##############

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/libramemoria.json")

# On ouvre le schéma JSON pour Libramemoria
with open(schema_path, "r", encoding="utf-8") as f:
    schema_libramemoria = json.load(f)

site = {
    "wait_for": "css:div.tableau_liste",
}


#################################################
############# Filtrage des données ##############

def clean_full_name(raw_name: str) -> str:
    """Nettoie le nom complet : espaces et '(93 ans)' éventuel."""
    name = re.sub(r"\s+", " ", raw_name).strip()
    name = re.sub(r"\(\s*\d+\s*ans\s*\)", "", name).strip()
    return name


def extract_date_from_title(title: str) -> str | None:
    """
    Extrait une date au format JJ/MM/AAAA depuis une chaîne,
    ex: 'Avis de décès publiés le 20/11/2025' -> '20/11/2025'
    """
    match = re.search(r"\b\d{2}/\d{2}/\d{4}\b", title)
    return match.group(0) if match else None


#################################################
############# Programme principal ###############

async def scrape_libramemoria() -> list:
    """
    Scrape la page principale de LibraMemoria avec Crawl4AI à partir du schéma JSON fourni.
    
    Returns:
        list: Liste aplatie des avis extraits et formatés (un dict par défunt).
    """
    all_notices = []

    # Config simple puisque tout fonctionne, pas besoin de proxies.
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for=site["wait_for"],
            extraction_strategy=JsonCssExtractionStrategy(schema=schema_libramemoria),
            only_text=True
        )

        result = await crawler.arun(
            url="https://www.libramemoria.com/avis/bouches-du-rhone/13055-marseille",
            config=crawler_config
        )

        if not result or not result.extracted_content:
            print("Aucun avis extrait.")
            return []
        
        if result.status_code == 429:
            print("429 Too Many Requests reçu, arrêt du scraping.")
            return []
            
        if result.status_code == 403:
            print("403 Forbidden reçu, arrêt du scraping.")
            return []

        raw_blocks = json.loads(result.extracted_content)
        all_notices = []

        # Pour un bloc d'un jour dans notre bloc
        for day_block in raw_blocks:
            raw_pub_title = day_block.get("publication_date", "")
            publication_date = extract_date_from_title(raw_pub_title)

            day_notices = day_block.get("avis", [])

            # Pour un avis sur notre bloc d'un jour
            for notice in day_notices:
                full_name = notice.get("full_name")
                if full_name:
                    notice["full_name"] = clean_full_name(full_name)

                notice["publication_date"] = publication_date
                all_notices.append(notice)

    return all_notices
