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


def filtrage_bienici(annonces):
    """
    Calcule la surface quand on n'a que prix et prix/m².
    """
    clean_annonces = []
    for annonce in annonces:
        price = annonce.get("price")
        surface_price = annonce.get("surface")

        if price is not None and surface_price is not None:
            annonce["surface"] = price // surface_price
        else:
            annonce["surface"] = None

        clean_annonces.append(annonce)
    return clean_annonces


sites = [
    {
        "url": "https://www.bienici.com/recherche/achat/france",
        "schema": schema_bienici,
        "wait_for": "css:article.ad-overview",
        "prefix": "https://www.bienici.com",
        "filter": "bienici"
    },
    {
        "url": "https://www.espaces-atypiques.com/ventes/?prj=ventes&pl=&pmax=&critere1=&s=&order=&map=&pt=vente",
        "schema": schema_atypiques,
        "wait_for": "css:.preview-annonce  ",
        "prefix": "https://www.espaces-atypiques.com",
        "filter": "atypiques"
    },
    {
        "url": "https://www.pap.fr/annonce/vente-immobiliere-france-g25",
        "schema": schema_pap,
        "wait_for": "css:.search-list-item-alt",
        "prefix": "https://www.pap.fr",
        "filter": "pap"
    }
]

async def extract_sites():
    """
    Fonction asynchrone permettant de lancer le Web Crawler pour récupérer les données des différents sites à l'aide d'une extraction
    CSS et d'un schéma JSON.
    """
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
                    annonces = json.loads(result.extracted_content)
                    
                    annonces = filter_annonces(annonces)
                    if site["filter"] == "bienici":
                        annonces = filtrage_bienici(annonces)
                    
                    for annonce in annonces:
                        print(f"Titre : {annonce.get('title', 'N/A')}")

                        address = annonce.get('address') or annonce.get('location') or annonce.get('city', 'N/A')
                        postal = annonce.get('postal_code')
                        if postal:
                            address += f" {postal}"
                        print(f"Adresse : {address}")
                        print(f"Surface : {annonce.get('surface')}")
                        print(f"Prix : {annonce.get('price')}")

                                        
                        url_ann = annonce.get('url')
                        if site.get('prefix') and url_ann and not url_ann.startswith("https"):
                            url_ann = site['prefix'] + url_ann
                            print(f"Lien : {url_ann}")
                        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(extract_sites())
