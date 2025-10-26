from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/espace_atypique.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_atypiques = json.load(f)

site = {
    "url": "https://www.espaces-atypiques.com/ventes/?prj=ventes&pl=&pmax=&critere1=&s=&order=&map=&pt=vente",
    "schema": schema_atypiques,
    "wait_for": "css:.preview-annonce",
    "prefix": "https://www.espaces-atypiques.com",
}

async def scrape_atypiques():
    """
    Scrape le site Espaces Atypiques à l’aide de Crawl4AI et du schéma JSON.
    """
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
        return annonces
