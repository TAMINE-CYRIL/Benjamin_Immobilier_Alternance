import argparse

from database.score_annonce import score_annonces
from services.enrichment.orchestrator import EnrichmentService


def parse_args():
    parser = argparse.ArgumentParser(description="Enrichit les annonces avec geocodage et cadastre")
    parser.add_argument("--limit", type=int, default=100, help="Nombre maximum d'annonces a traiter")
    parser.add_argument("--refresh-days", type=int, default=30, help="Rafraichir les enrichissements plus anciens")
    return parser.parse_args()


def main():
    args = parse_args()
    service = EnrichmentService(logger=print)
    summary = service.run(limit=args.limit, refresh_days=args.refresh_days)
    rescoring = score_annonces(logger=print)
    print(
        "Enrichissement termine - total: {total}, success: {success}, partial: {partial_success}, "
        "not_found: {not_found}, failed: {failed}, rescored: {rescored}".format(
            **summary,
            rescored=rescoring["scored"],
        )
    )


if __name__ == "__main__":
    main()
