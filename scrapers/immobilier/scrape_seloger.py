import asyncio
import datetime as dt
import json
import os
import random
import re

from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    JsonCssExtractionStrategy,
    ProxyConfig,
)
from crawl4ai.async_configs import CrawlerRunConfig
from utils.cleaning import extract_number
from utils.config import get_browser_config, get_proxy_strategy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
schema_path = os.path.join(BASE_DIR, "../../schema/immobilier/seloger.json")

with open(schema_path, "r", encoding="utf-8") as f:
    schema_seloger = json.load(f)


site = {
    "url": "https://www.seloger.com/classified-search?distributionTypes=Buy,Buy_Auction,Compulsory_Auction&estateTypes=House,Apartment&locations=AD02FR1&page=1&order=DateDesc",
    "schema": schema_seloger,
    "prefix": "https://www.seloger.com",
    "wait_for": "div[data-testid='serp-core-classified-card-testid']",
    "source_site": "SeLoger",
}

DEBUG_DIR = os.path.join(BASE_DIR, "../../logs/seloger_debug")
ANTI_BOT_PATTERNS = [
    r"captcha",
    r"access denied",
    r"forbidden",
    r"verify you are human",
    r"robot",
    r"security check",
    r"challenge",
    r"too many requests",
    r"datadome",
    r"cloudflare",
]


def filter_url(annonces: list):
    """
    On filtre l'URL afin de ne pas avoir des annonces provenant de BellesDemeures.
    Tolere les annonces sans URL.
    """
    filtrage = []
    for annonce in annonces:
        url = annonce.get("url")
        if not url:
            filtrage.append(annonce)
            continue

        if "www.bellesdemeures.com" in url:
            continue

        filtrage.append(annonce)

    return filtrage


def extract_type_bien(url: str):
    """
    Extrait le type de bien (appartement, maison, etc.) a partir de l'URL de l'annonce.
    Fonctionne meme si le segment d'URL est 'achat', 'vente' ou 'location'.
    """
    if not url:
        return None

    try:
        parts = url.split("/")
        categories = {"achat", "vente", "location"}
        for cat in categories:
            if cat in parts:
                idx = parts.index(cat)
                if idx + 1 < len(parts):
                    return parts[idx + 1].capitalize()
        return None
    except Exception:
        return None


