from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig
from utils.cleaning import extract_number
from utils.config import get_browser_config
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
    "source_site": "Logic Immo"
}

def calculate_surface(price: float, price_square_meter: float):
    """Calcule la surface quand on n’a que le prix et le prix/m²."""
    if price and price_square_meter:
        surface = round(price // price_square_meter, 2)
    else:
        surface = None

    return surface

def extract_type_bien(url: str):
    """
    Extrait le type de bien (appartement, maison, etc.) à partir de l'URL de l'annonce.
    Fonctionne même si le segment d'URL est 'achat', 'vente' ou 'location'.
    """
    if not url:
        return None

    try:
        parts = url.split('/')
        categories = {"achat", "vente", "location"}
        for cat in categories:
            if cat in parts:
                idx = parts.index(cat)
                if idx + 1 < len(parts):
                    return parts[idx + 1].lower()
        return None
    except Exception:
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

def extract_zip_code(address: str):

    """
    Extrait le code postal (5 chiffres) de l'adresse.
    """
    if not address:
        return None

    match = re.search(r"\b(\d{5})\b", address)
    return match.group(1) if match else None

def format_url(url: str):
    """
    Ajoute le préfixe du site aux URLs relatives.
    """
    url = url.replace("https%3A%2F%2F", "https://").replace("%2F", "/")
    return url


async def scrape_logicimmo(max_pages=3):
    """Scrape plusieurs pages de Logic Immo avec Crawl4AI et gère la pagination."""
    browser_config = get_browser_config()
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
            for annonce in annonces:
                annonce["source_site"] = site.get("source_site")
                annonce["price"] = extract_number(annonce.get("price"))
                annonce["price_square_meter"] = extract_number(annonce.get("price_square_meter"))
                #annonce["surface"] = calculate_surface(annonce.get("price"), annonce.get("price_square_meter"))
                annonce["url"] = format_url(annonce.get("url", ""))
                annonce["zip_code"] = extract_zip_code(annonce.get("address", ""))
                annonce["rooms"] = extract_number(annonce.get("rooms"))
                annonce["address"] = format_address(annonce.get("address", ""))
            all_annonces.extend(annonces)

    return all_annonces
