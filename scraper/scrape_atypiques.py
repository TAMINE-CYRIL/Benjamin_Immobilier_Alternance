from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from utils.cleaning import extract_number
import json, os, time, random, regex as re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/espace_atypique.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_atypiques = json.load(f)

detail_schema_path = os.path.join(BASE_DIR, "../schema/details/espace_atypique_details.json")

with open(detail_schema_path, "r", encoding="utf-8") as f:
    schema_detail = json.load(f)


site = {
    "url": "https://www.espaces-atypiques.com/ventes/page/1/?prj=ventes&pl&pmax&critere1&s&order&map&pt=vente",
    "schema": schema_atypiques,
    "wait_for": "css:.preview-annonce",
    "prefix": "https://www.espaces-atypiques.com",
    "source": "Espaces Atypiques"
}

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

def format_address(address: str):
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

    formatted = " ".join(format_word(w) for w in re.split(r"\s+", address))

    return formatted


async def scrape_details(crawler, url, schema):
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for="css:#infos-cles",
        extraction_strategy=JsonCssExtractionStrategy(schema=schema),
    )

    result = await crawler.arun(url=url, config=config, wait_after_load=5)

    if result and result.extracted_content:
        return json.loads(result.extracted_content)

    return {}



async def scrape_atypiques(max_pages=3):
    """
    Scrape plusieurs pages du site Espaces Atypiques à l’aide de Crawl4AI et du schéma JSON.
    """
    browser_config = BrowserConfig(browser_type="chromium", headless=True)
    all_annonces = []
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):
            site["url"] = f"https://www.espaces-atypiques.com/ventes/page/{page}/?prj=ventes&pl&pmax&critere1&s&order&map&pt=vente"
            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for=site["wait_for"],
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
            )

            result = await crawler.arun(url=site["url"], config=crawler_config, wait_after_load=10)
            
            time.sleep(random.uniform(1, 3))
            
            if not result or not result.extracted_content:
                print("Aucun résultat extrait.")
                return []  

            annonces = json.loads(result.extracted_content)
            if not annonces:
                print("Aucune annonce trouvée.")
                return []  
            

            annonces = json.loads(result.extracted_content)

            for annonce in annonces:
                url = annonce.get("url")
                details = await scrape_details(crawler, url, schema_detail)                
                for detail in details:
                    if detail['label'] == 'Chambres':
                        annonce['rooms'] = detail['value']
                    elif detail['label'] == details[0]['label']: 
                        zip_code = ''.join(filter(str.isdigit, detail['value']))
                        if len(zip_code) == 5:
                            annonce['zip_code'] = zip_code
                annonce["source"] = site.get("source")
                annonce["address"] = format_address(annonce.get("address", ""))
                annonce["price_square_meter"] = calculate_price_square_meter(annonce.get("price"), annonce.get("surface"))                        
                time.sleep(random.uniform(1,3))
            all_annonces.extend(annonces)

    return all_annonces
