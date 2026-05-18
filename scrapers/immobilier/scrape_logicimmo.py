import json
import os
import asyncio
import random
import re  

from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    JsonCssExtractionStrategy,
    ProxyConfig,
)
from crawl4ai.async_configs import CrawlerRunConfig

from utils.cleaning import extract_number
from utils.config import get_browser_config, get_proxy_strategy


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../../schema/immobilier/logic_immo.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_logicimmo = json.load(f)

site = {
    "schema": schema_logicimmo,
    "wait_for": "div[data-testid='serp-core-classified-card-testid']",
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
    (Pas forcément utile si le type est déjà dans le titre ou le schéma.)
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
                    return parts[idx + 1].lower()
        return None
    except Exception:
        return None


def format_address(address: str):
    """
    Formate l'adresse en capitalisant correctement les mots,
    en supprimant le code postal et les caractères spéciaux.
    """
    if not address:
        return address

    address = address.replace("\u00A0", " ").replace("\u202F", " ")
    address = address.replace("’", "'")
    address = re.sub(r"\(?\b\d{5}\b\)?", " ", address)
    address = re.sub(r"[(),/]", " ", address)
    address = address.lower().strip()
    address = re.sub(r"\s+", " ", address)

    lower_words = {
        "sur", "sous", "les", "des", "du", "de", "la", "le", "l",
        "d", "aux", "au", "et",
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
    """Extrait le code postal (5 chiffres) de l'adresse."""
    if not address:
        return None

    match = re.search(r"\b(\d{5})\b", address)
    return match.group(1) if match else None


def format_url(url: str):
    """
    Nettoie l'URL éventuellement encodée.
    """
    if not url:
        return url
    url = url.replace("https%3A%2F%2F", "https://").replace("%2F", "/")
    return url


def extract_type_from_title(title: str):
    """
    Extrait le type de bien (appartement, maison, etc.) à partir du titre.
    Pour LogicImmo, le type de bien est souvent le premier mot du titre.
    """
    if not title:
        return None
    parts = title.split()
    return parts[0] if parts else None



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



async def scrape_logicimmo(max_pages: int = 10, use_proxies: bool = True):
    """
    Scrape plusieurs pages de LogicImmo avec Crawl4AI et gère la pagination.

    Args:
        max_pages (int): Nombre maximum de pages à scraper.
        use_proxies (bool): Indique si l'on doit utiliser des proxies Webshare.

    Returns:
        list: Liste des annonces extraites et filtrées.
    """
    all_annonces = []

    browser_config = get_browser_config()

    # Proxies Webshare (optionnels)
    proxy_strategy = None
    if use_proxies:
        try:
            proxy_strategy = get_proxy_strategy(raise_if_missing=True)
            proxies = ProxyConfig.from_env() or []
            print(f"{len(proxies)} proxies Webshare trouvés (LogicImmo)")
        except Exception as e:
            print(f"Impossible de charger les proxies pour LogicImmo, on continue sans. Raison : {e}")
            proxy_strategy = None

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):
            url = (
                f"https://www.logic-immo.com/classified-search?"
                f"distributionTypes=Buy"
                f"&estateTypes=House,Apartment"
                f"&locations=AD06FR13,AD06FR84,AD06FR6"
                f"&projectTypes=Resale"
                f"&page={page}"
                f"&order=DateDesc"
            )
            print(f"\n===== LogicImmo – page {page}/{max_pages} : {url} =====")

            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                proxy_rotation_strategy=proxy_strategy,
                wait_for=site["wait_for"],
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
                page_timeout=15000,
                wait_for_timeout=8000,
                delay_before_return_html=0.2,
                only_text=True,
                mean_delay=2.0,
                max_range=1.5,
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

            # Si toujours pas de succès après retries
            if not result or not result.success:
                print(f"Échec du scraping LogicImmo pour la page {page} après {attempts} tentative(s)")
                if result and result.error_message:
                    print(f"Erreur: {result.error_message}")
                break  # on stoppe la pagination si une page bloque vraiment

            if not result.extracted_content:
                print(f"Aucune annonce extraite pour la page {page}")
                break

            try:
                annonces = json.loads(result.extracted_content)
            except json.JSONDecodeError as e:
                print(f"JSON invalide pour la page {page} : {e}")
                break

            if not annonces:
                print(f"Liste d'annonces vide pour la page {page}")
                break

            for annonce in annonces:
                annonce["source_site"] = "LogicImmo"

                annonce["price"] = extract_number(annonce.get("price"))
                annonce["price_square_meter"] = extract_number(annonce.get("price_square_meter"))

                annonce["url"] = format_url(annonce.get("url", ""))

                raw_city = annonce.get("city", "") or annonce.get("address", "")
                formatted_city = format_address(raw_city)
                annonce["zip_code"] = extract_zip_code(raw_city)
                annonce["city"] = formatted_city
                annonce["address"] = formatted_city

                annonce["rooms"] = extract_number(annonce.get("rooms"))
                annonce["type_bien"] = extract_type_from_title(annonce.get("title", ""))

                if not annonce.get("surface") and annonce.get("price") and annonce.get("price_square_meter"):
                    annonce["surface"] = calculate_surface(
                        annonce["price"],
                        annonce["price_square_meter"],
                    )

            all_annonces.extend(annonces)

            # Petite pause entre les pages pour ne pas bourriner
            await asyncio.sleep(random.uniform(1, 3))

    print(f"\nTotal annonces LogicImmo récupérées : {len(all_annonces)}")
    return all_annonces
