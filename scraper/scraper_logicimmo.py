from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from utils.cleaning import extract_number
import json, os, time, random, regex as re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/logic_immo.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_logicimmo = json.load(f)

site = {
    "url": "https://www.logic-immo.com/classified-search?distributionTypes=Buy&estateTypes=House,Apartment&locations=AD02FR1&order=DateDesc",
    "schema": schema_logicimmo,
    "wait_for": "div[data-testid='serp-core-classified-card-testid']",
    "prefix": "https://www.logic-immo.com",
}

def extract_zip_code(address: str):
    if not address:
        return None
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None


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


async def scrape_logicimmo(max_pages=3):
    """Scrape plusieurs pages de Logic Immo avec Crawl4AI et gère la pagination."""
    browser_config = BrowserConfig(browser_type="chromium", headless=False)
    all_annonces = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        #for page in range(1, max_pages + 1):
            #url = f"{site['url']}?page={page}"

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
            """
            annonces = json.loads(result.extracted_content)
            """
            if not annonces:
                break  
            """
            print(result.status_code)
            annonces = format_surface(annonces)
            for annonce in annonces:
                    adresse = annonce.get("address", "")
                    annonce["zip_code"] = extract_zip_code(adresse)
            all_annonces.extend(annonces)

    return all_annonces
