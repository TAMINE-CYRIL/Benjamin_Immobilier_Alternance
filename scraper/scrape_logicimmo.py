import os, json

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from utils.config import get_browser_config


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/logicimmo.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema_logicimmo = json.load(f)


site = {
    "url":"",
    "schema": schema_logicimmo,
    "prefix": "",
    "wait_for": ""
}

async def scrape_logicimmo():
    """
    Fonction asynchrone permettant de lancer le Web Crawler pour récupérer les données du site LogicImmo à l'aide d'une extraction
    CSS et d'un schéma JSON.
    """
    browser_config = get_browser_config()
    async with AsyncWebCrawler(config= browser_config) as crawler:
        crawler_config = CrawlerRunConfig()
        result = await crawler.arun(
            url=site["url"], 
            config=crawler_config, 
            wait_after_load=15
        )

        if not result or not result.extracted_content:
            return []
    
        annonces = json.loads(result.extracted_content)
        return annonces