def format_surface(price: float, price_square_meter: float):
    """Calcule la surface quand on n'a que le prix et le prix/m2."""
    if price and price_square_meter:
        surface = round(price // price_square_meter, 2)
    else:
        surface = None

    return surface


def format_address(address: str):
    """
    Formate l'adresse en capitalisant correctement les mots,
    en supprimant le code postal et les caracteres speciaux.
    """
    if not address:
        return address

    address = address.replace("\u00A0", " ").replace("\u202F", " ")
    address = address.replace("â€™", "'")

    address = re.sub(r"\(?\b\d{5}\b\)?", " ", address)
    address = re.sub(r"[(),/]", " ", address)

    address = address.lower().strip()
    address = re.sub(r"\s+", " ", address)

    lower_words = {
        "sur", "sous", "les", "des", "du", "de",
        "la", "le", "l", "d", "aux", "au", "et",
    }

    def cap_token(token: str):
        if token.isdigit():
            return token

        if "'" in token:
            parts = token.split("'")
            return "'".join(
                p.capitalize() if p and p not in lower_words else p
                for p in parts
            )

        if "-" in token:
            parts = token.split("-")
            return "-".join(
                p.capitalize() if p and p not in lower_words else p
                for p in parts
            )

        return token if token in lower_words else token.capitalize()

    tokens = [cap_token(t) for t in address.split(" ") if t]
    formatted = " ".join(tokens)
    formatted = re.sub(r"\bl'", "L'", formatted)

    return formatted


def extract_zip_code(address: str):
    """
    Extrait le code postal (5 chiffres) de l'adresse.
    """
    if not address:
        return None

    match = re.search(r"\b(\d{5})\b", address)
    return match.group(1) if match else None


def ensure_seloger_debug_dir() -> str:
    os.makedirs(DEBUG_DIR, exist_ok=True)
    return DEBUG_DIR


def detect_antibot_signals(html: str | None, error_message: str | None = None) -> list[str]:
    haystack = " ".join(part for part in (html or "", error_message or "") if part).lower()
    return [pattern for pattern in ANTI_BOT_PATTERNS if re.search(pattern, haystack)]


def extract_html_excerpt(html: str | None, length: int = 400) -> str:
    if not html:
        return ""
    compact = re.sub(r"\s+", " ", html).strip()
    return compact[:length]


def save_debug_snapshot(page: int, attempt: int, url: str, result, reason: str) -> str | None:
    html = getattr(result, "html", None)
    if not html:
        return None

    ensure_seloger_debug_dir()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"seloger_page{page}_try{attempt}_{reason}_{timestamp}.html"
    path = os.path.abspath(os.path.join(DEBUG_DIR, filename))

    with open(path, "w", encoding="utf-8") as outfile:
        outfile.write(f"<!-- url: {url} -->\n")
        outfile.write(f"<!-- status_code: {getattr(result, 'status_code', None)} -->\n")
        outfile.write(f"<!-- error: {getattr(result, 'error_message', None)} -->\n")
        outfile.write(html)

    return path


def log_result_diagnostics(result, page: int, attempt: int, url: str):
    if not result:
        print(f"[SeLoger][page {page}] Aucun resultat retourne a la tentative {attempt}")
        return

    status_code = getattr(result, "status_code", None)
    html = getattr(result, "html", None)
    error_message = getattr(result, "error_message", None)
    antibot_signals = detect_antibot_signals(html, error_message)

    print(
        f"[SeLoger][page {page}] tentative={attempt} "
        f"success={getattr(result, 'success', None)} status={status_code} "
        f"html_len={len(html) if html else 0} extracted_len={len(getattr(result, 'extracted_content', '') or '')}"
    )

    if antibot_signals:
        print(f"[SeLoger][page {page}] Signaux antibot detectes: {', '.join(antibot_signals)}")

    excerpt = extract_html_excerpt(html)
    if excerpt:
        print(f"[SeLoger][page {page}] Extrait HTML: {excerpt}")


async def fetch_with_retries(
    crawler: AsyncWebCrawler,
    url: str,
    config: CrawlerRunConfig,
    page: int,
    retries: int = 2,
    delay: float = 1.0,
):
    """
    Appelle crawler.arun avec une logique de retry simple.
    Retourne (result, nb_tentatives).
    """
    last_result = None

    for attempt in range(1, retries + 2):
        print(f"    -> Tentative {attempt} sur {url}")
        result = await crawler.arun(url=url, config=config)
        last_result = result
        log_result_diagnostics(result, page, attempt, url)

        if result.success:
            return result, attempt

        print("Echec:", result.error_message)
        snapshot_path = save_debug_snapshot(page, attempt, url, result, reason="fetch_failed")
        if snapshot_path:
            print(f"[SeLoger][page {page}] Snapshot HTML sauvegarde: {snapshot_path}")

        if attempt <= retries:
            await asyncio.sleep(delay)

    return last_result, attempt


async def scrape_seloger(max_pages: int = 10, use_proxies: bool = False):
    """
    Scrape plusieurs pages de SeLoger avec Crawl4AI et gere la pagination.

    Args:
        max_pages (int): Nombre maximum de pages a scraper.
        use_proxies (bool): Indique si l'on doit utiliser des proxies Webshare.
    Returns:
        list: Liste des annonces extraites et filtrees.
    """
    all_annonces = []

    browser_config = get_browser_config()

    proxy_strategy = None
    if use_proxies:
        try:
            proxy_strategy = get_proxy_strategy(raise_if_missing=True)
            proxies = ProxyConfig.from_env() or []
            print(f"{len(proxies)} proxies Webshare trouves (SeLoger)")
        except Exception as e:
            print(f"Impossible de charger les proxies pour SeLoger, on continue sans. Raison : {e}")
            proxy_strategy = None

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for page in range(1, max_pages + 1):
            url = (
                f"https://www.seloger.com/classified-search?"
                f"distributionTypes=Buy,Buy_Auction,Compulsory_Auction"
                f"&estateTypes=House,Apartment"
                f"&locations=AD04FR33"
                f"&page={page}"
                f"&order=DateDesc"
            )

            print(f"\n===== SeLoger - page {page}/{max_pages} : {url} =====")

            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                proxy_rotation_strategy=proxy_strategy,
                wait_for=site["wait_for"],
                wait_for_timeout=15000,
                page_timeout=30000,
                extraction_strategy=JsonCssExtractionStrategy(schema=site["schema"]),
                delay_before_return_html=1.0,
                scroll_delay=0.5,
                only_text=True,
                exclude_all_images=True,
                exclude_external_images=True,
            )

            result, attempts = await fetch_with_retries(
                crawler,
                url,
                crawler_config,
                page=page,
                retries=2,
                delay=1.0,
            )

            await asyncio.sleep(random.uniform(5, 10))

            if not result or not result.success:
                print(f"Echec du scraping SeLoger pour la page {page} apres {attempts} tentative(s)")
                if result and result.error_message:
                    print(f"Erreur: {result.error_message}")
                if result:
                    snapshot_path = save_debug_snapshot(page, attempts, url, result, reason="page_failed")
                    if snapshot_path:
                        print(f"[SeLoger][page {page}] Dernier snapshot HTML: {snapshot_path}")
                break

            if not result.extracted_content:
                print(f"Aucune annonce extraite pour la page {page}")
                snapshot_path = save_debug_snapshot(page, attempts, url, result, reason="empty_extraction")
                if snapshot_path:
                    print(f"[SeLoger][page {page}] Snapshot HTML sans extraction: {snapshot_path}")
                break

            if result.status_code == 429:
                print(f"429 Too Many Requests recu pour la page {page}, arret du scraping.")
                break

            if result.status_code == 403:
                print(f"403 Forbidden recu pour la page {page}, arret du scraping.")
                break

            try:
                annonces = json.loads(result.extracted_content)
            except json.JSONDecodeError as e:
                print(f"JSON invalide pour la page {page} : {e}")
                snapshot_path = save_debug_snapshot(page, attempts, url, result, reason="json_error")
                if snapshot_path:
                    print(f"[SeLoger][page {page}] Snapshot HTML JSON invalide: {snapshot_path}")
                break

            if not annonces:
                print(f"Liste d'annonces vide pour la page {page}")
                snapshot_path = save_debug_snapshot(page, attempts, url, result, reason="empty_annonces")
                if snapshot_path:
                    print(f"[SeLoger][page {page}] Snapshot HTML liste vide: {snapshot_path}")
                break

            annonces = filter_url(annonces)

            for annonce in annonces:
                annonce["source_site"] = site.get("source_site")
                annonce["price"] = extract_number(annonce.get("price"))
                annonce["price_square_meter"] = extract_number(annonce.get("price_square_meter"))
                annonce["surface"] = format_surface(
                    annonce.get("price"),
                    annonce.get("price_square_meter"),
                )
                raw_city = annonce.get("city", "")
                formatted_city = format_address(raw_city)
                annonce["zip_code"] = extract_zip_code(raw_city)
                annonce["city"] = formatted_city
                annonce["address"] = formatted_city
                annonce["type_bien"] = extract_type_bien(annonce.get("url", ""))

            all_annonces.extend(annonces)

    print(f"\n Total annonces SeLoger recuperees : {len(all_annonces)}")
    return all_annonces
