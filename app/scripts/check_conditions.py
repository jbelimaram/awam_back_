"""
Affiche les chiffres de la page « Climat et cultures » pour une ferme et un
mois : chaque paramètre, sa normale 2020-2025 et son écart. Ne modifie rien.

Usage, depuis la racine du backend :

    python -m app.scripts.check_conditions --farm "Sidi Mechreg" --month 2026-10
"""

import argparse
import sys

from app.db.database import SessionLocal
from app.models.farm import Farm
from app.services import conditions_service as cs

LABELS = {
    "temperature_max_c": ("Température max.", "°C"),
    "temperature_min_c": ("Température min.", "°C"),
    "temperature_mean_c": ("Température moy.", "°C"),
    "precipitation_mm": ("Pluie", "mm"),
    "humidity_mean_pct": ("Humidité de l'air", "%"),
    "wind_speed_mean_kmh": ("Vent moyen", "km/h"),
    "radiation_mj_m2": ("Rayonnement", "MJ/m²"),
    "et0_mm": ("ET₀", "mm"),
    "dry_days": ("Jours sans pluie", "jours"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Chiffres du climat d'un mois pour une ferme.")
    parser.add_argument("--farm", required=True, help="Nom de la ferme")
    parser.add_argument("--month", required=True, help="Mois, au format AAAA-MM")
    args = parser.parse_args()
    year, month = (int(x) for x in args.month.split("-"))

    db = SessionLocal()
    farm = db.query(Farm).filter(Farm.name.ilike(args.farm)).first()
    if not farm:
        sys.exit(f"Ferme « {args.farm} » introuvable.")
    r = cs.month_conditions(db, farm.id, year, month)
    db.close()

    print(f"{farm.name} · {r['month']} · {r['days']} jours sur {r['days_in_month']}"
          f"{' (mois en cours)' if r['partial'] else ''}")
    print(f"Normale : {r['normals_period'][0]}-{r['normals_period'][1]}, sur {r['normals_years']} années complètes\n")
    print(f"{'Paramètre':<20}{'Valeur':>12}{'Normale':>12}{'Écart':>12}")
    for key, p in r["parameters"].items():
        label, unit = LABELS[key]
        unit_gap = p["anomaly_unit"] or ("pts" if unit == "%" else unit)
        value = "—" if p["value"] is None else f"{p['value']} {unit}"
        normal = "—" if p["normal"] is None else f"{p['normal']} {unit}"
        gap = "—" if p["anomaly"] is None else f"{p['anomaly']:+} {unit_gap}"
        print(f"{label:<20}{value:>12}{normal:>12}{gap:>12}")
    print(f"\nPlus longue suite de jours secs : {r['longest_dry_spell']} jours")
    print(f"Rafale la plus forte : {r['wind_speed_max_kmh']} km/h, le {r['windiest_day']}")


if __name__ == "__main__":
    main()