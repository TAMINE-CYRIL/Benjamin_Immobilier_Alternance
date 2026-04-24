from crawl4ai import AsyncWebCrawler, CacheMode, JsonCssExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig
from utils.cleaning import extract_number
from utils.config import get_browser_config
import asyncio, json, os, random, regex as re



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "../../schema/immobilier/espace_atypique.json"), "r", encoding="utf-8") as f:
    schema_atypiques = json.load(f)


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
    price_number = extract_number(price) # On transforme notre prix en nombre
    surface_number = extract_number(surface) # On transforme notre surface en nombre
    if price_number is None or surface_number is None or surface_number == 0:
        return None
    return round(price_number / surface_number, 2)



def format_city(city: str) -> str:
    """
    Formate l'adresse en capitalisant correctement les mots, en supprimant le code postal et les caractères spéciaux.
    
    Args:
        city (str): L'adresse brute à formater.

    Returns:
        str: L'adresse formatée.
    """
    if not city:
        return city

    city = city.lower().strip()
    lower_words = {"sur", "sous", "les", "des", "du", "de", "la", "le", "l'", "d'", "aux", "au"}

    def format_word(word):
        if "'" in word:
            parts = word.split("'")
            return parts[0].capitalize() + "'" + parts[1].capitalize()
        if "-" in word:
            return "-".join([w.capitalize() if w not in lower_words else w for w in word.split("-")])
        return word.capitalize() if word not in lower_words else word

    return " ".join(format_word(w) for w in re.split(r"\s+", city))


def extract_type_from_title(title: str) -> str | None:
    """
    Extrait le type de bien à partir du titre et le normalise
    en 'Maison' ou 'Appartement'.

    Args:
        title (str): Le titre de l'annonce.

    Returns:
        str | None: 'Maison', 'Appartement' ou None si non trouvé.
    """

    TYPE_TO_CATEGORIE = {
    # Maison
    "maison": "Maison",
    "maisons": "Maison",
    "villa": "Maison",
    "chalet": "Maison",
    "mas": "Maison",
    "manoir": "Maison",
    "demeure": "Maison",
    "château": "Maison",
    "chateau": "Maison",   
    "bastide": "Maison",
    "terrain": "Maison",
    "atelier": "Maison",

    # Appartement
    "appartement": "Appartement",
    "loft": "Appartement",
    "duplex": "Appartement",
}


    title_lower = title.lower()

    for type_bien, categorie in TYPE_TO_CATEGORIE.items():
        if re.search(rf"\b{type_bien}\b", title_lower):
            return categorie

    return None

async def scrape_atypiques(max_pages=1) -> list:
    
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

            url = f"https://www.espaces-atypiques.com/ventes/page/{page}/?prj=ventes&pl=447%2C519%2C440&pmax&critere1&s&order&map&pt=vente"
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

            for annonce in annonces:
                annonce["source_site"] = site["source_site"]
                annonce["city"] = format_city(annonce.get("city", ""))
                annonce["price_square_meter"] = calculate_price_square_meter(
                    annonce.get("price"), annonce.get("surface")
                )
                annonce["type_bien"] = extract_type_from_title(annonce.get("title", ""))

            all_annonces.extend(annonces)

            await asyncio.sleep(random.uniform(1, 3))

    return all_annonces
