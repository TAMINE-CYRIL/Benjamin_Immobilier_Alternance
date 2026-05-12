import argparse
import asyncio
import datetime as dt
import json
import os
from types import SimpleNamespace

from database.automation_runs import create_run, finish_run
from database.create_tables import create_all_tables
from database.migrations import apply_pending_migrations
from database.reset_db import cleanup
from main_immo import create_run_logger, run_pipeline
from services.enrichment.orchestrator import EnrichmentService


def parse_args():
    parser = argparse.ArgumentParser(description="Orchestrateur Windows Benjamin Immobilier")
    parser.add_argument("--source", help="Limiter le scraping a une source")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Nombre de pages par source. Par defaut, chaque scraper garde sa propre valeur.",
    )
    parser.add_argument("--enrichment-limit", type=int, default=100, help="Nombre d'annonces a enrichir")
    parser.add_argument("--refresh-days", type=int, default=30, help="Rafraichir les enrichissements anciens")
    parser.add_argument("--skip-scraping", action="store_true", help="Ne pas lancer le scraping")
    parser.add_argument("--skip-enrichment", action="store_true", help="Ne pas lancer l'enrichissement")
    parser.add_argument("--skip-cleanup", action="store_true", help="Ne pas nettoyer les annonces anciennes")
    parser.add_argument("--cleanup-days", type=int, default=30, help="Age des annonces a archiver puis supprimer")
    parser.add_argument("--output-json", default=os.path.join("data", "automation", "latest_run.json"))
    return parser.parse_args()


def _status_from_stages(stages):
    if any(stage.get("status") == "failed" for stage in stages.values()):
        return "failed"
    if any(stage.get("status") in {"partial", "partial_success"} for stage in stages.values()):
        return "partial_success"
    return "success"


def _write_summary(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as outfile:
        json.dump(payload, outfile, ensure_ascii=False, indent=2, default=str)


async def run(args=None):
    args = args or parse_args()
    create_all_tables()
    apply_pending_migrations()
    logger, log_path, log_file = create_run_logger()
    run_record = create_run(run_type="full", log_path=log_path)

    started_at = dt.datetime.now()
    summary = {
        "started_at": started_at.isoformat(timespec="seconds"),
        "completed_at": None,
        "status": "running",
        "log_path": log_path,
        "stages": {},
    }

    try:
        logger("===== Lancement automatisation V2 =====")

        if args.skip_scraping:
            summary["stages"]["scraping"] = {"status": "skipped"}
        else:
            pipeline_args = SimpleNamespace(
                source=args.source,
                max_pages=args.max_pages,
                no_db=False,
                no_score=False,
                output_json=None,
            )
            annonces, scraping_summary = await run_pipeline(pipeline_args, logger=logger)
            summary["stages"]["scraping"] = scraping_summary
            summary["stages"]["scraping"]["annonces_in_memory"] = len(annonces)

        if args.skip_enrichment:
            summary["stages"]["enrichment"] = {"status": "skipped"}
        else:
            service = EnrichmentService(logger=logger)
            enrichment_summary = service.run(limit=args.enrichment_limit, refresh_days=args.refresh_days)
            enrichment_status = "success"
            if enrichment_summary.get("failed"):
                enrichment_status = "partial"
            enrichment_summary["status"] = enrichment_status
            summary["stages"]["enrichment"] = enrichment_summary

        if args.skip_cleanup:
            summary["stages"]["cleanup"] = {"status": "skipped"}
        else:
            deleted = cleanup(days=args.cleanup_days, logger=logger)
            summary["stages"]["cleanup"] = {"status": "success", "deleted": deleted, "days": args.cleanup_days}

        completed_at = dt.datetime.now()
        summary["completed_at"] = completed_at.isoformat(timespec="seconds")
        summary["duration_seconds"] = round((completed_at - started_at).total_seconds(), 2)
        summary["status"] = _status_from_stages(summary["stages"])
        finish_run(run_record["id"], summary["status"], summary=summary)
        _write_summary(args.output_json, summary)
        logger(f"Automatisation terminee - statut: {summary['status']}")
        return summary
    except Exception as exc:
        completed_at = dt.datetime.now()
        summary["completed_at"] = completed_at.isoformat(timespec="seconds")
        summary["duration_seconds"] = round((completed_at - started_at).total_seconds(), 2)
        summary["status"] = "failed"
        summary["error_message"] = str(exc)
        finish_run(run_record["id"], "failed", summary=summary, error_message=str(exc))
        _write_summary(args.output_json, summary)
        logger(f"[AUTOMATION ERROR] {exc}")
        raise
    finally:
        log_file.close()


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
