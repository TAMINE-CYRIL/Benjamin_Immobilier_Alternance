from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig
from utils.config import get_browser_config
from utils.cleaning import extract_number
import json, os, time, random


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/seloger.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema_seloger = json.load(f)


site = {
    "url": "https://www.seloger.com/classified-search?distributionTypes=Buy,Buy_Auction,Compulsory_Auction&estateTypes=House,Apartment&locations=AD02FR1&page=1",
    "schema": schema_seloger,
    "prefix": "https://www.seloger.com",
    "wait_for": "div[data-testid^='classified-card-mfe-']",
}

def format_surface(annonces):
    """Calcule la surface quand on n’a que le prix et le prix/m²."""
    clean_annonces = []
    for annonce in annonces:
        price = extract_number(annonce.get("price"))
        surface_price = extract_number(annonce.get("surface"))

        annonce["price"] = price

        if price and surface_price:
            annonce["surface"] = price // surface_price
        else:
            annonce["surface"] = None

        clean_annonces.append(annonce)
    return clean_annonces


async def scrape_seloger(max_pages=4):
    """
    Fonction asynchrone permettant de lancer le Web Crawler pour récupérer les données du site SeLoger à l'aide d'une extraction
    CSS et d'un schéma JSON.
    """
    browser_config = get_browser_config()
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):
            site["url"] = f"https://www.seloger.com/classified-search?distributionTypes=Buy,Buy_Auction,Compulsory_Auction&estateTypes=House,Apartment&locations=AD02FR1&page={page}"
            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for_timeout=60000,
                    wait_for=site["wait_for"],
                    extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
                    simulate_user=True,
                    override_navigator=True,
                )

                
            result = await crawler.arun(
                url=site["url"], 
                config=crawler_config, 
                wait_after_load=15
            )

            if not result or not result.extracted_content:
                return []
                                
            annonces = json.loads(result.extracted_content)
            annonces = format_surface(annonces)
    return annonces
