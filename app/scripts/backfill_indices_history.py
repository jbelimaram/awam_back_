"""
Télécharge l'historique Sentinel-2 des parcelles sur plusieurs années, en
ligne de commande. Pour les parcelles déjà existantes, ou pour relancer à
la main ; une parcelle NOUVELLE reçoit son historique automatiquement, en
tâche de fond (app/tasks/history_tasks.py).

Les règles sont celles de app/services/history_service.py, partagées avec
la tâche Celery : une image par date, 60 % de parcelle dégagée, rien avant
la plantation, dates déjà en base ignorées, valeurs seules sans image
cartographique, relances en cas de coupure réseau.

Usage, depuis la racine du backend :

    python -m app.scripts.backfill_indices_history --parcel-id 20 --dry-run
    python -m app.scripts.backfill_indices_history --parcel-id 20
    python -m app.scripts.backfill_indices_history --farm "Makthar" --farm "Sidi Mechreg"

⚠️  Ne pas lancer entre 5 h et 7 h, ni pendant que le worker historique
    traite la même parcelle (aucun doublon possible, mais travail en double).
⚠️  Durée : environ 12 secondes par date retenue. Pour une parcelle sur
    trois ans, compter 30 à 60 minutes.
"""

import argparse
import logging
import os
import sys
import time
from collections import defaultdict

from pystac_client import Client
from sqlalchemy import text

from app.db.database import SessionLocal
from app.services import history_service as hs
from app.services.sentinel_service import STAC_API_URL

logging.basicConfig(level=logging.WARNING, format="%(message)s")


def _select_parcels(db, parcel_id: int | None, farms: list[str]) -> list:
    """Parcelles à traiter : une seule, celles de certaines fermes, ou toutes les actives."""
    query = """
        SELECT p.id, p.name, f.name AS farm
        FROM parcel p JOIN farm f ON f.id = p.farm_id
        WHERE p.geom IS NOT NULL
    """
    params: dict = {}
    if parcel_id is not None:
        query += " AND p.id = :pid"
        params["pid"] = parcel_id
    else:
        query += " AND p.status = 'active'"
        if farms:
            query += " AND f.name = ANY(:farms)"
            params["farms"] = farms
    query += " ORDER BY f.name, p.name"
    return db.execute(text(query), params).fetchall()


def _process_parcel(db, client: Client, parcel, years: int, dry_run: bool) -> dict:
    stats = {"dates": 0, "deja": 0, "inserees": 0, "nuageuses": 0, "echecs": 0}

    plan = hs.plan_parcel(db, parcel.id, years=years, client=client)
    if plan is None:
        print("   pas de géométrie, ignorée")
        return stats

    stats["dates"], stats["deja"] = plan.found, plan.already
    print(f"   période : {plan.start.isoformat()} → {plan.end.isoformat()}")
    print(f"   {plan.found} dates trouvées, {plan.already} déjà en base, {len(plan.todo)} à traiter")

    if dry_run or not plan.todo:
        return stats

    started = time.time()

    def progress(i: int, total: int, result: hs.BatchResult) -> None:
        if i % 10 == 0 or i == total:
            print(
                f"   {i}/{total} dates · {result.inserted} enregistrées · "
                f"{result.cloudy} trop nuageuses · {(time.time() - started) / 60:.1f} min"
            )

    result = hs.process_dates(db, parcel.id, plan.todo, client=client, on_progress=progress)

    stats.update(inserees=result.inserted, nuageuses=result.cloudy, echecs=result.failed)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--parcel-id", type=int, help="Traiter une seule parcelle")
    parser.add_argument(
        "--farm", action="append", default=[],
        help="Limiter aux parcelles de cette ferme (option répétable)",
    )
    parser.add_argument("--years", type=int, default=hs.HISTORY_YEARS, help="Années passées (défaut : 3)")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Compter les dates à traiter, sans rien télécharger ni enregistrer",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        parcels = _select_parcels(db, args.parcel_id, args.farm)
        if not parcels:
            print("Aucune parcelle trouvée.")
            return 1

        client = Client.open(STAC_API_URL)
        mode = "ESSAI, rien ne sera enregistré" if args.dry_run else "téléchargement"
        print(f"Historique sur {args.years} ans · {len(parcels)} parcelle(s) · {mode}\n")

        totals = defaultdict(int)
        failed: list[str] = []
        for parcel in parcels:
            print(f"[{parcel.farm}] {parcel.name} (id {parcel.id})")
            try:
                stats = _process_parcel(db, client, parcel, args.years, args.dry_run)
            except Exception as e:
                # Une parcelle en échec n'arrête pas les suivantes
                db.rollback()
                failed.append(f"{parcel.name} (id {parcel.id})")
                print(f"   ÉCHEC de la parcelle : {type(e).__name__} : {e}")
                print("   les dates déjà enregistrées sont conservées\n")
                continue
            for k, v in stats.items():
                totals[k] += v
            print()

        if args.dry_run:
            todo = totals["dates"] - totals["deja"]
            print(f"Total : {todo} dates à traiter, soit environ {todo * 12 / 3600:.1f} h de calcul.")
            print("Rien n'a été enregistré.")
        else:
            print(
                f"Terminé : {totals['inserees']} dates enregistrées, "
                f"{totals['nuageuses']} trop nuageuses, {totals['echecs']} échecs."
            )
        if failed:
            print(f"Parcelles interrompues : {', '.join(failed)}.")
            print("Relancer la même commande pour les reprendre : les dates déjà en base sont ignorées.")
            return 2
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    code = 1
    try:
        code = main()
    except KeyboardInterrupt:
        print("\nInterrompu. Relancer la même commande pour reprendre.")
    finally:
        # Sortie immédiate : évite les erreurs de fermeture de rasterio et
        # GDAL sous Windows (« Error in sys.excepthook »), sans effet sur les données.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)