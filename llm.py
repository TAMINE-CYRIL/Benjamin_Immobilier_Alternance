import json
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlResult, CrawlerRunConfig, LLMConfig, LLMExtractionStrategy
import asyncio
from pydantic import BaseModel, Field


class GameProduct(BaseModel):
    title: str = Field(..., description="Full product name, e.g., 'The Legend of Zelda: Ocarina of Time'")
    category: List[str] = Field(..., description="List of product category, e.g., 'Action Adventure', 'Fantasy'")
    summary: str = Field(..., description="Product description, e.g., 'As a young boy, Link is tricked by Ganondorf, the King of the Gerudo Thieves. The evil human uses Link to gain access to the Sacred Realm, where he places his tainted hands on Triforce and transforms the beautiful Hyrulean landscape into a barren wasteland. Link is determined to fix the problems he helped to create, so with the help of Rauru he travels through time gathering the powers of the Seven Sages.''")
    price: str = Field(..., description="Current displayed price with currency, e.g., '91,99 €'")
    in_stock: str = Field(..., description="Stock availability, either 'In Stock' or 'Out of Stock'")
    url: str = Field(..., description="Product URL")


llm_config = LLMConfig(provider="ollama/llama3")


browser_config = BrowserConfig(
    headless=False,
    verbose=False
)

BASE_URL = "https://sandbox.oxylabs.io/products"

async def main():

    schema = GameProduct.model_json_schema()

    extractionStrategy = LLMExtractionStrategy(
        llm_config=LLMConfig(provider="ollama/llama3"),
        instruction = (
            "Extract **all products** from the provided text. "
            "Each product must be represented as one object in the schema. "
            "Return an array of objects strictly following the schema fields: "
            "title, category, summary, price, in_stock, url. "
            "Do not skip any products. "
            "If a field is missing, leave it as an empty string. "
            "Never merge multiple products into one object. "
            "Ensure that each product title appears only once in the final output. "
            "If the same title appears multiple times, keep the most complete entry and discard duplicates."
        ),
        extraction_type="schema",
        schema=schema,
        verbose=True
    )

    config = CrawlerRunConfig(
        extraction_strategy=extractionStrategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results : List[CrawlResult] = await crawler.arun(
            url=BASE_URL,
            config=config
        )

        for result in results:
            if result.success:
                print("Extraction réussie :")
                data = json.loads(result.extracted_content) 
                print(json.dumps(data, indent=4, ensure_ascii=False))
            else:
                print("Erreur pendant le scraping")

if __name__ == "__main__":
    asyncio.run(main())