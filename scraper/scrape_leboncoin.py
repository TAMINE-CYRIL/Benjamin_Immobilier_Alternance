from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig
from utils.cleaning import extract_number
from utils.config import get_browser_config
import json
import os
import regex as re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/leboncoin.json")



with open(schema_path, "r", encoding="utf-8") as f:
    schema_leboncoin = json.load(f)

site = {
    "url": "https://www.leboncoin.fr/recherche?category=9",
    "schema": schema_leboncoin,
    "wait_for": "css:article[data-test-id='ad']",
    "prefix": "https://www.leboncoin.fr",
    "source_site": "Leboncoin"
}


def extract_zip_code(address: str):
    """Extrait le code postal d'une adresse."""
    if not address:
        return None
    match = re.search(r"\b\d{5}\b", address)
    return match.group(0) if match else None


def format_price(price: str):
    """Nettoie et formate le prix en nombre."""
    if not price:
        return None
    
    # Extraire le montant numérique
    price = price.replace("€", "").replace("\u00A0", "").replace(" ", "").strip()
    match = re.search(r"(\d[\d,]*)", price)
    if not match:
        return None

    price = match.group(1).replace(",", "")

    try:
        value = float(price)
        return int(value) if value.is_integer() else value
    except:
        return None

def calculate_price_square_meter(price, surface):
    """
    Calcule le prix au m², en divisant le prix total par la surface.
    """
    if not price or not surface:
        return None
    price = extract_number(price)
    surface = extract_number(surface)
    price_square_meter = round(price // surface, 2)
    return price_square_meter


def extract_property_details(title: str):
    """Extrait le type de bien, nombre de pièces et surface du titre."""
    if not title:
        return None, None, None
    
    # Extraire le type de bien
    property_type = None
    if "Maison" in title:
        property_type = "Maison"
    elif "Appartement" in title:
        property_type = "Appartement"
    elif "Terrain" in title:
        property_type = "Terrain"
    else:
        # Essayer d'extraire du format "Type · ..."
        parts = title.split("·")
        if len(parts) > 0:
            property_type = parts[0].strip()
    
    # Extraire le nombre de pièces
    rooms = None
    rooms_match = re.search(r"(\d+)\s*pièce", title)
    if rooms_match:
        rooms = int(rooms_match.group(1))
    
    # Extraire la surface
    surface = None
    surface_match = re.search(r"(\d+)\s*m[eè]tres carrés", title)
    if not surface_match:
        surface_match = re.search(r"(\d+)\s*m²", title)
    if surface_match:
        surface = int(surface_match.group(1))
    
    return property_type, rooms, surface


def extract_city_from_address(address: str):
    """Extrait la ville de l'adresse (avant le code postal)."""
    if not address:
        return None
    
    # Nettoyer les retours à la ligne et espaces multiples
    address = " ".join(address.split())
    
    # Format: "L'Aigle 61300"
    parts = address.split()
    if len(parts) >= 2:
        # Prendre tout sauf le dernier élément (code postal)
        city = " ".join(parts[:-1])
        return city if city else None
    return address


async def scrape_leboncoin(max_pages=1):
    """
    Scrape les annonces immobilières de Leboncoin.
    """
    all_annonces = []
    
    browser_config = get_browser_config()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):

            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for=site["wait_for"],
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
                page_timeout=90000,  
                delay_before_return_html=4.0,  
                override_navigator=True,
                simulate_user=True,
                magic=True,  
                mean_delay=2.0,  
                max_range=1.5  
            )

            
            result = await crawler.arun(
                    url=site["url"],
                    config=crawler_config
                )

            if not result or not result.success:
                print(f"Échec du scraping pour la page {page}")
                if result and result.error_message:
                    print(f"Erreur: {result.error_message}")
                continue

            if not result.extracted_content:
                    print(f"Aucune annonce extraite pour la page {page}")
                    continue

            annonces = json.loads(result.extracted_content)

            for annonce in annonces:
                    title = annonce.get("title", "")
                    if not title:
                        continue
                        
                    # Extraire les détails du titre
                    type_bien, rooms, surface = extract_property_details(title)
                    
                    # Formater l'URL complète
                    url_path = annonce.get("url", "")
                    if url_path and not url_path.startswith("http"):
                        annonce["url"] = site["prefix"] + url_path
                    
                    annonce["type_bien"] = type_bien
                    annonce["rooms"] = rooms
                    annonce["surface"] = surface
                    annonce["price"] = extract_number(annonce.get("price", ""))
                    annonce["price_square_meter"] = calculate_price_square_meter(
                        annonce.get("price"), annonce.get("surface")
                    )
                    annonce["zip_code"] = extract_zip_code(annonce.get("address", ""))
                    annonce["address"] = extract_city_from_address(annonce.get("address", ""))
                    annonce["source_site"] = site["source_site"]                    

                    if annonce.get("energy_class"):
                        match = re.search(r"Classe.*?([A-G])", annonce["energy_class"])
                        annonce["energy_class"] = match.group(1) if match else None
                    
                    annonce["title"] = title

            all_annonces.extend(annonces)

    return all_annonces