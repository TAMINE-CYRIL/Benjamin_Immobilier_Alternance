from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json, os, regex as re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/avoventes.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_avoventes = json.load(f)

site = {
    "url": "https://avoventes.fr/recherche/toutes?sort=date&order=asc&display=liste",
    "schema": schema_avoventes,
    "wait_for": "css:div.row.mb-4.bg-white",
    "prefix": "https://avoventes.fr",
    "source_site": "AvoVentes"
}

def extract_zip_code(address: str):
    if not address:
        return None
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None

def format_price(price: str):
    if not price:
        return None
    
    match = re.search(r"(\d[\d\s.,]*)", price)
    if not match:
        return None

    price = match.group(1)

    price = price.replace("€", "").replace("\u00A0", "").strip()
    price = price.replace(" ", "").replace(",", ".")

    try:
        value = float(price)
        return int(value) if value.is_integer() else value
    except:
        return None


def format_address(address: str):
    parts = address.split(',')
    if parts:
        if len(parts) == 2:
            address = parts[0].strip()
            address = re.sub(r'^\s*\d{5}\s*', '', address).strip()
            return address
        else:
            address = parts[1].strip()
            address = re.sub(r'^\s*\d{5}\s*', '', address).strip()
            return address

def format_address_details(address: str):
    parts = address.split(',')
    if parts and len(parts) > 2:
        details = parts[0].strip()
        return details
    return None

def format_sale(annonces):
    """
    Formate les indications sur la vente :
    - Supprime les labels 'Date de la vente :' et 'Date des visites :'
    """
    clean_annonces = []

    for annonce in annonces:
        # Retirer les labels des dates
        if "sale_date" in annonce:
            annonce["sale_date"] = re.sub(r"Date de la vente\s*:\s*", "", annonce["sale_date"], flags=re.I)
        if "visit_date" in annonce:
            annonce["visit_date"] = re.sub(r"Date des visites\s*:\s*", "", annonce["visit_date"], flags=re.I)

        clean_annonces.append(annonce)

    return clean_annonces

async def scrape_avoventes():
    """Scrape la page principale d'AvoVentes avec Crawl4AI."""
    all_annonces = []
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for=site["wait_for"],
            extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
        )

        result = await crawler.arun(
            url=site["url"],
            config=crawler_config
        )

        if not result or not result.extracted_content:
            print("Aucun titre extrait.")
            return []

        annonces = json.loads(result.extracted_content)

        if result.html:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(result.html, 'html.parser')
            blocks = soup.select('div.row.mb-4.bg-white[data-link]')
            
            # Associer les URLs aux annonces extraites
            for i, (annonce, block) in enumerate(zip(annonces, blocks)):
                url = block.get('data-link', '')
                annonces[i]['url'] = url
        annonces = format_sale(annonces)
        for annonce in annonces:
            annonce["price"] = format_price(annonce.get("price", ""))
            annonce["zip_code"] = extract_zip_code(annonce.get("address", ""))
            annonce["surface"] = None
            annonce["price_square_meter"] = None
            annonce["rooms"] = None
            annonce["source_site"] = site.get("source_site")
            annonce["address_details"] = format_address_details(annonce.get("address", ""))
            annonce["address"] = format_address(annonce.get("address", ""))
            

        all_annonces.extend(annonces)

        return annonces
