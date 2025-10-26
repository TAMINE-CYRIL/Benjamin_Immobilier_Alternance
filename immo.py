from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import asyncio, json

async def extract_leboncoin():
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True  
    )

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for='css:[data-test-id="ad"]',  
        extraction_strategy=JsonCssExtractionStrategy(
            schema={
                "name": "Leboncoin Immobilier",
                "baseSelector": "[data-test-id='ad']", 
                "fields": [
                    {
                        "name": "title",
                        "selector": "[data-test-id='adcard-title']",
                        "type": "text",
                    },
                    {
                        "name": "price",
                        "selector": "[data-test-id='price']",
                        "type": "text",
                    },
                    {
                        "name": "location",
                        "selector": "[data-test-id='location']",
                        "type": "text",
                    },
                    {
                        "name": "url",
                        "selector": "a",
                        "type": "attribute",
                        "attribute": "href",
                    },
                    {
                        "name": "image",
                        "selector": "img",
                        "type": "attribute",
                        "attribute": "src",
                    },
                ],
            }
        ),
    )

    url = "https://www.leboncoin.fr/recherche?text=bien+immobilier&locations=Marseille__43.29913187499456_5.386161307537629_10000_5000&kst=r&from=rs"

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawler_config)

        if result and result.extracted_content:
            annonces = json.loads(result.extracted_content)

            for ann in annonces:
                print("\n🏠 Annonce :")
                print(f"Titre : {ann.get('title')}")
                print(f"Prix : {ann.get('price')}")
                print(f"Localisation : {ann.get('location')}")
                print(f"Image : {ann.get('image')}")
                print("-" * 60)

if __name__ == "__main__":
    asyncio.run(extract_leboncoin())
