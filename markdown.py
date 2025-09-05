import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
        )
        if result.success:
            print("Page extraite avec succès")
            print(result.markdown)
        else:
            print(f"Erreur pendant le scraping : {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())