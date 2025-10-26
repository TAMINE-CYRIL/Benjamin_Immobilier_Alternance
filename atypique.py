from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import asyncio, json
import json

with open("json/bienici.json", "r", encoding="utf-8") as f:
    schema_bienici = json.load(f)

with open("json/espace_atypique.json", "r", encoding="utf-8") as f:
    schema_atypiques = json.load(f)

with open("json/pap.json", "r", encoding="utf-8") as f:
    schema_pap = json.load(f)


sites = [
    {
        "url": "https://www.espaces-atypiques.com/ventes/?prj=ventes&pl=&pmax=&critere1=&s=&order=&map=&pt=vente",
        "schema": schema_atypiques,
        "wait_for": "css:.preview-annonce  ",
        "prefix": "https://www.espaces-atypiques.com",
        "filter": "atypiques"
    },

]

async def extract_sites():
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
            for site in sites:
                crawler_config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    wait_for=site["wait_for"],
                    extraction_strategy=JsonCssExtractionStrategy(
                        schema=site["schema"]
                        ),
                )
                result = await crawler.arun(url=site["url"], config=crawler_config, wait_after_load=10)

                if result and result.extracted_content:
                    print(result.html[20000:])


if __name__ == "__main__":
    asyncio.run(extract_sites())
