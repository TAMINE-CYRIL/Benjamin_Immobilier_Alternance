from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json, os
from utils.cleaning import extract_number

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/bienici.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_bienici = json.load(f)

site = {
    "url": "https://www.bienici.com/recherche/achat/france",
    "schema": schema_bienici,
    "wait_for": "css:article.ad-overview",
    "prefix": "https://www.bienici.com",
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

def format_url(annonces):
    """Ajoute le préfixe du site aux URLs relatives."""
    for annonce in annonces:
        url = annonce.get("url")
        if url and not url.startswith("http"):
            annonce["url"] = site["prefix"] + url
    return annonces

async def scrape_bienici():
    """Scrape le site BienIci à l’aide de Crawl4AI et du schéma JSON."""
    browser_config = BrowserConfig(browser_type="chromium", headless=True)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for=site["wait_for"],
            extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
        )

        result = await crawler.arun(url=site["url"], config=crawler_config, wait_after_load=10)

        if not result or not result.extracted_content:
            return []

        annonces = json.loads(result.extracted_content)
        annonces = format_url(annonces)
        annonces = format_surface(annonces)
        return annonces
