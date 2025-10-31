from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json, os, time, random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/espace_atypique.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_atypiques = json.load(f)

detail_schema_path = os.path.join(BASE_DIR, "../schema/details/espace_atypique_details.json")

with open(detail_schema_path, "r", encoding="utf-8") as f:
    schema_detail = json.load(f)


site = {
    "url": "https://www.espaces-atypiques.com/ventes/page/1/?prj=ventes&pl&pmax&critere1&s&order&map&pt=vente",
    "schema": schema_atypiques,
    "wait_for": "css:.preview-annonce",
    "prefix": "https://www.espaces-atypiques.com",
}

async def scrape_details(crawler, url, schema):
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for="css:#infos-cles",
        extraction_strategy=JsonCssExtractionStrategy(schema=schema),
    )

    result = await crawler.arun(url=url, config=config, wait_after_load=5)

    if result and result.extracted_content:
        return json.loads(result.extracted_content)

    return {}



async def scrape_atypiques(max_pages=3):
    """
    Scrape plusieurs pages du site Espaces Atypiques à l’aide de Crawl4AI et du schéma JSON.
    """
    browser_config = BrowserConfig(browser_type="chromium", headless=True)
    all_annonces = []
    async with AsyncWebCrawler(config=browser_config) as crawler:
        #for page in range(1, max_pages + 1):
            #site["url"] = f"https://www.espaces-atypiques.com/ventes/page/{page}/?prj=ventes&pl&pmax&critere1&s&order&map&pt=vente"
            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for=site["wait_for"],
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
            )

            result = await crawler.arun(url=site["url"], config=crawler_config, wait_after_load=10)
            
            time.sleep(random.uniform(1, 3))
            """
            if not result or not result.extracted_content:
                break  

            annonces = json.loads(result.extracted_content)
            if not annonces:
                break  
            """

            annonces = json.loads(result.extracted_content)

            for annonce in annonces:
                url = annonce.get("url")
                details = await scrape_details(crawler, url, schema_detail)                
                for detail in details:
                    if detail['label'] == 'Chambres':
                        annonce['bedrooms'] = detail['value']
                    elif detail['label'] == details[0]['label']: 
                        zip_code = ''.join(filter(str.isdigit, detail['value']))
                        if len(zip_code) == 5:
                            annonce['zip_code'] = zip_code
                        
                    time.sleep(random.uniform(2,5))

            all_annonces.extend(annonces)

    return all_annonces
