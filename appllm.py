from crawl4ai import AsyncWebCrawler, CacheMode, LLMExtractionStrategy, LLMConfig
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import asyncio, json
from pydantic import BaseModel, Field



class ImmoObject(BaseModel):
    title: str = Field("", description="The headline or main title of the property")
    price: str = Field("", description="The listed price")
    address: str = Field("", description="Street or city information describing the property location")
    postal_code: str = Field("", description="Postal or ZIP code of the property")
    surface: str = Field("", description="Surface area of the property")
    url: str = Field("", description="URL of the property ad")


def filter_annonces(annonces):
    clean_annonces = []
    for annonce in annonces:
        #annonce["price"]= normalize_price(annonce.get("price"))
        #annonce["surface"]= normalize_surface(annonce.get("surface"))
        annonce.pop("error", None)
        values = list(annonce.values())
        na_count = values.count("N/A")
        empty_count = values.count("")
        if (na_count + empty_count) > 2:
            continue
        clean_annonces.append(annonce)
    return clean_annonces

def normalize_price(annonces):
    return

def normalize_surface(annonces):
    return


async def extract_sites():
    promptInstruction = """
    You are a real estate data extractor.
Extract ALL possible property ads visible in the webpage content.
Return them as a JSON array.

Each ad must contain:
- title 
- price 
- address 
- postal_code
- surface 
- url 

Rules:
- If a field is missing, set it to None.
- Output only JSON, no explanations.
"""



    browser_config = BrowserConfig(browser_type="chromium", headless=False)

    llm_strategy = LLMExtractionStrategy(
        schema=ImmoObject.model_json_schema(),
        llm_config=LLMConfig(provider="ollama/llama3"),
        chunk_token_threshold=500,
        instruction=promptInstruction,
    )

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=llm_strategy,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # urls = [f"https://www.espaces-atypiques.com/ventes/page/{i}" for i in range(1, 3)]
        #for url in urls:
            result = await crawler.arun(
                url="https://www.espaces-atypiques.com/ventes/page/1",
                config=crawler_config,
                wait_for_selector=".preview-annonce",
                extract_from_selector=".list-annonces",
                wait_after_load=10 
            )

            if result and result.extracted_content:
                annonces = json.loads(result.extracted_content)
                annonces_clean = filter_annonces(annonces)
                print(json.dumps(annonces_clean, indent=4, ensure_ascii=False))
            else:
                print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(extract_sites())
