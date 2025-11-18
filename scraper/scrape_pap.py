from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json, os, asyncio, random, regex as re
from utils.cleaning import extract_number



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/pap.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_pap = json.load(f)

def extract_type_from_url(url: str):
    """
    Extrait le type de bien à partir de l'URL de l'annonce.
    """
    if not url:
        return None

    patterns = {
        "maison": "Maison",
        "appartement": "Appartement",
        "programme": "Programme neuf",
        "parking": "Parking",
        "terrain": "Terrain",
        "loft": "Loft",
        "commerce": "Commerce",
        "bureau": "Bureau",
        "chateau": "Château",
        "hotel": "Hôtel",
        "local": "Local commercial",
        "autres": "Autre bien"
    }

    for key, value in patterns.items():
        if f"/{key}/" in url.lower():
            return value

    return None

def format_url(annonces: list):
    """
    Ajoute le préfixe du site aux URLs relatives.
    """
    filtrage = []
    for annonce in annonces:
        url = annonce.get("url")
        if url and not url.startswith("http"):
            annonce["url"] = site.get("prefix") + url
        filtrage.append(annonce)
    return filtrage

def format_title(annonces: list):
    """
    Formate le titre des annonces en fonction de l'URL.
    Ajoute "Vente" suivi du type de bien et de la localisation extraite de l'URL.
    On évite également les publicités provenant d'ImmoNeuf.
    """
    filtrage = []
    for annonce in annonces:  
        title = annonce.get("title") 
        url = annonce.get("url")

        if "www.immoneuf.com" in url:
            continue
        if url:
            url_clean = url.replace("/annonces/", "-").split("-")
            annonce["title"] = "Vente " + url_clean[1] + " "+ title
        filtrage.append(annonce)
    return filtrage

def extract_zip_code(address: str):
    """
    Extrait le code postal (5 chiffres) de l'adresse.
    """
    if not address:
        return None

    match = re.search(r"\b(\d{5})\b", address)
    return match.group(1) if match else None

def clean_address(address: str):
    """
    Supprime le code postal (5 chiffres) de l'adresse.
    """
    if not address:
        return address

    cleaned = re.sub(r"\s*\(?\b\d{5}\b\)?", "", address).strip()
    return cleaned

def extract_type_from_url(url: str):
    """
    Extrait le type de bien depuis l'URL
    """
    if not url:
        return None
    
    url_clean = url.replace("/annonces/", "-").split("-")
    # le type se trouve après 'vente' ou au début selon PAP
    for item in url_clean:
        if item.lower() in ["maison", "appartement", "garage", "parking", "terrain", "immeuble", "local", "peniche"]:
            return item.capitalize()
    return None


def calculate_price_square_meter(price: float, surface: float):
    """
    Calcule le prix au mètre carré.
    """
    if not price or not surface:
        return None
    try:
        if surface == 0:
            return None
        price_per_sqm = price / surface
        return int(price_per_sqm) if price_per_sqm.is_integer() else round(price_per_sqm, 2)
    except:
        return None

site = {
        "url": "https://www.pap.fr/annonce/vente-appartement-bureaux-divers-fonds-de-commerce-garage-parking-immeuble-local-commercial-local-d-activite-maison-mobil-home-multipropriete-peniche-residence-avec-service-surface-a-amenager-terrain-viager-france-g25",
        "schema": schema_pap,
        "wait_for": "css:.search-list-item-alt",
        "prefix": "https://www.pap.fr",
        "source_site": "PAP"
    }

async def scrape_pap(max_pages=20):
    """
    Scrape les annonces de PAP jusqu'à max_pages.
    Retourne une liste d'annonces formatées.
    """

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        text_mode=False,
        java_script_enabled=True
    )

    all_annonces = []

    async with AsyncWebCrawler(config=browser_config) as crawler:

        for page in range(1, max_pages + 1):

            if page == 1:
                url = site["url"]
            else:
                url = f"{site['url']}-{page}"

            run_cfg = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_until="domcontentloaded",
                wait_for=site["wait_for"],
                wait_for_timeout=8000,

                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),

                scan_full_page=False,     
                scroll_delay=0.1,
                max_scroll_steps=None,

                delay_before_return_html=0.1
            )

            result = await crawler.arun(
                url=url,
                config=run_cfg,
                wait_after_load=0.1
            )

            if not result or not result.extracted_content:
                break

            annonces = json.loads(result.extracted_content)
            if not annonces:
                break

            annonces = format_url(annonces)
            annonces = format_title(annonces)

            for annonce in annonces:
                adresse = annonce.get("address", "")
                price = extract_number(annonce.get("price"))
                surface = extract_number(annonce.get("surface"))

                annonce["zip_code"] = extract_zip_code(adresse)
                annonce["source_site"] = site["source_site"]
                annonce["address"] = clean_address(adresse)
                annonce["type_bien"] = extract_type_from_url(annonce["url"])
                annonce["price_square_meter"] = calculate_price_square_meter(price, surface)

            all_annonces.extend(annonces)
    return all_annonces




