from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/pap.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_pap = json.load(f)

def format_url(annonces):
    filtrage = []
    for annonce in annonces:
        url = annonce.get("url")
        if url and not url.startswith("http"):
            annonce["url"] = site.get("prefix") + url
        filtrage.append(annonce)
    return filtrage

def format_title(annonces):
    filtrage = []
    for annonce in annonces:  
        title = annonce.get("title") 
        url = annonce.get("url")

        if "www.immoneuf.com" in url:
            continue
        if url:
            url_clean = url.replace("/annonces/", "-").split("-")
            annonce["title"] = "Vente " + url_clean[1] + " "+ title
        filtrage.append(annonce)
    return filtrage

# Données du site à scraper sous forme de tableau.
site = {
        "url": "https://www.pap.fr/annonce/vente-immobiliere-france-g25",
        "schema": schema_pap,
        "wait_for": "css:.search-list-item-alt",
        "prefix": "https://www.pap.fr",
        "filter": "pap"
    }

async def scrape_pap():
    """
    Fonction asynchrone permettant de lancer le Web Crawler pour récupérer les données du site PAP à l'aide d'une extraction
    CSS et d'un schéma JSON.
    """
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
                crawler_config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    wait_for=site.get("wait_for"),
                    extraction_strategy=JsonCssExtractionStrategy(
                        schema=site.get("schema")),
                )
                result = await crawler.arun(url=site.get("url"), config=crawler_config, wait_after_load=10)

                if not result or not result.extracted_content:
                    return []
                
                annonces = json.loads(result.extracted_content)
                annonces = format_url(annonces)
                annonces = format_title(annonces)
                return annonces



