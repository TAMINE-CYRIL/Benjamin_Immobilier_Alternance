####################################


############# Imports ##############

import json, os, regex as re
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

###########################################################################


############# Ouverture des schémas et informations diverses ##############

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../../schema/immobilier/avoventes.json")

# On ouvre le schéma JSON pour AvoVentes
with open(schema_path, "r", encoding="utf-8") as f:
    schema_avoventes = json.load(f)

site = {
    "wait_for": "css:div.row.mb-4.bg-white",
    "prefix": "https://avoventes.fr",
}

######################################################################


############# Fonctions de filtrage et de normalisation ##############

def extract_zip_code(address: str) -> str | None:
    """
    Extrait le code postal (5 chiffres) de l'adresse à l'aide de regex.
    Par exemple : "123 Rue de la Paix, 75002 Paris" -> "75002"

    Args:
        address (str): L'adresse complète.

    Returns:
        str or None: Le code postal extrait ou None s'il n'est pas trouvé.
    
    """
    if not address:
        return None
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None


def format_price(price: str) -> int | float | None:
    """
    Formate le prix pour en faire un nombre entier ou float.

    Args:
        price (str): Le prix sous forme de chaîne de caractères.

    Returns:
        int, float, or None: Le prix formaté ou None si le prix est invalide.
    
    """

    if not price:
        return None
    
    match = re.search(r"(\d[\d\s.,]*)", price)
    if not match:
        return None

    price = match.group(1)

    price = price.replace("€", "").replace("\u00A0", "").strip()
    price = price.replace(" ", "").replace(",", ".")

    try:
        value = float(price)
        return int(value) if value.is_integer() else value
    except:
        return None


def format_address(address: str) -> str | None:
    """
    Formate l'adresse en supprimant le code postal et en nettoyant les espaces.
    Args:
        address (str): L'adresse complète.

    Returns:
        str: L'adresse formatée.
    
    """
    parts = address.split(',')
    if parts:
        if len(parts) == 2:
            address = parts[0].strip()
            address = re.sub(r'^\s*\d{5}\s*', '', address).strip()
            return address
        else:
            address = parts[1].strip()
            address = re.sub(r'^\s*\d{5}\s*', '', address).strip()
            return address

def format_address_details(address: str) -> str | None:
    """
    Récupère l'élément de l'adresse avant la première virgule comme détails de l'adresse.
    Par exemple : "123 Rue de la Paix, 75002 Paris" -> "123 Rue de la Paix"

    Args:
        address (str): L'adresse complète.

    Returns:
        str | None: Les détails de l'adresse ou None si non disponible.
    
    """
    parts = address.split(',')
    if parts and len(parts) > 2:
        details = parts[0].strip()
        return details
    return None

def format_sale(annonces) -> list:
    """
    Formate les indications sur la vente :
    -> Supprime les labels 'Date de la vente :' et 'Date des visites :'

    Args:
        annonces (list): Liste des annonces extraites.

    Returns:
        list: Liste des annonces avec les dates formatées.
    """
    clean_annonces = []

    for annonce in annonces:
        # Retirer les labels des dates
        if "sale_date" in annonce:
            annonce["sale_date"] = re.sub(r"Date de la vente\s*:\s*", "", annonce["sale_date"], flags=re.I)
        if "visit_date" in annonce:
            annonce["visit_date"] = re.sub(r"Date des visites\s*:\s*", "", annonce["visit_date"], flags=re.I)

        clean_annonces.append(annonce)

    return clean_annonces

#################################################


############# Programme principal ###############

async def scrape_avoventes() -> list:
    """
    Scrape la page principale d'AvoVentes avec Crawl4AI à partir du schéma JSON fourni.
    
    Returns:
        list: Liste des annonces extraites et formatées.
    """
    all_annonces = []

    # Config simple puisque tout fonctionne, pas besoin de proxies.
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for=site["wait_for"],
            extraction_strategy=JsonCssExtractionStrategy(schema=schema_avoventes),
            only_text=True
        )

        result = await crawler.arun(
            url="https://avoventes.fr/recherche/toutes?sort=date&order=asc&display=liste",
            config=crawler_config
        )

        if not result or not result.extracted_content:
            print("Aucun titre extrait.")
            return []
        
        if result.status_code == 429:
            print(f"429 Too Many Requests reçu, arrêt du scraping.")
            return []
            
        if result.status_code == 403:
            print(f"403 Forbidden reçu, arrêt du scraping.")
            return []

        annonces = json.loads(result.extracted_content)

        # On passe sur BeautifulSoup puisque les URLs ne sont pas dans le JSON extrait, et que Crawl4AI ne les récupère pas automatiquement sur le schéma.
        if result.html:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(result.html, 'html.parser')
            blocks = soup.select('div.row.mb-4.bg-white[data-link]')
            
            # Associer les URLs aux annonces extraites
            for i, (annonce, block) in enumerate(zip(annonces, blocks)):
                url = block.get('data-link', '')
                annonces[i]['url'] = url

        

        annonces = format_sale(annonces)
        # On lance nos fonctions de formatage/filtrages pour chaque annonce
        for annonce in annonces:
            annonce["price"] = format_price(annonce.get("price", ""))
            annonce["zip_code"] = extract_zip_code(annonce.get("address", ""))
            annonce["source_site"] = "AvoVentes"
            annonce["address_details"] = format_address_details(annonce.get("address", ""))
            annonce["address"] = format_address(annonce.get("address", ""))
            

        all_annonces.extend(annonces)

    return annonces
