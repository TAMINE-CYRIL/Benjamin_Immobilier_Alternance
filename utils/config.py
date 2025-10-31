from crawl4ai import BrowserConfig


HEADERS= {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
}

def get_browser_config():
    """Retourne une configuration de navigateur standardisée pour les scrapers."""
    browser_config = BrowserConfig(
        browser_type="chromium", 
        headless=False,
        viewport_width=1920,
        viewport_height=1080,
        headers=HEADERS,
        enable_stealth=True
    )
    return browser_config