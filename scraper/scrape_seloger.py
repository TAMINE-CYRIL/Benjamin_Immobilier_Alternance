from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig
from utils.config import get_browser_config
from utils.cleaning import extract_number
import json, os, random, asyncio, regex as re


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/seloger.json")
with open(schema_path, "r", encoding="utf-8") as f:
    schema_seloger = json.load(f)


site = {
    "url": "https://www.seloger.com/classified-search?distributionTypes=Buy,Buy_Auction,Compulsory_Auction&estateTypes=House,Apartment&locations=AD02FR1&page=1&order=DateDesc",
    "schema": schema_seloger,
    "prefix": "https://www.seloger.com",
    "wait_for": "div[data-testid^='classified-card-mfe-']",
    "source_site": "SeLoger"
}

def filter_url(annonces: list):
    """
    On filtre l'URL afin de ne pas avoir des annonces provenant de BellesDemeures.
    Tolère les annonces sans URL.
    """
    filtrage = []
    for annonce in annonces:
        url = annonce.get("url")
        if not url:  
            filtrage.append(annonce)
            continue

        if "www.bellesdemeures.com" in url:
            continue
        filtrage.append(annonce)

    return filtrage



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
                    return parts[idx + 1].capitalize()
        return None
    except Exception:
        return None


def format_surface(price: float, price_square_meter: float):
    """Calcule la surface quand on n’a que le prix et le prix/m²."""
    if price and price_square_meter:
        surface = round(price // price_square_meter, 2)
    else:
        surface = None

    return surface

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

async def scrape_seloger(max_pages=2):
    """
    Fonction asynchrone permettant de lancer le Web Crawler pour récupérer les données du site SeLoger à l'aide d'une extraction
    CSS et d'un schéma JSON.
    """
    browser_config = get_browser_config()
    all_annonces = []
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):
            url = f"https://www.seloger.com/classified-search?distributionTypes=Buy,Buy_Auction,Compulsory_Auction&estateTypes=House,Apartment&locations=AD02FR1&page={page}&order=DateDesc"
            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for=site["wait_for"],
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
                scroll_delay=1
                )

                
            result = await crawler.arun(
                url=url, 
                config=crawler_config, 
                wait_after_load=15
            )



            await asyncio.sleep(random.uniform(1, 3))
            print(result.status_code)
            

            if not result or not result.extracted_content:
                break
        
            annonces = json.loads(result.extracted_content)

            if not annonces:
                break

            annonces = filter_url(annonces)  
            for annonce in annonces:
                annonce["source_site"] = site.get("source_site")
                annonce["price"] = extract_number(annonce.get("price"))
                annonce["price_square_meter"] = extract_number(annonce.get("price_square_meter"))
                annonce["surface"] = format_surface(annonce.get("price"), annonce.get("price_square_meter"))
                annonce["zip_code"] = extract_zip_code(annonce.get("address", ""))
                annonce["address"] = format_address(annonce.get("address", ""))
                annonce["type_bien"] = extract_type_bien(annonce.get("url", ""))
            all_annonces.extend(annonces)
    return all_annonces
