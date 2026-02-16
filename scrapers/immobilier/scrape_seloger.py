import json, os, random, asyncio, re

from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    JsonCssExtractionStrategy,
    ProxyConfig,
)
from crawl4ai.async_configs import CrawlerRunConfig
from utils.config import get_browser_config, get_proxy_strategy
from utils.cleaning import extract_number

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../../schema/immobilier/seloger.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_seloger = json.load(f)


site = {
    "url": "https://www.seloger.com/classified-search?distributionTypes=Buy,Buy_Auction,Compulsory_Auction&estateTypes=House,Apartment&locations=AD02FR1&page=1&order=DateDesc",
    "schema": schema_seloger,
    "prefix": "https://www.seloger.com",
    "wait_for": "div[data-testid^='classified-card-mfe-']",
    "source_site": "SeLoger",
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
        parts = url.split("/")
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
    Formate l'adresse en capitalisant correctement les mots,
    en supprimant le code postal et les caractères spéciaux.
    """
    if not address:
        return address

    address = address.replace("\u00A0", " ").replace("\u202F", " ")
    address = address.replace("’", "'")

    # Supprimer le code postal
    address = re.sub(r"\(?\b\d{5}\b\)?", " ", address)
    # Supprimer quelques caractères spéciaux
    address = re.sub(r"[(),/]", " ", address)

    address = address.lower().strip()
    address = re.sub(r"\s+", " ", address)

    lower_words = {
        "sur", "sous", "les", "des", "du", "de",
        "la", "le", "l", "d", "aux", "au", "et",
    }

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



async def fetch_with_retries(
    crawler: AsyncWebCrawler,
    url: str,
    config: CrawlerRunConfig,
    retries: int = 2,
    delay: float = 1.0,
):
    """
    Appelle crawler.arun avec une logique de retry simple.
    Retourne (result, nb_tentatives).
    """
    last_result = None

    for attempt in range(1, retries + 2):  # 1 tentative initiale + `retries`
        print(f"    → Tentative {attempt} sur {url}")
        result = await crawler.arun(url=url, config=config)
        last_result = result

        if result.success:
            return result, attempt

        print("Echec:", result.error_message)
        if attempt <= retries:
            await asyncio.sleep(delay)

    return last_result, attempt



async def scrape_seloger(max_pages: int = 2, use_proxies: bool = False):
    """
    Scrape plusieurs pages de SeLoger avec Crawl4AI et gère la pagination.

    Args:
        max_pages (int): Nombre maximum de pages à scraper.
        use_proxies (bool): Indique si l'on doit utiliser des proxies Webshare.
    Returns:
        list: Liste des annonces extraites et filtrées.
    """
    all_annonces = []

    browser_config = get_browser_config() # On récupère la config du navigateur

    proxy_strategy = None
    if use_proxies:
        try:
            proxy_strategy = get_proxy_strategy(raise_if_missing=True)
            proxies = ProxyConfig.from_env() or []
            print(f"{len(proxies)} proxies Webshare trouvés (SeLoger)")
        except Exception as e:
            print(f"Impossible de charger les proxies pour SeLoger, on continue sans. Raison : {e}")
            proxy_strategy = None

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):
            url = (
                f"https://www.seloger.com/classified-search?"
                f"distributionTypes=Buy,Buy_Auction,Compulsory_Auction"
                f"&estateTypes=House,Apartment"
                f"&locations=AD04FR33"
                f"&page={page}"
                f"&order=DateDesc"
            )

            
            print(f"\n===== SeLoger – page {page}/{max_pages} : {url} =====")

            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                proxy_rotation_strategy=proxy_strategy,
                wait_for=site["wait_for"],
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
                delay_before_return_html=3.0,
                scroll_delay=0.5,
                only_text=True,
                exclude_all_images=True,
                exclude_external_images=True,
            )

            result, attempts = await fetch_with_retries(
                crawler,
                url,
                crawler_config,
                retries=2,
                delay=1.0,
            )

            await asyncio.sleep(random.uniform(5, 10)) # On attend un peu entre les pages

            if not result or not result.success:
                print(f"Échec du scraping SeLoger pour la page {page} après {attempts} tentative(s)")
                if result and result.error_message:
                    print(f"Erreur: {result.error_message}")
                break

            if not result.extracted_content:
                print(f"Aucune annonce extraite pour la page {page}")
                break

            if result.status_code == 429:
                print(f"429 Too Many Requests reçu pour la page {page}, arrêt du scraping.")
                break
            
            if result.status_code == 403:
                print(f"403 Forbidden reçu pour la page {page}, arrêt du scraping.")
                break

            try:
                annonces = json.loads(result.extracted_content)
            except json.JSONDecodeError as e:
                print(f"JSON invalide pour la page {page} : {e}")
                break

            if not annonces:
                print(f"Liste d'annonces vide pour la page {page}")
                break

            annonces = filter_url(annonces)

            for annonce in annonces:
                annonce["source_site"] = site.get("source_site")
                annonce["price"] = extract_number(annonce.get("price"))
                annonce["price_square_meter"] = extract_number(annonce.get("price_square_meter"))
                annonce["surface"] = format_surface(
                    annonce.get("price"),
                    annonce.get("price_square_meter"),
                )
                raw_address = annonce.get("address", "")
                annonce["zip_code"] = extract_zip_code(raw_address)
                annonce["address"] = format_address(raw_address)
                annonce["type_bien"] = extract_type_bien(annonce.get("url", ""))

            all_annonces.extend(annonces)

    print(f"\n Total annonces SeLoger récupérées : {len(all_annonces)}")
    return all_annonces
