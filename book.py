import asyncio
import json
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, JsonCssExtractionStrategy, CacheMode

class Book(BaseModel):
    title: str = Field(..., description="Book title")
    price: str = Field(..., description="Book price")
    stock: str = Field(..., description="Book availability (In stock / Out of stock)")

schema = {
    "name": "Book",
    "baseSelector": "article.product_pod",
    "fields": [
        {"name": "title", "selector": "h3 a", "type": "text"},
        {"name": "price", "selector": "p.price_color", "type": "text"},
        {"name": "stock", "selector": "p.instock.availability", "type": "text"}
    ]
}

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
TOTAL_PAGES = 12

async def main():
    browser_config = BrowserConfig(headless=True, verbose=True)
    extraction_strategy = JsonCssExtractionStrategy(schema)

    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        cache_mode=CacheMode.BYPASS
    )

    all_books = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, TOTAL_PAGES + 1):
            url = BASE_URL.format(page)
            result = await crawler.arun(url=url, config=run_config)

            if result.success and result.extracted_content:
                try:
                    books = json.loads(result.extracted_content)
                    for book in books:
                        try:
                            validated = Book(**book)
                            all_books.append(validated.model_dump())
                        except:
                            continue
                    print(f"[Page {page}] {len(books)} books extracted")
                except Exception as e:
                    print(f"Error parsing JSON on page {page}: {e}")
            else:
                print(f"Error extracting page {page}: {result.error_message}")

    print(f"\nTotal books extracted: {len(all_books)}")
    print(json.dumps(all_books, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
