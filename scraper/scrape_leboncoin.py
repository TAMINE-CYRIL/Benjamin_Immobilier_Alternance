from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig
from utils.config import get_browser_config
import json, os, time, random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../schema/leboncoin.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_leboncoin = json.load(f)

site = {
    "url": "https://www.leboncoin.fr/recherche?category=9&real_estate_type=1,2&sort=time&order=desc",
    "schema": schema_leboncoin,
    "prefix": "leboncoin.fr"
}


async def scrape_leboncoin(max_pages=3):
    """Scrape plusieurs pages de Leboncoin avec Crawl4AI et gère la pagination."""
    browser_config = get_browser_config()
    all_annonces = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):
            url = f"{site['url']}&page={page}"
            
            print(f"Scraping page {page}: {url}")

            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
                # Attendre que le conteneur principal soit chargé
                wait_for="css:div[data-test-id='@ad/search']",
                # Temps d'attente supplémentaire pour le chargement lazy
                page_timeout=90000,
                js_code=[
                    # Scroll pour déclencher le lazy loading
                    "window.scrollTo(0, document.body.scrollHeight);",
                    "await new Promise(r => setTimeout(r, 2000));",
                    "window.scrollTo(0, 0);"
                ]
            )

            try:
                result = await crawler.arun(url=url, config=crawler_config)

                if not result or result.status_code != 200:
                    print(f"❌ Erreur page {page}: status {result.status_code if result else 'None'}")
                    break
                
                annonces = json.loads(result.extracted_content)
                
                if not annonces:
                    print(f"⚠️ Aucune annonce trouvée page {page}")
                    # Ne pas break, peut être normal sur certaines pages
                else:
                    print(f"✅ {len(annonces)} annonces extraites de la page {page}")
                    all_annonces.extend(annonces)
                
            except json.JSONDecodeError as e:
                print(f"❌ Erreur JSON page {page}: {e}")
                print(f"Contenu brut: {result.extracted_content[:500]}")
            except Exception as e:
                print(f"❌ Erreur inattendue page {page}: {e}")
                break
            
            # Pause aléatoire entre les pages
            if page < max_pages:
                wait_time = random.uniform(3, 5)
                print(f"⏳ Pause de {wait_time:.1f}s avant la page suivante...")
                time.sleep(wait_time)

    print(f"\n🎯 Total: {len(all_annonces)} annonces extraites")
    return all_annonces


# Pour tester
if __name__ == "__main__":
    import asyncio
    
    async def test():
        annonces = await scrape_leboncoin(max_pages=2)
        print(f"\nPremière annonce:")
        print(json.dumps(annonces[0] if annonces else {}, indent=2, ensure_ascii=False))
    
    asyncio.run(test())