from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from utils.cleaning import extract_number
import json, os, time, random, regex as re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/bienici.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_bienici = json.load(f)

site = {
    "url": "https://www.bienici.com/recherche/achat/france/maisonvilla,appartement,parking,terrain,loft,commerce,batiment,chateau,local,bureau,hotel,autres",
    "schema": schema_bienici,
    "wait_for": "css:article.ad-overview",
    "prefix": "https://www.bienici.com",
    "source": "BienIci"
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

def format_url(annonces):
    """Ajoute le préfixe du site aux URLs relatives."""
    for annonce in annonces:
        url = annonce.get("url")
        if url and not url.startswith("http"):
            annonce["url"] = site["prefix"] + url
    return annonces

async def scrape_bienici(max_pages=3):
    """Scrape plusieurs pages de BienIci avec Crawl4AI et gère la pagination."""
    browser_config = BrowserConfig(browser_type="chromium", headless=True)
    all_annonces = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):
            url = f"{site['url']}?page={page}"

            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for=site["wait_for"],
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
            )

            result = await crawler.arun(url=site["url"], config=crawler_config, wait_after_load=10)

            time.sleep(random.uniform(1, 3))
            if not result or not result.extracted_content:
                print("Aucun résultat extrait.")
                return []  
            annonces = json.loads(result.extracted_content)
            if not annonces:
                print("Aucune annonce trouvée.")
                return []  
            
            annonces = format_url(annonces)
            annonces = format_surface(annonces)
            for annonce in annonces:
                    adresse = annonce.get("address", "")
                    annonce["zip_code"] = extract_zip_code(adresse)
                    annonce["source"] = site.get("source")
            all_annonces.extend(annonces)

    return all_annonces
