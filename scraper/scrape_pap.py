from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/pap.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_pap = json.load(f)


def extract_number(text):
    """
    Extrait un nombre entier d'une chaîne de caractères.
    Retourne None si 'N/A' ou pas de chiffre.
    """
    if text is None or text == "N/A":
        return
    digits = ""
    for c in text:
        if c in "0123456789":
            digits += c
    if digits == "":
        return None
    return int(digits)

def normalization(annonces):
    """
    Normalise les champs prix et surface en entiers (ou None).
    """
    clean_annonces = []
    for annonce in annonces:
        annonce["price"] = extract_number(annonce.get("price"))
        annonce["surface"] = extract_number(annonce.get("surface"))
        
        clean_annonces.append(annonce)

    return clean_annonces

def filter_annonces(annonces):
    filtrage = []
    clean_annonces=normalization(annonces)
    for annonce in clean_annonces:
        price = annonce.get("price")
        surface = annonce.get("surface")
        if price is None and surface is None :
            continue
        filtrage.append(annonce)
    return filtrage


# Données du site à scraper sous forme de tableau.
site ={
        "url": "https://www.pap.fr/annonce/vente-immobiliere-france-g25",
        "schema": schema_pap,
        "wait_for": "css:.search-list-item-alt",
        "prefix": "https://www.pap.fr",
        "filter": "pap"
    }

async def scrape_pap():
    """
    Fonction asynchrone permettant de lancer le Web Crawler pour récupérer les données du site PAP à l'aide d'une extraction
    CSS et d'un schéma JSON.
    """
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
                crawler_config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    wait_for=site.get("wait_for"),
                    extraction_strategy=JsonCssExtractionStrategy(
                        schema=site.get("schema")
                        ),
                )
                result = await crawler.arun(url=site.get("url"), config=crawler_config, wait_after_load=10)

                if not result and result.extracted_content:
                    return []
                
                annonces = json.loads(result.extracted_content)

                annonces = filter_annonces(annonces)
                return annonces



