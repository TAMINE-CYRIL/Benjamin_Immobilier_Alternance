####################################


############# Imports ##############

import json
import os
import asyncio
import re
from crawl4ai import AsyncWebCrawler, CacheMode, JsonCssExtractionStrategy, ProxyConfig
from crawl4ai.async_configs import CrawlerRunConfig
from utils.cleaning import extract_number
from utils.config import get_browser_config, get_proxy_strategy


###########################################################################


############# Ouverture des schémas et informations diverses ##############

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../../schema/immobilier/leboncoin.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_leboncoin = json.load(f)

site = {
    "url": "https://www.leboncoin.fr/recherche?category=9&locations=d_6%2Cd_83%2Cd_13&sort=time&order=desc&page=1",
    "schema": schema_leboncoin,
    "wait_for": "css:div[data-qa-id='aditem_container']",
    "prefix": "https://www.leboncoin.fr",
    "source_site": "Leboncoin",
}

######################################################################


############# Fonctions de filtrage et de normalisation ##############

def extract_zip_code(address: str):
    """Extrait le code postal d'une adresse."""
    if not address:
        return None
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None


def format_price(price: str):
    """Nettoie et formate le prix en nombre (fonction pas utilisée pour l'instant)."""
    if not price:
        return None

    price = price.replace("€", "").replace("\u00A0", "").replace(" ", "").strip()
    match = re.search(r"(\d[\d,]*)", price)
    if not match:
        return None

    price = match.group(1).replace(",", "")

    try:
        value = float(price)
        return int(value) if value.is_integer() else value
    except Exception:
        return None


def calculate_price_square_meter(price: str, surface):
    """
    Calcule le prix au m², en divisant le prix total par la surface.
    price et surface peuvent être des strings -> on passe par extract_number.

    Args:
        price (str|float|int): Le prix total.
        surface (str|float|int): La surface en m².

    Returns:
        float|None: Le prix au m² arrondi à 2 décimales,
    """
    if price is None or surface is None:
        return None

    price_val = extract_number(price)
    surface_val = extract_number(surface)

    if not price_val or not surface_val or surface_val == 0:
        return None

    return round(price_val / surface_val, 2)


def extract_property_details(title: str):
    """Extrait type de bien, nombre de pièces et surface à partir du titre."""
    if not title:
        return None, None, None

    # Type de bien
    property_type = None
    if "Maison" in title:
        property_type = "Maison"
    elif "Appartement" in title:
        property_type = "Appartement"
    elif "Terrain" in title:
        property_type = "Terrain"
    else:
        parts = title.split("·")
        if parts:
            property_type = parts[0].strip()

    # Nombre de pièces
    rooms = None
    rooms_match = re.search(r"(\d+)\s*pièce", title, flags=re.IGNORECASE)
    if rooms_match:
        rooms = int(rooms_match.group(1))

    # Surface
    surface = None
    surface_match = re.search(r"(\d+)\s*m[eè]tres carrés", title, flags=re.IGNORECASE)
    if not surface_match:
        surface_match = re.search(r"(\d+)\s*m²", title, flags=re.IGNORECASE)
    if surface_match:
        surface = int(surface_match.group(1))

    return property_type, rooms, surface


def extract_city_from_address(address: str):
    """Extrait la ville (grosso modo) à partir de l'adresse contenant un CP."""
    if not address:
        return None

    address = " ".join(address.split())
    match = re.search(r"\b(\d{5})\b", address)
    if not match:
        return None

    before = address[:match.start()].strip()
    after = address[match.end():].strip()

    if before:
        return before.split()[-1]
    if after:
        return after.split()[0]
    return None


def normalize_leboncoin_location(location: str):
    """Retourne (ville, code postal) depuis une localisation Leboncoin."""
    if not location:
        return None, None

    location = " ".join(str(location).split())
    zip_code = extract_zip_code(location)
    if not zip_code:
        return location or None, None

    city = extract_city_from_address(location)
    return city, zip_code

#################################################


############# Partie dédiée aux proxies ##############

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


#################################################


############# Programme principal ###############


async def scrape_leboncoin(max_pages: int = 10, use_proxies: bool = True):
    """
    Scrape les annonces immobilières Leboncoin.
    - max_pages : nombre de pages à parcourir
    - use_proxies : True = utilise Webshare via get_proxy_strategy
    """
    all_annonces = []

    browser_config = get_browser_config()

    # Gestion proxy : on essaye d'en prendre, sinon on log et on continue sans.
    proxy_strategy = None
    if use_proxies:
        try:
            proxy_strategy = get_proxy_strategy(raise_if_missing=True)
            proxies = ProxyConfig.from_env() or []
            print(f"{len(proxies)} proxies Webshare trouvés")
        except Exception as e:
            print(f"Impossible de charger les proxies, on continue sans. Raison : {e}")
            proxy_strategy = None

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):
            url = site["url"].replace("page=1", f"page={page}")
            print(f"\n===== Page {page}/{max_pages} – {url} =====")

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

            if not result or not result.success:
                print(f"Échec du scraping pour la page {page} après {attempts} tentative(s)")
                if result and result.error_message:
                    print(f"   Erreur: {result.error_message}")
                continue

            if not result.extracted_content:
                print(f"Aucune annonce extraite pour la page {page}")
                continue

            try:
                annonces = json.loads(result.extracted_content)
            except json.JSONDecodeError as e:
                print(f"JSON invalide pour la page {page} : {e}")
                continue

            for annonce in annonces:
                title = annonce.get("title", "")
                if not title:
                    continue

                type_bien, rooms, surface = extract_property_details(title)

                # URL complète
                url_path = annonce.get("url", "")
                if url_path and not url_path.startswith("http"):
                    annonce["url"] = site["prefix"] + url_path

                # Champs enrichis
                annonce["type_bien"] = type_bien
                annonce["rooms"] = rooms
                annonce["surface"] = surface

                raw_price = annonce.get("price", "")
                raw_surface = annonce.get("surface", surface)

                annonce["price"] = extract_number(raw_price)
                annonce["price_square_meter"] = calculate_price_square_meter(
                    raw_price,
                    raw_surface,
                )

                full_address = annonce.get("address") or annonce.get("city", "")
                city, zip_code = normalize_leboncoin_location(full_address)
                annonce["zip_code"] = zip_code
                annonce["city"] = city
                annonce["address"] = full_address or city
                annonce["source_site"] = site["source_site"]

                # Classe énergie : garder juste la lettre A-G si possible
                if annonce.get("energy_class"):
                    match = re.search(r"Classe.*?([A-G])", annonce["energy_class"])
                    annonce["energy_class"] = match.group(1) if match else None

                annonce["title"] = title

            all_annonces.extend(annonces)

    print(f"\nTotal annonces Leboncoin récupérées : {len(all_annonces)}")
    return all_annonces

