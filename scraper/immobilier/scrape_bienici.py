####################################


############# Imports ##############

import json, os, asyncio, random, re
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from utils.cleaning import extract_number

###########################################################################


############# Ouverture du schéma et informations diverses ##############

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../../schema/immobilier/bienici.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_bienici = json.load(f)

site = {
    "url": "https://www.bienici.com/recherche/achat/bouches-du-rhone-13,alpes-maritimes-06,var-83/maisonvilla,appartement,parking,terrain,loft,commerce,batiment,chateau,local,bureau,hotel,autres",
    "wait_for": "css:article.ad-overview",
    "prefix": "https://www.bienici.com",
}

######################################################################


############# Fonctions de filtrage et de normalisation ##############

def extract_zip_code(address: str) -> str | None:
    """
    Extrait le code postal (5 chiffres) de l'adresse à l'aide de regex.

    Args:
        address (str): L'adresse complète.

    Returns:
        str or None: Le code postal extrait ou None s'il n'est pas trouvé.
    """
    if not address:
        return None
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None


def extract_type_from_url(url: str) -> str | None:
    """
    Extrait le type de bien à partir de l'URL de l'annonce, on compare ensuite à notre liste de patterns.

    Args:
        url (str): L'URL de l'annonce.

    Returns:
        str | None: Le type de bien extrait ou None si non trouvé.
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
    Par exemple : "75002 paris" -> "Paris"
    
    Args:
        address (str): L'adresse brute à formater.

    Returns:
        str: L'adresse formatée.
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

def format_surface(price: float, price_square_meter: float) -> float | None:
    """
    Calcule la surface quand on n’a que le prix et le prix/m².
    
    Args:
        price (float): Le prix total de l'annonce.
        price_square_meter (float): Le prix au mètre carré.

    Returns:
        float | None: La surface arrondie à 2 décimales, ou None si le calcul n'est pas possible.
    """
    if price and price_square_meter:
        surface = round(price // price_square_meter, 2)
    else:
        surface = None

    return surface

def format_url(url: str) -> str:
    """
    Ajoute le préfixe du site aux URLs relatives.
    
    Args:
        url (str): L'URL de l'annonce.

    Returns:
        str: L'URL complète.
    """
    if url and not url.startswith("http"):
        url = site["prefix"] + url
    return url

#################################################


############# Programme principal ###############

async def scrape_bienici(max_pages=10):
    """
    Scrape plusieurs pages de BienIci avec Crawl4AI et filtre les annonces spécifiques à BienIci.
    
    Args:
        max_pages (int): Nombre maximum de pages à scraper. On part avec 10 pages par défaut.

    Returns:
        list: Liste des annonces extraites et nettoyées.
    """
    browser_config = BrowserConfig(browser_type="chromium", headless=True) # Pas besoin de configuration précise pour le moment.

    all_annonces = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Pagination par boucle
        for page in range(1, max_pages + 1):
            url = f"{site['url']}?page={page}"

            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for=site["wait_for"],
                extraction_strategy=JsonCssExtractionStrategy(schema=schema_bienici),
            )

            result = await crawler.arun(url=url, config=crawler_config, wait_after_load=3)

            await asyncio.sleep(random.uniform(2, 4)) # On patiente un peu entre les pages

            # Gestion des erreurs et cas particuliers
            if not result.extracted_content:
                print(f"Aucune annonce extraite pour la page {page}")
                break

            
            if result.status_code == 429:
                print(f"429 Too Many Requests reçu pour la page {page}, arrêt du scraping.")
                break
            
            if result.status_code == 403:
                print(f"403 Forbidden reçu pour la page {page}, arrêt du scraping.")
                break

            annonces = json.loads(result.extracted_content)

            if not annonces:
                print("Aucune annonce trouvée.")
                break 
            
        
            # Nettoyage et formatage des annonces
            for annonce in annonces:
                    url = annonce.get("url")
                    adresse = annonce.get("address", "")
                    annonce["zip_code"] = extract_zip_code(adresse)
                    annonce["source_site"] = "BienIci"
                    annonce["address"] = format_address(adresse)
                    annonce["type_bien"] = extract_type_from_url(url)
                    annonce["url"] = format_url(url)
                    annonce["price"] = extract_number(annonce.get("price"))
                    annonce["price_square_meter"] = extract_number(annonce.get("price_square_meter"))
                    annonce["surface"] = format_surface(annonce.get("price"), annonce.get("price_square_meter"))
            all_annonces.extend(annonces)

    return all_annonces
