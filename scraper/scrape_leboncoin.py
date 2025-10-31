from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig
from utils.config import get_browser_config
import json, os, time, random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/leboncoin.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_bienici = json.load(f)

site = {
    "url": "https://www.leboncoin.fr/recherche?category=9&real_estate_type=1,2,3,4,5&sort=time&order=desc",
    "schema": schema_bienici,
    "wait_for": "css:li[data-test-id='ad']",
    "prefix": "leboncoin.fr"
}


async def scrape_leboncoin(max_pages=3):
    """Scrape plusieurs pages de Leboncoin avec Crawl4AI et gère la pagination."""
    browser_config = get_browser_config()
    all_annonces = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        #for page in range(1, max_pages + 1):
            #url = f"{site['url']}?page={page}"

            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
                wait_for="css:li[data-test-id='ad']",
            )

            result = await crawler.arun(url=site["url"], config=crawler_config, wait_after_load=10)

            time.sleep(random.uniform(1, 3))
            

            """
            if not result or not result.extracted_content:
                break  
            """
            annonces = json.loads(result.extracted_content)
            """
            if not annonces:
                break  
            """
            print(result.status_code)
            
            all_annonces.extend(annonces)

    return all_annonces
