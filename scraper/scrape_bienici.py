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
    "source_site": "BienIci"
}

def extract_zip_code(address: str):
    """
    Extrait le code postal (5 chiffres) de l'adresse à l'aide de regex.
    """
    if not address:
        return None
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None

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

def format_address(address: str):
    """
    Formate l'adresse en capitalisant correctement les mots, en supprimant le code postal et les caractères spéciaux.
    """
    if not address:
        return address

    address = address.replace("\u00A0", " ").replace("\u202F", " ")

    address = address.replace("’", "'")

    address = re.sub(r"\(?\b\d{5}\b\)?", " ", address)

    address = re.sub(r"[(),/]", " ", address)

    address = address.lower().strip()

    address = re.sub(r"\s+", " ", address)

    lower_words = {"sur", "sous", "les", "des", "du", "de", "la", "le", "l", "d", "aux", "au", "et"}

    def cap_token(token: str):
        if token.isdigit():
            return token

        if "'" in token:
            parts = token.split("'")
            return "'".join(
                p.capitalize() if p and p not in lower_words else p
                for p in parts
            )

        if "-" in token:
            parts = token.split("-")
            return "-".join(
                p.capitalize() if p and p not in lower_words else p
                for p in parts
            )

        return token if token in lower_words else token.capitalize()

    tokens = [cap_token(t) for t in address.split(" ") if t]
    formatted = " ".join(tokens)

    formatted = re.sub(r"\bl'", "L'", formatted)

    return formatted

def format_surface(price: float, price_square_meter: float):
    """Calcule la surface quand on n’a que le prix et le prix/m²."""
    if price and price_square_meter:
        surface = round(price // price_square_meter, 2)
    else:
        surface = None

    return surface

def format_url(url: str):
    """Ajoute le préfixe du site aux URLs relatives."""
    if url and not url.startswith("http"):
        url = site["prefix"] + url
    return url

async def scrape_bienici(max_pages=4):
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

            result = await crawler.arun(url=url, config=crawler_config, wait_after_load=10)

            time.sleep(random.uniform(1, 3))
            if not result or not result.extracted_content:
                print("Aucun résultat extrait.")
                return []  
            annonces = json.loads(result.extracted_content)
            if not annonces:
                print("Aucune annonce trouvée.")
                return []  
        
            for annonce in annonces:
                    url = annonce.get("url")
                    adresse = annonce.get("address", "")
                    annonce["zip_code"] = extract_zip_code(adresse)
                    annonce["source_site"] = site.get("source_site")
                    annonce["address"] = format_address(adresse)
                    annonce["type_bien"] = extract_type_from_url(url)
                    annonce["url"] = format_url(url)
                    annonce["price"] = extract_number(annonce.get("price"))
                    annonce["price_square_meter"] = extract_number(annonce.get("price_square_meter"))
                    annonce["surface"] = format_surface(annonce.get("price"), annonce.get("price_square_meter"))
            all_annonces.extend(annonces)

    return all_annonces
