import argparse

from services.enrichment.orchestrator import EnrichmentService


def parse_args():
    parser = argparse.ArgumentParser(description="Enrichit les annonces avec cadastre et urbanisme")
    parser.add_argument("--limit", type=int, default=100, help="Nombre maximum d'annonces a traiter")
    parser.add_argument("--refresh-days", type=int, default=30, help="Rafraichir les enrichissements plus anciens")
    return parser.parse_args()


def main():
    args = parse_args()
    service = EnrichmentService(logger=print)
    summary = service.run(limit=args.limit, refresh_days=args.refresh_days)
    print(
        "Enrichissement termine - total: {total}, success: {success}, partial: {partial}, "
        "not_found: {not_found}, failed: {failed}".format(**summary)
    )


if __name__ == "__main__":
    main()
