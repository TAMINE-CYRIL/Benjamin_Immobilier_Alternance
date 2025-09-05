import asyncio
import json
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, JsonCssExtractionStrategy, CacheMode

class ImmoObject(BaseModel):
    title: str = Field(..., description="Titre de l'annonce")
    price: str = Field(..., description="Prix")
    location: str = Field(..., description="Localisation")
    description: str = Field(..., description="Description")
    date: str = Field(..., description="Date de publication")

schema = {
    "name": "Listing",
    "baseSelector": "li.listing-item",  
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "price", "selector": ".price", "type": "text"},
        {"name": "location", "selector": ".location", "type": "text"},
        {"name": "description", "selector": ".description", "type": "text"},
        {"name": "date", "selector": ".date", "type": "text"},
    ]
}

BASE_URL = "https://www.logic-immo.com/vente?page={}" 
TOTAL_PAGES = 3  

async def main():
    browser_config = BrowserConfig(headless=True, verbose=True)
    extraction_strategy = JsonCssExtractionStrategy(schema)

    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        cache_mode=CacheMode.BYPASS
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
