import argparse
import asyncio
import datetime as dt
import json
import os

from database.db import insert_annonces
from database.score_annonce import score_annonce_payloads
from scrapers.immobilier.scrape_atypiques import scrape_atypiques
from scrapers.immobilier.scrape_avoventes import scrape_avoventes
from scrapers.immobilier.scrape_bienici import scrape_bienici
from scrapers.immobilier.scrape_leboncoin import scrape_leboncoin
from scrapers.immobilier.scrape_logicimmo import scrape_logicimmo
from scrapers.immobilier.scrape_pap import scrape_pap
from scrapers.immobilier.scrape_seloger import scrape_seloger
from utils.cleaning import deduplicate_annonces, normalize_annonces


def parse_args():
    parser = argparse.ArgumentParser(description="Benjamin Immobilier scraping pipeline")
    parser.add_argument("--source", help="Run only one source by name")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Override max pages for paginated scrapers. Defaults to each scraper's own setting.",
    )
    parser.add_argument("--no-db", action="store_true", help="Skip database insert/update")
    parser.add_argument("--no-score", action="store_true", help="Skip scoring step")
    parser.add_argument(
        "--output-json",
        default=os.path.join("data", "annonces.json"),
        help="Write normalized annonces and summary to a JSON file",
    )
    return parser.parse_args()


def _scrape_with_optional_max_pages(scraper, max_pages=None, **kwargs):
    if max_pages is None:
        return scraper(**kwargs)
    return scraper(max_pages=max_pages, **kwargs)


def build_source_registry():
    return [
        {
            "name": "LogicImmo",
            "enabled": True,
            "builder": lambda max_pages: _scrape_with_optional_max_pages(
                scrape_logicimmo,
                max_pages=max_pages,
                use_proxies=False,
            ),
        },
        {
            "name": "SeLoger",
            "enabled": True,
            "builder": lambda max_pages: _scrape_with_optional_max_pages(
                scrape_seloger,
                max_pages=max_pages,
                use_proxies=False,
            ),
        },
        {
            "name": "PAP",
            "enabled": True,
            "builder": lambda max_pages: _scrape_with_optional_max_pages(scrape_pap, max_pages=max_pages),
        },
        {
            "name": "BienIci",
            "enabled": True,
            "builder": lambda max_pages: _scrape_with_optional_max_pages(scrape_bienici, max_pages=max_pages),
        },
        {
            "name": "Leboncoin",
            "enabled": False,
            "builder": lambda max_pages: _scrape_with_optional_max_pages(
                scrape_leboncoin,
                max_pages=max_pages,
                use_proxies=True,
            ),
        },
        {
            "name": "Espaces Atypiques",
            "enabled": True,
            "builder": lambda max_pages: _scrape_with_optional_max_pages(scrape_atypiques, max_pages=max_pages),
        },
        {
            "name": "AvoVentes",
            "enabled": True,
            "builder": lambda max_pages: scrape_avoventes(),
        },
    ]


def create_run_logger():
    """
    Crée une fonction de logging 
    qui écrit dans un fichier de log horodaté.
    """
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join("logs", f"run_{timestamp}.log")
    log_file = open(log_path, "a", encoding="utf-8")

    def logger(message):
        line = f"[{dt.datetime.now().isoformat(timespec='seconds')}] {message}"
        log_file.write(line + "\n")
        log_file.flush()

    return logger, log_path, log_file


def _empty_source_summary(name):
    """
    Initialise un résumé de source avec des compteurs à zéro et un statut "pending".
    """
    return {
        "name": name,
        "status": "pending",
        "scraped_total": 0,
        "normalized_total": 0,
        "valid_scoring": 0,
        "valid_no_scoring": 0,
        "partial": 0,
        "skipped": 0,
        "eligible_for_scoring": 0,
        "not_scored_missing_fields": 0,
        "error": None,
    }


def _compute_run_status(summary):
    if summary["normalized_total"] == 0:
        return "failed"
    db_summary = summary.get("db") or {}
    db_errors = db_summary.get("errors") or 0
    db_written = (db_summary.get("inserted") or 0) + (db_summary.get("updated") or 0)
    if db_errors and db_written == 0:
        return "failed"
    if db_errors:
        return "partial_success"
    if summary["failed_sources"] or summary["scoring"].get("errors"):
        return "partial_success"
    return "success"


