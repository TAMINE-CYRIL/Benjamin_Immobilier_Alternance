from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json
import os
import regex as re
from utils.cleaning import extract_number



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../../schema/immobilier/pap.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_pap = json.load(f)


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
    except ValueError:
        return None

def is_valid_pap_annonce(annonce):
    """
    Détecte si une annonce PAP est une vraie annonce immobilière.
    Évite les pages éditoriales comme prix m2, actualités, etc.
    """

    url = annonce.get("url", "").lower()

    if "/annonces/" not in url:
        return False

    blacklist_keywords = [
        "/vendeur/", "prix-m2", "/actualite", "/immobilier",
        "/g", "-g25", "/estimation", "conseils"
    ]

    if any(key in url for key in blacklist_keywords):
        return False

    if not annonce.get("price") and not annonce.get("surface"):
        return False

    return True

def parse_pap_tags(tags_raw):
    """
    Gère :
    - liste de tags
    - string compacte type '3 chambres30 m²'
    """

    rooms = None
    surface = None

    if not tags_raw:
        return rooms, surface

    # Si c'est une liste → on la transforme en string
    if isinstance(tags_raw, list):
        text = " ".join(tags_raw)
    else:
        text = tags_raw

    # Nettoyage espaces insécables
    text = text.replace("\xa0", " ").strip().lower()

    # Surface
    match_surface = re.search(r"(\d+)\s*m²", text)
    if match_surface:
        surface = int(match_surface.group(1))

    # Pièces
    match_rooms = re.search(r"(\d+)\s*pièce", text)
    if match_rooms:
        rooms = int(match_rooms.group(1))

    return rooms, surface




site = {
        "url": "https://www.pap.fr/annonce/vente-appartement-bureaux-divers-fonds-de-commerce-garage-parking-immeuble-local-commercial-local-d-activite-maison-mobil-home-multipropriete-peniche-residence-avec-service-surface-a-amenager-terrain-alpes-maritimes-06-g369g376g447-studio",
        "schema": schema_pap,
        "wait_for": "css:.search-list-item-alt",
        "prefix": "https://www.pap.fr",
        "source_site": "PAP"
    }

async def scrape_pap(max_pages=10):
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

            url = site["url"] if page == 1 else f"{site['url']}-{page}"

            run_cfg = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_until="networkidle",
                wait_for=site["wait_for"],
                wait_for_timeout=8000,
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
                scan_full_page=True,
                delay_before_return_html=0.2
            )

            result = await crawler.arun(
                url=url,
                config=run_cfg,
                wait_after_load=0.2
            )

            if not result or not result.extracted_content:
                break

            annonces = json.loads(result.extracted_content)
            if not annonces:
                break

            annonces = [a for a in annonces if is_valid_pap_annonce(a)]

            annonces = format_url(annonces)
            annonces = format_title(annonces)

            # Nettoyage des annonces
            for annonce in annonces:

                raw_city = annonce.get("city", "")
                raw_price = annonce.get("price")
                raw_tags = annonce.get("tags_raw")

                price = extract_number(raw_price)
                rooms, surface = parse_pap_tags(raw_tags)

                annonce["price"] = price
                annonce["rooms"] = rooms
                annonce["surface"] = surface
                annonce["zip_code"] = extract_zip_code(raw_city)
                annonce["city"] = clean_address(raw_city)
                annonce["type_bien"] = extract_type_from_url(annonce.get("url"))
                annonce["price_square_meter"] = calculate_price_square_meter(price, surface)
                annonce["source_site"] = site["source_site"]
                annonce.pop("tags_raw", None)

            all_annonces.extend(annonces)

    return all_annonces






