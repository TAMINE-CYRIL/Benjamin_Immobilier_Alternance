import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai import LLMExtractionStrategy
from pydantic import BaseModel, Field
import json

class CountriesWorld(BaseModel):
    country: str = Field(..., description="Le nom du pays")
    capital: str = Field(..., description="La capitale du pays")
    population: str = Field(..., description="La population du pays")

async def main():
    url = "https://www.scrapethissite.com/pages/simple/"

    browser_config = BrowserConfig(
        verbose=False,
        headless=True,
    )

    run_config = CrawlerRunConfig(
        word_count_threshold=1,
        extraction_strategy=LLMExtractionStrategy(
            llm_config=LLMConfig(provider="ollama/llama2"), 
            schema=CountriesWorld.model_json_schema(),
            extraction_type="schema",
            instruction=(
                "Extraire uniquement les pays présents dans les blocs '.country'. "
                "Retourne une liste JSON d'objets avec 3 champs : "
                "'country', 'capital', 'population'. "
                "Ne rien ajouter d'autre."),
        ),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            result = await crawler.arun(url=url, config=run_config)

            # ⚡ Nettoyage du résultat
            extracted = result.extracted_content
            if not extracted:
                print("Rien n'a été extrait")
                return

            print(json.dumps(extracted, ensure_ascii=False))

        except Exception as e:
            print(f"Erreur pendant le scraping : {e}")

if __name__ == "__main__":
    asyncio.run(main())
