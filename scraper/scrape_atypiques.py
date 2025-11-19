from crawl4ai import AsyncWebCrawler, CacheMode, JsonCssExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig
from utils.cleaning import extract_number
from utils.config import get_browser_config
import asyncio, json, os, random, regex as re



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "../schema/espace_atypique.json"), "r", encoding="utf-8") as f:
    schema_atypiques = json.load(f)

with open(os.path.join(BASE_DIR, "../schema/details/espace_atypique_details.json"), "r", encoding="utf-8") as f:
    schema_detail = json.load(f)


site = {
    "schema": schema_atypiques,
    "wait_for": "css:.preview-annonce",
    "source_site": "Espaces Atypiques",
}

######################################################################


############# Fonctions de filtrage et de normalisation ##############

def calculate_price_square_meter(price: str, surface: str) -> float | None:
    """
    Calcule le prix au mètre carré en divisant le prix par la surface.
    
    Args:
        price (str): Le prix total de l'annonce.
        surface (str): La surface totale en m².

    Returns:
        float | None: Le prix au mètre carré arrondi à 2 décimales, ou None si le calcul n'est pas possible.
    
    """
    if not price or not surface:
        return None
    price = extract_number(price) # On transforme notre prix en nombre
    surface = extract_number(surface) # On transforme notre surface en nombre
    return round(price // surface, 2)


def format_address(address: str):
    """
    Formate l'adresse en capitalisant correctement les mots, en supprimant le code postal et les caractères spéciaux.
    
    Args:
        address (str): L'adresse brute à formater.

    Returns:
        str: L'adresse formatée.
    """
    if not address:
        return address

    address = address.lower().strip()
    lower_words = {"sur", "sous", "les", "des", "du", "de", "la", "le", "l'", "d'", "aux", "au"}

    def format_word(word):
        if "'" in word:
            parts = word.split("'")
            return parts[0].capitalize() + "'" + parts[1].capitalize()
        if "-" in word:
            return "-".join([w.capitalize() if w not in lower_words else w for w in word.split("-")])
        return word.capitalize() if word not in lower_words else word

    return " ".join(format_word(w) for w in re.split(r"\s+", address))


def extract_type_from_title(title: str) -> str | None:
    """
    Extrait le type de bien (appartement, maison, etc.) à partir du titre.
    Pour Espaces Atypiques, le type de bien est souvent dans le titre

    Args:
        title (str): Le titre de l'annonce.
        
    Returns:
        str: Le type de bien extrait ou None s'il n'est pas trouvé.
    """
    types = ["maison", "appartement", "loft", "atelier", "duplex", "villa", "chalet", "terrain"]
    for part in title.split():
        if part.lower() in types:
            return part.capitalize()
    return None



async def scrape_details(crawler, annonce) -> dict | None:
    """
    Scrape une page de détail en parallèle.

    Args:
        crawler (AsyncWebCrawler): L'instance du crawler.
        annonce (dict): L'annonce contenant l'URL à scraper.

    Returns:
        dict: L'annonce mise à jour avec les détails extraits.
    
    """

    url = annonce.get("url")
    if not url:
        return annonce

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for="css:#infos-cles",
        extraction_strategy=JsonCssExtractionStrategy(schema=schema_detail),
    )

    result = await crawler.arun(url=url, config=run_cfg, wait_after_load=0.2)

    if not result or not result.extracted_content:
        return annonce

    details = json.loads(result.extracted_content)

    for d in details:
        if d['label'] == 'Chambres':
            annonce['rooms'] = extract_number(d['value'])

        if d['label'] == details[0]['label']:
            zip_code = ''.join(filter(str.isdigit, d['value']))
            if len(zip_code) == 5:
                annonce['zip_code'] = zip_code

    return annonce



async def scrape_atypiques(max_pages=5):
    
    """
    Scrape plusieurs pages du site Espaces Atypiques avec Crawl4AI et gère la pagination.
    
    Args:
        max_pages (int): Nombre maximum de pages à scraper.

    Returns:
        list: Liste des annonces extraites et formatées.
    """

    browser_config = get_browser_config() # On récupère la config du navigateur

    all_annonces = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):

            url = f"https://www.espaces-atypiques.com/ventes/page/{page}/?prj=ventes"

            run_cfg = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for=site["wait_for"],
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
            )

            result = await crawler.arun(url=url, config=run_cfg, wait_after_load=0.2)

            if not result or not result.extracted_content:
                print("Aucun résultat extrait.")
                continue

            

            annonces = json.loads(result.extracted_content)
            if not annonces:
                print("Aucune annonce trouvée.")
                continue

            detail_tasks = [scrape_details(crawler, a) for a in annonces]
            annonces = await asyncio.gather(*detail_tasks)

            for annonce in annonces:
                annonce["source_site"] = site["source_site"]
                annonce["address"] = format_address(annonce.get("address", ""))
                annonce["price_square_meter"] = calculate_price_square_meter(
                    annonce.get("price"), annonce.get("surface")
                )
                annonce["type_bien"] = extract_type_from_title(annonce.get("title", ""))

            all_annonces.extend(annonces)

            await asyncio.sleep(random.uniform(1, 3))

    return all_annonces
