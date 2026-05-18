# config.py
from __future__ import annotations

import random
from typing import Optional

from crawl4ai import BrowserConfig, ProxyConfig, RoundRobinProxyStrategy
from dotenv import load_dotenv

# Charge .env une fois à l'import
load_dotenv()


# Ici je ne garde que des UA "desktop" pour rester cohérent
# avec les headers.
DESKTOP_USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",

    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",

    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",

    # Un peu d'Opera / Brave pour la variété
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/105.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Brave/131.0.0.0",
]

# Tu peux garder une liste MOBILE à part si tu veux faire du mobile plus tard
MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
]


def get_random_user_agent(mobile: bool = False) -> str:
    """
    Retourne un User-Agent réaliste randomisé.
    Si mobile=True, retourne un UA mobile, sinon desktop.
    """
    pool = MOBILE_USER_AGENTS if mobile else DESKTOP_USER_AGENTS
    return random.choice(pool)



def get_proxy_strategy(raise_if_missing: bool = True) -> Optional[RoundRobinProxyStrategy]:
    """
    Récupère la stratégie de rotation basée sur la variable d'env PROXIES.

    - Si raise_if_missing=True : lève une erreur si aucun proxy trouvé.
    - Sinon : renvoie None si pas de proxy.
    """
    # PROXIES est le nom par défaut, donc l'argument n'est pas obligatoire.
    proxies = ProxyConfig.from_env()

    if not proxies:
        if raise_if_missing:
            raise RuntimeError("Aucun proxy trouvé dans PROXIES")
        return None

    return RoundRobinProxyStrategy(proxies)



# Viewports typiques desktop / mobile
DESKTOP_VIEWPORTS = [
    (1920, 1080),
    (1366, 768),
    (1536, 864),
    (1440, 900),
]

MOBILE_VIEWPORTS = [
    (414, 896),   # iPhone 11/12/13
    (390, 844),   # iPhone 12/13/14
    (412, 915),   # Android grands écrans
]


def get_browser_config(*, mobile: bool = False) -> BrowserConfig:
    """
    Configuration du navigateur, avec randomisation légère
    (UA + viewport) et quelques options anti-détection.
    
    """
    if mobile:
        width, height = random.choice(MOBILE_VIEWPORTS)
    else:
        width, height = random.choice(DESKTOP_VIEWPORTS)

    ua = get_random_user_agent(mobile=mobile)

    headers = {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    return BrowserConfig(
        browser_type="chromium",
        headless=True,
        viewport_width=width,
        viewport_height=height,
        user_agent=ua,
        java_script_enabled=True,
        accept_downloads=False,
        ignore_https_errors=False,  
        extra_args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-first-run",
            "--safebrowsing-disable-auto-update",
            "--password-store=basic",
            "--use-mock-keychain",
            "--enable-features=NetworkService,NetworkServiceInProcess",
            "--use-gl=swiftshader",
        ],
        headers=headers,
        storage_state=None,
    )

if __name__ == "__main__":
    # Petit self-test des proxies avec httpbin.org/ip
    import asyncio
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

    async def test_proxies(n_requests: int = 5):
        strategy = get_proxy_strategy(raise_if_missing=True)
        browser_config = get_browser_config()
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            proxy_rotation_strategy=strategy,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            for i in range(1, n_requests + 1):
                result = await crawler.arun(
                    url="https://httpbin.org/ip",
                    config=run_config,
                )
                print(f"\n--- Requête {i} ---")
                if result.success:
                    print(result.markdown.strip())
                else:
                    print("Echec:", result.error_message)

    asyncio.run(test_proxies())
