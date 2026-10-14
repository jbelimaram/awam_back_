"""
Diagnostic, en LECTURE SEULE : liste les images Sentinel-2 disponibles pour
une parcelle depuis une date, avec la part de la parcelle dégagée pour
chacune, et ce que le système en fait. Rien n'est téléchargé ni enregistré.

Sert à comprendre pourquoi la dernière image affichée n'est pas plus récente :
  - « trop nuageuse » : le satellite est passé, mais la parcelle était
    couverte ; le système garde volontairement l'image précédente ;
  - « exploitable, en base » : tout va bien ;
  - « exploitable, ABSENTE de la base » : une image utilisable n'a pas été
    enregistrée, c'est une anomalie à corriger.

Usage, depuis la racine du backend :

    python -m app.scripts.check_recent_scenes --parcel-id 20 --since 2026-10-01
    python -m app.scripts.check_recent_scenes --farm "Sidi Mechreg" --since 2026-10-01
"""

import argparse
import logging
import os
import sys
from collections import defaultdict
from datetime import date

import planetary_computer
from pystac_client import Client
from sqlalchemy import text

from app.db.database import SessionLocal
from app.services.sentinel_service import (
    COLLECTION,
    MAX_CLOUD_COVER,
    MIN_VALID_RATIO,
    STAC_API_URL,
    _get_bbox_for_parcel,
    _get_geometry_for_parcel,
    _parcel_valid_ratio,
)

logging.basicConfig(level=logging.WARNING, format="%(message)s")


def _parcels(db, parcel_id, farm):
    query = """
        SELECT p.id, p.name, f.name AS farm FROM parcel p
        JOIN farm f ON f.id = p.farm_id
        WHERE p.geom IS NOT NULL
    """
    params = {}
    if parcel_id is not None:
        query += " AND p.id = :pid"
        params["pid"] = parcel_id
    else:
        query += " AND p.status = 'active'"
        if farm:
            query += " AND f.name = :farm"
            params["farm"] = farm
    return db.execute(text(query + " ORDER BY f.name, p.name"), params).fetchall()


def _dates_in_base(db, parcel_id):
    rows = db.execute(
        text("SELECT DISTINCT scene_date FROM indice_reading WHERE parcel_id = :pid"),
        {"pid": parcel_id},
    ).fetchall()
    return {r.scene_date.isoformat() for r in rows if r.scene_date}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--parcel-id", type=int)
    parser.add_argument("--farm")
    parser.add_argument("--since", required=True, help="Date de début, AAAA-MM-JJ")
    args = parser.parse_args()

    since = date.fromisoformat(args.since)
    db = SessionLocal()
    try:
        parcels = _parcels(db, args.parcel_id, args.farm)
        if not parcels:
            print("Aucune parcelle trouvée.")
            return 1

        client = Client.open(STAC_API_URL)
        print(f"Images depuis le {since.isoformat()} · seuil : {MIN_VALID_RATIO:.0%} de parcelle dégagée\n")

        for p in parcels:
            print(f"[{p.farm}] {p.name} (id {p.id})")
            bbox = _get_bbox_for_parcel(db, p.id)
            geometry = _get_geometry_for_parcel(db, p.id)
            known = _dates_in_base(db, p.id)

            items = client.search(
                collections=[COLLECTION],
                bbox=bbox,
                datetime=f"{since.isoformat()}/{date.today().isoformat()}",
                query={"eo:cloud_cover": {"lt": 100}},
            ).items()
            by_date = defaultdict(list)
            for item in items:
                by_date[item.properties.get("datetime", "")[:10]].append(item)

            if not by_date:
                print("   aucun passage du satellite sous le plafond de nuages de la scène\n")
                continue

            for day in sorted(by_date):
                best = max(
                    _parcel_valid_ratio(planetary_computer.sign(i), bbox, geometry)
                    for i in by_date[day]
                )
                if best < MIN_VALID_RATIO:
                    verdict = "trop nuageuse, écartée (normal)"
                elif day in known:
                    verdict = "exploitable, en base"
                else:
                    verdict = "exploitable, ABSENTE de la base  <-- anomalie"
                print(f"   {day} · parcelle dégagée à {best:4.0%} · {verdict}")
            print()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    code = 1
    try:
        code = main()
    finally:
        sys.stdout.flush()
        os._exit(code)