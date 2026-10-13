"""
Tâches Celery : constitution de l'historique Sentinel-2 d'une parcelle,
en arrière-plan et sans affichage. L'utilisateur voit simplement la plage
habituelle apparaître sous la courbe une fois l'historique constitué.

Déroulement (file dédiée « awam_queues:historique ») :

    history.plan_parcel
        · liste les dates de passage du satellite sur HISTORY_YEARS ans,
          moins celles déjà en base
        · lance la chaîne :
    history.ingest_batch (lot 1) → (lot 2) → … → (lot N)
        · chaque lot : BATCH_SIZE dates, environ 4 à 5 minutes

Pourquoi des lots : une tâche de 30 à 60 minutes serait considérée comme
perdue par le broker Redis au bout d'une heure, et relancée en double ;
une coupure tardive ferait tout recommencer. Avec des lots courts, une
coupure ne coûte qu'un lot.

Relances sûres : les dates déjà en base sont toujours ignorées, donc un
double lancement ou une reprise ne crée aucun doublon.

Déclencheur : création d'une parcelle active (routes/parcels.py), quelques
minutes après les premières tâches. Pour les parcelles existantes :
app/scripts/backfill_indices_history.py.

⚠️  Ces tâches sont longues : elles doivent tourner sur un worker DÉDIÉ,
    pour ne jamais bloquer les indices du jour ni la tâche de 6 h :

    celery -A app.celery_app worker -Q awam_queues:historique --pool=solo -n historique@%h
"""

import logging

from sqlalchemy import text

from app.db.database import SessionLocal
from app.services import history_service as hs

logger = logging.getLogger(__name__)

#: File Celery dédiée à l'historique (voir celery_app.py)
HISTORY_QUEUE = "awam_queues:historique"


def _parcel_exists(db, parcel_id: int) -> bool:
    return db.execute(
        text("SELECT 1 FROM parcel WHERE id = :pid"), {"pid": parcel_id}
    ).scalar() is not None


def plan_parcel_history(parcel_id: int, years: int = hs.HISTORY_YEARS) -> dict:
    """Liste les dates à traiter et lance la chaîne de lots."""
    db = SessionLocal()
    try:
        if not _parcel_exists(db, parcel_id):
            return {"parcel_id": parcel_id, "skipped": "parcelle introuvable"}

        plan = hs.plan_parcel(db, parcel_id, years=years)
        if plan is None:
            return {"parcel_id": parcel_id, "skipped": "pas de géométrie"}
    finally:
        db.close()

    if not plan.todo:
        logger.info("[Historique] Parcelle %s : déjà complet (%s dates)", parcel_id, plan.found)
        return {"parcel_id": parcel_id, "todo": 0, "already": plan.already}

    lots = hs.batches(plan.todo)
    _launch_chain(parcel_id, lots)
    logger.info(
        "[Historique] Parcelle %s : %s dates à traiter en %s lots (%s → %s)",
        parcel_id, len(plan.todo), len(lots), plan.start, plan.end,
    )
    return {"parcel_id": parcel_id, "todo": len(plan.todo), "batches": len(lots), "already": plan.already}


def ingest_history_batch(parcel_id: int, dates: list[str]) -> dict:
    """Traite un lot de dates."""
    db = SessionLocal()
    try:
        if not _parcel_exists(db, parcel_id):
            return {"parcel_id": parcel_id, "skipped": "parcelle supprimée"}
        result = hs.process_dates(db, parcel_id, dates)
        logger.info(
            "[Historique] Parcelle %s : lot de %s dates · %s enregistrées · %s nuageuses · %s échecs",
            parcel_id, len(dates), result.inserted, result.cloudy, result.failed,
        )
        return {
            "parcel_id": parcel_id,
            "inserted": result.inserted,
            "cloudy": result.cloudy,
            "failed": result.failed,
        }
    finally:
        db.close()


def _launch_chain(parcel_id: int, lots: list[list[str]]) -> None:
    """Enchaîne les lots, sur la file dédiée."""
    from celery import chain

    chain(*[ingest_history_batch_task.si(parcel_id, lot) for lot in lots]).apply_async(
        queue=HISTORY_QUEUE
    )


def enqueue_history(parcel_id: int, countdown: int = 0) -> bool:
    """
    Met la constitution de l'historique en file. Renvoie False si Celery
    ou le broker est indisponible : la création de la parcelle n'échoue pas
    pour autant, et le script permettra de constituer l'historique plus tard.
    """
    if plan_parcel_history_task is None:
        logger.warning("[Historique] Celery indisponible : historique non lancé (parcelle %s)", parcel_id)
        return False
    try:
        plan_parcel_history_task.apply_async(
            args=[parcel_id], countdown=countdown, queue=HISTORY_QUEUE
        )
        return True
    except Exception:
        logger.exception("[Historique] Mise en file impossible (parcelle %s)", parcel_id)
        return False


# ======================================================================
# Wrappers Celery
# ======================================================================

try:
    from app.celery_app import celery_app

    @celery_app.task(name="history.plan_parcel", bind=True, max_retries=3)
    def plan_parcel_history_task(self, parcel_id: int, years: int = hs.HISTORY_YEARS) -> dict:
        """Planification : relancée jusqu'à 3 fois si le catalogue est injoignable."""
        try:
            return plan_parcel_history(parcel_id, years=years)
        except Exception as exc:
            logger.exception("[Historique] Échec de la planification (parcelle %s)", parcel_id)
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

    @celery_app.task(name="history.ingest_batch", bind=True, max_retries=3)
    def ingest_history_batch_task(self, parcel_id: int, dates: list[str]) -> dict:
        """Un lot : relancé jusqu'à 3 fois en cas de coupure réseau."""
        try:
            return ingest_history_batch(parcel_id, dates)
        except Exception as exc:
            logger.exception("[Historique] Échec d'un lot (parcelle %s)", parcel_id)
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

except ImportError as e:
    plan_parcel_history_task = None
    ingest_history_batch_task = None
    logger.error("Celery non configuré (%s) : historique indisponible en tâche de fond.", e)