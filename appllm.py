from crawl4ai import AsyncWebCrawler, CacheMode, LLMExtractionStrategy, LLMConfig
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from pydantic import BaseModel, Field
from utils.cleaning import filter_annonces
import asyncio, json, os



class ImmoObject(BaseModel):
    title: str = Field("", description="The headline or main title of the property")
    url: str = Field("", description="URL of the property ad")
    address: str = Field("", description="Street or city information describing the property location")
    price: str = Field("", description="The listed price")
    surface: str = Field("", description="Surface area of the property")
   


async def extract_sites():
    promptInstruction = """
Extract ALL possible property ads visible in the webpage content.
Return them as a JSON array.

Each ad must contain:
- title 
- url 
- address 
- surface 
- price 

Rules:
- If a field is missing, set it to None.
- Output only JSON, no explanations.
"""



    browser_config = BrowserConfig(
        browser_type="chromium", 
        headless=False,
        enable_stealth=True

    )

    llm_strategy = LLMExtractionStrategy(
        schema=ImmoObject.model_json_schema(),
        llm_config=LLMConfig(provider="ollama/llama3"),
        chunk_token_threshold=500,
        instruction=promptInstruction,
    )

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=llm_strategy,
        #check_robots_txt=True,
    )

    urls = ["https://www.espaces-atypiques.com/ventes/page/1", "https://www.pap.fr/annonce/vente-immobiliere-france-g25", "https://www.seloger.com/classified-search?distributionTypes=Buy,Buy_Auction,Compulsory_Auction&estateTypes=House,Apartment&locations=AD02FR1&page=1", "https://www.bienici.com/recherche/achat/france"]

    async with AsyncWebCrawler(config=browser_config) as crawler:
        #urls = [f"https://www.espaces-atypiques.com/ventes/page/{i}" for i in range(1, 3)]
        #for url in urls:
            result = await crawler.arun(
                url=urls[2],
                config=crawler_config,
                wait_after_load=10 
            )

            if result and result.extracted_content:
                annonces = json.loads(result.extracted_content)
                annonces_clean = filter_annonces(annonces)
            
            else:
                print("Error:", result.error_message)
            

    f = os.path.join("data", "annoncesLLM.json")
    with open(f, "w", encoding="utf-8") as outfile:
        json.dump(annonces_clean, outfile, ensure_ascii=False, indent=4)
    print(f"Données sauvegardées dans {f}") 

if __name__ == "__main__":
    asyncio.run(extract_sites())
