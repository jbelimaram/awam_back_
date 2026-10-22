"""
Suivi des cultures : lecture des données en base, diagnostic, archivage.

Fait le lien entre la base (indices, activités, cultures) et le moteur
de diagnostic, qui lui ne fait aucun accès en base.

L'archivage dans `crop_diagnosis` est ce qui permet :
  - la règle des deux observations consécutives (une anomalie n'est
    confirmée qu'à la seconde image) ;
  - les alertes, qui ne partent que sur anomalie confirmée ;
  - l'historique des performances au fil des saisons.

INTERPRÉTATION DES ANALYSES — les indices de chaque date sont déjà
calculés (indice_reading). Ce module les INTERPRÈTE : il ne télécharge
aucune image et ne recalcule aucun indice. À chaque passage, toutes les
dates d'analyse des INTERPRETATION_WINDOW_DAYS derniers jours qui n'ont
pas encore été interprétées pour une culture le sont, de la plus ancienne
à la plus récente : la règle des deux images exige que la date précédente
soit interprétée avant la suivante. Le système se rattrape donc tout seul
(premier passage, worker arrêté, plusieurs images entre deux passages).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.crop import Crop
from app.models.crop_diagnosis import CropDiagnosis
from app.services.alert_service import sync_alert
from app.services.diagnosis_service import Diagnosis, diagnose

logger = logging.getLogger(__name__)

#: Une récolte de moins de 30 jours explique encore une baisse de couvert
HARVEST_WINDOW_DAYS = 30
HARVEST_TYPES = {"recolte", "récolte", "harvest", "coupe"}

#: Fenêtre des analyses interprétées à chaque passage, en jours
INTERPRETATION_WINDOW_DAYS = 30


@dataclass
class SceneValues:
    scene_date: date | None
    values: dict[str, float]
    #: Part de la parcelle réellement observée (0 à 1), si connue
    valid_ratio: float | None


def latest_scene(db: Session, parcel_id: int, before: date | None = None) -> SceneValues:
    """
    Valeurs des indices d'une image de la parcelle.

    Sans `before` : l'image la plus récente. Avec `before` : la dernière
    image antérieure à cette date (pour calculer les variations).
    """
    params: dict = {"pid": parcel_id}
    condition = ""
    if before is not None:
        condition = "AND scene_date < :before"
        params["before"] = before

    row = db.execute(
        text(f"""
            SELECT MAX(scene_date) AS d FROM indice_reading
            WHERE parcel_id = :pid AND is_valid IS NOT FALSE {condition}
        """),
        params,
    ).fetchone()
    if not row or not row.d:
        return SceneValues(None, {}, None)
    return scene_at(db, parcel_id, row.d)


def scene_at(db: Session, parcel_id: int, scene_date: date) -> SceneValues:
    """Valeurs des indices, déjà calculés, de l'analyse d'une date."""
    rows = db.execute(
        text("""
            SELECT indice_name, value, valid_ratio FROM indice_reading
            WHERE parcel_id = :pid AND scene_date = :d AND value IS NOT NULL
        """),
        {"pid": parcel_id, "d": scene_date},
    ).fetchall()

    ratios = [r.valid_ratio for r in rows if r.valid_ratio is not None]
    return SceneValues(
        scene_date=scene_date,
        values={r.indice_name: r.value for r in rows},
        valid_ratio=min(ratios) if ratios else None,
    )


def analysis_dates(db: Session, parcel_id: int, since: date) -> list[date]:
    """Dates des analyses valides de la parcelle depuis `since`, dans l'ordre."""
    rows = db.execute(
        text("""
            SELECT DISTINCT scene_date FROM indice_reading
            WHERE parcel_id = :pid AND is_valid IS NOT FALSE AND scene_date >= :since
            ORDER BY scene_date
        """),
        {"pid": parcel_id, "since": since},
    ).fetchall()
    return [r.scene_date for r in rows]


def has_recent_harvest(db: Session, crop: Crop, reference: date) -> bool:
    """Une récolte ou coupe récente explique une baisse de couvert."""
    since = reference - timedelta(days=HARVEST_WINDOW_DAYS)
    activities = (
        db.query(Activity)
        .filter(Activity.crop_id == crop.id, Activity.performed_at >= since)
        .all()
    )
    return any(
        (a.activity_type or "").strip().lower() in HARVEST_TYPES for a in activities
    )


def previous_severity(db: Session, crop_id: int, scene_date: date | None) -> str | None:
    """Gravité du dernier diagnostic archivé AVANT cette image."""
    query = db.query(CropDiagnosis).filter(CropDiagnosis.crop_id == crop_id)
    if scene_date is not None:
        query = query.filter(CropDiagnosis.scene_date < scene_date)
    last = query.order_by(CropDiagnosis.scene_date.desc()).first()
    return last.severity if last else None


def run_diagnosis(db: Session, crop: Crop) -> tuple[Diagnosis, SceneValues]:
    """Diagnostic de la culture sur la dernière image disponible."""
    current = latest_scene(db, crop.parcel_id)
    if current.scene_date is not None:
        return run_diagnosis_at(db, crop, current.scene_date)
    return _diagnose(db, crop, current, SceneValues(None, {}, None))


