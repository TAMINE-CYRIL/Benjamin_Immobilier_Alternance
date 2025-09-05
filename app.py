import asyncio
import json
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, JsonCssExtractionStrategy, CacheMode

class ImmoObject(BaseModel):
    title: str = Field(..., description="Titre complet de l'annonce (provenant de l'attribut title du bouton couvrant la carte)")
    price: str = Field(..., description="Prix affiché, ex: '371 000 €'")
    price_per_m2: str = Field(..., description="Prix au mètre carré, ex: '3 092 €/m²'")
    location: str = Field(..., description="Localisation, ex: 'Palais de Justice, Marseille 6ème (13006)'")
    keyfacts: str = Field(..., description="Caractéristiques clés : nb de pièces, chambres, surface, étage, etc.")
    description: str = Field(..., description="Texte descriptif court de l'annonce")
    date: str = Field("", description="Date de publication (si disponible, sinon chaîne vide)")

schema = {
    "name": "Listing",
    "baseSelector": "div[data-testid='serp-core-classified-card-testid']",
    "fields": [
        {"name": "title", "selector": "button[data-testid='card-mfe-covering-link-testid']", "type": "attribute", "attribute": "title"},
        {"name": "price", "selector": "div[data-testid='cardmfe-price-testid']", "type": "text"},
        {"name": "price_per_m2", "selector": "div[data-testid='cardmfe-price-testid'] span", "type": "text"},
        {"name": "location", "selector": "div[data-testid='cardmfe-description-box-address']", "type": "text"},
        {"name": "keyfacts", "selector": "div[data-testid='cardmfe-keyfacts-testid']", "type": "text"},
        {"name": "description", "selector": "div[data-testid='cardmfe-description-testid']", "type": "text"}
    ]
}


BASE_URL = "https://www.logic-immo.com/vente?page={}" 
TOTAL_PAGES = 3  

async def main():
    browser_config = BrowserConfig(headless=True, verbose=True)
    extraction_strategy = JsonCssExtractionStrategy(schema)

    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        cache_mode=CacheMode.BYPASS,
        wait_for="div[data-testid='serp-core-classified-card-testid']"

    )

    all_listings = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, TOTAL_PAGES + 1):
            url = BASE_URL.format(page)
            result = await crawler.arun(url=url, config=run_config)

            if result.success and result.extracted_content:
                try:
                    listings = json.loads(result.extracted_content)
                    for listing in listings:
                        try:
                            validated = ImmoObject(**listing)
                            all_listings.append(validated.model_dump())
                        except:
                            continue
                    print(f"[Page {page}] {len(listings)} annonces extraites")
                except Exception as e:
                    print(f"Erreur parsing JSON page {page}: {e}")
            else:
                print(f"Erreur extraction page {page}: {result.error_message}")

    print(f"\nTotal annonces extraites: {len(all_listings)}")
    print(json.dumps(all_listings, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