async def run_pipeline(args, logger=None):
    """
    Lance la pipeline de scraping,
    normalisation, déduplication, insertion en base et scoring des annonces immobilières.
    """
    start_time = dt.datetime.now()
    registry = build_source_registry()

    if args.source:
        selected_names = {args.source.lower()}
        registry = [source for source in registry if source["name"].lower() in selected_names]
        if not registry:
            raise ValueError(f"Unknown source '{args.source}'")
    else:
        registry = [source for source in registry if source["enabled"]]

    all_annonces = []
    source_summaries = []

    for source in registry:
        source_summary = _empty_source_summary(source["name"])
        source_summaries.append(source_summary)
        if logger:
            logger(f"===== Lancement scraper : {source['name']} =====")

        try:
            raw_annonces = await source["builder"](args.max_pages)
            source_summary["scraped_total"] = len(raw_annonces or [])

            normalized_annonces, normalization_summary = normalize_annonces(raw_annonces or [])
            source_summary["status"] = "success"
            source_summary["normalized_total"] = normalization_summary["total"]
            source_summary["valid_scoring"] = normalization_summary["valid_scoring"]
            source_summary["valid_no_scoring"] = normalization_summary["valid_no_scoring"]
            source_summary["partial"] = normalization_summary["partial"]
            source_summary["skipped"] = normalization_summary["skipped"]
            source_summary["eligible_for_scoring"] = normalization_summary["eligible_for_scoring"]
            source_summary["not_scored_missing_fields"] = normalization_summary["not_scored_missing_fields"]

            for annonce in normalized_annonces:
                annonce["source_site"] = annonce.get("source_site") or source["name"]
            all_annonces.extend(normalized_annonces)
        except Exception as exc:
            source_summary["status"] = "failed"
            source_summary["error"] = str(exc)
            if logger:
                logger(f"[SOURCE ERROR] {source['name']} -> {exc}")

    all_annonces, deduplication_summary = deduplicate_annonces(all_annonces)
    if logger and deduplication_summary["removed"]:
        logger(
            "[DEDUP] {removed} doublon(s) retire(s) avant insertion "
            "({before} -> {after})".format(
                removed=deduplication_summary["removed"],
                before=deduplication_summary["input_total"],
                after=deduplication_summary["output_total"],
            )
        )

    status_counts = {
        "valid_scoring": 0,
        "valid_no_scoring": 0,
        "partial": 0,
        "skipped": 0,
    }
    for annonce in all_annonces:
        status = annonce.get("_validation_status")
        if status in status_counts:
            status_counts[status] += 1

    global_summary = {
        "started_at": start_time.isoformat(timespec="seconds"),
        "completed_at": None,
        "duration_seconds": None,
        "status": "failed",
        "log_path": None,
        "sources": source_summaries,
        "scraped_total": sum(item["scraped_total"] for item in source_summaries),
        "normalized_before_dedup": deduplication_summary["input_total"],
        "normalized_total": len(all_annonces),
        "deduplicated": deduplication_summary["removed"],
        "deduplication": deduplication_summary,
        "inserted": 0,
        "updated": 0,
        "skipped": status_counts["skipped"],
        "eligible_for_scoring": status_counts["valid_scoring"],
        "scored": 0,
        "not_scored": 0,
        "not_scored_missing_fields": (
            status_counts["valid_no_scoring"] + status_counts["partial"] + status_counts["skipped"]
        ),
        "not_scored_no_reference": 0,
        "failed_sources": [item["name"] for item in source_summaries if item["status"] == "failed"],
        "db": {
            "total": len(all_annonces),
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "skip_reasons": {},
            "processed_ids": [],
        },
        "scoring": {
            "eligible_for_scoring": 0,
            "scored": 0,
            "retained": 0,
            "filtered_below_min_score": 0,
            "not_scored_missing_fields": 0,
            "not_scored_no_reference": 0,
            "errors": 0,
        },
    }

    if not args.no_db and all_annonces:
        annonces_to_save = all_annonces
        if not args.no_score:
            annonces_to_save, scoring_summary = score_annonce_payloads(
                all_annonces,
                logger=logger,
            )
            global_summary["scoring"] = scoring_summary
            global_summary["scored"] = scoring_summary["scored"]
            global_summary["not_scored_missing_fields"] += scoring_summary["not_scored_missing_fields"]
            global_summary["not_scored_no_reference"] = scoring_summary["not_scored_no_reference"]
            global_summary["not_scored"] = (
                scoring_summary["not_scored_missing_fields"] + scoring_summary["not_scored_no_reference"]
            )

        db_summary = insert_annonces(annonces_to_save, logger=logger)
        global_summary["db"] = db_summary
        global_summary["inserted"] = db_summary["inserted"]
        global_summary["updated"] = db_summary["updated"]
        global_summary["skipped"] += db_summary["skipped"]

        if args.no_score:
            global_summary["not_scored"] = global_summary["eligible_for_scoring"]
    else:
        global_summary["not_scored"] = global_summary["eligible_for_scoring"]

    end_time = dt.datetime.now()
    global_summary["completed_at"] = end_time.isoformat(timespec="seconds")
    global_summary["duration_seconds"] = round((end_time - start_time).total_seconds(), 2)
    global_summary["status"] = _compute_run_status(global_summary)
    return all_annonces, global_summary


async def main():
    """
    Lance la pipeline de scraping, 
    normalisation, déduplication, 
    insertion en base et scoring des annonces immobilières.
    """
    args = parse_args()
    logger, log_path, log_file = create_run_logger()
    try:
        annonces, summary = await run_pipeline(args, logger=logger)
        summary["log_path"] = log_path

        payload = {
            "summary": summary,
            "annonces": annonces,
        }
        with open(args.output_json, "w", encoding="utf-8") as outfile:
            json.dump(payload, outfile, ensure_ascii=False, indent=2, default=str)
        logger(f"Donnees sauvegardees dans {args.output_json}")

        logger(
            "Run termine - statut: {status}, scraped: {scraped}, normalized: {normalized}, "
            "inserted: {inserted}, updated: {updated}, scored: {scored}, not_scored: {not_scored}".format(
                status=summary["status"],
                scraped=summary["scraped_total"],
                normalized=summary["normalized_total"],
                inserted=summary["inserted"],
                updated=summary["updated"],
                scored=summary["scored"],
                not_scored=summary["not_scored"],
            )
        )
    finally:
        log_file.close()


if __name__ == "__main__":
    asyncio.run(main())