def run_diagnosis_at(db: Session, crop: Crop, scene_date: date) -> tuple[Diagnosis, SceneValues]:
    """
    Interprète l'analyse d'UNE date : ses indices sont comparés aux seuils
    et à l'analyse précédente, sans rien recalculer.
    """
    current = scene_at(db, crop.parcel_id, scene_date)
    previous = latest_scene(db, crop.parcel_id, before=scene_date)
    return _diagnose(db, crop, current, previous)


def _diagnose(
    db: Session, crop: Crop, current: SceneValues, previous: SceneValues
) -> tuple[Diagnosis, SceneValues]:
    reference = current.scene_date or date.today()
    result = diagnose(
        species=crop.species,
        scene_date=reference,
        values=current.values,
        previous_values=previous.values,
        previous_severity=previous_severity(db, crop.id, current.scene_date),
        recent_harvest=has_recent_harvest(db, crop, reference),
        planting_date=crop.planting_date,
        valid_ratio=current.valid_ratio,
    )
    return result, current


def archive_diagnosis(
    db: Session, crop: Crop, result: Diagnosis, scene: SceneValues
) -> CropDiagnosis | None:
    """
    Enregistre le diagnostic d'une image. Une seule ligne par culture et
    par date d'image : un nouveau calcul sur la même image la met à jour.
    """
    if scene.scene_date is None or not result.indicators:
        return None

    first_risk = result.risks[0] if result.risks else None
    payload = dict(
        stage=result.stage,
        indicators=[
            {
                "name": i.name,
                "value": round(i.value, 4),
                "delta": round(i.delta, 4) if i.delta is not None else None,
                "level": i.level,
                "threshold_label": i.threshold_label,
                "unit": i.unit,
            }
            for i in result.indicators
        ],
        severity=result.severity,
        diagnosis=first_risk.diagnosis if first_risk else result.reading,
        measure=first_risk.measure if first_risk else None,
        action=first_risk.action if first_risk else result.recommendation,
        cultural_drop="true" if result.cultural_drop else "false",
    )

    existing = (
        db.query(CropDiagnosis)
        .filter(CropDiagnosis.crop_id == crop.id, CropDiagnosis.scene_date == scene.scene_date)
        .first()
    )
    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
        record = existing
    else:
        record = CropDiagnosis(crop_id=crop.id, scene_date=scene.scene_date, **payload)
        db.add(record)

    db.commit()
    return record


def interpret_crop(
    db: Session, crop: Crop, today: date | None = None
) -> tuple[int, bool]:
    """
    Interprète les analyses des INTERPRETATION_WINDOW_DAYS derniers jours
    qui ne l'ont pas encore été pour cette culture, de la plus ancienne à
    la plus récente, et fait évoluer son alerte à chaque date.

    La date la plus récente est toujours réinterprétée : elle a pu être
    enregistrée par la consultation du diagnostic, avant que l'alerte ne
    soit mise à jour. Le traitement des alertes étant idempotent, une date
    déjà prise en compte ne change rien.

    Returns:
        (nombre d'interprétations enregistrées, une alerte a-t-elle changé)
    """
    today = today or date.today()
    since = today - timedelta(days=INTERPRETATION_WINDOW_DAYS)
    if crop.planting_date and crop.planting_date > since:
        since = crop.planting_date

    dates = analysis_dates(db, crop.parcel_id, since)
    if not dates:
        return 0, False

    done = {
        d for (d,) in db.query(CropDiagnosis.scene_date)
        .filter(CropDiagnosis.crop_id == crop.id, CropDiagnosis.scene_date >= since)
        .all()
    }
    latest = dates[-1]

    archived, changed = 0, False
    for scene_date in dates:
        if scene_date in done and scene_date != latest:
            continue
        result, scene = run_diagnosis_at(db, crop, scene_date)
        if archive_diagnosis(db, crop, result, scene):
            archived += 1
        if sync_alert(db, crop, result, scene):
            changed = True
    return archived, changed


def archive_for_parcel(db: Session, parcel_id: int) -> int:
    """
    Interprète les analyses de toutes les cultures EN COURS d'une parcelle
    et fait évoluer leurs alertes. Appelé après chaque analyse satellite.

    Returns:
        Nombre d'interprétations enregistrées.
    """
    crops = (
        db.query(Crop)
        .filter(Crop.parcel_id == parcel_id, Crop.status == "active")
        .all()
    )

    archived = 0
    alerts_changed = False
    for crop in crops:
        try:
            count, changed = interpret_crop(db, crop)
            archived += count
            alerts_changed = alerts_changed or changed
            if count:
                logger.info("[suivi] Culture %s (%s) : %s analyse(s) interprétée(s)", crop.id, crop.species, count)
        except Exception:
            db.rollback()
            logger.exception("[suivi] Interprétation impossible pour la culture %s", crop.id)

    # Prévient les pages ouvertes : la cloche et l'historique se mettent à jour
    if alerts_changed:
        from app.services.events import publish_parcel_event

        publish_parcel_event(parcel_id, "alerts")

    return archived