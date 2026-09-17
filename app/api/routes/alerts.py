from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.utilisateur import User
from app.models.parcel import Parcel
from app.models.alert import Alert
from app.schemas.alert import AlertResponse

router = APIRouter(tags=["alerts"])


@router.get("/parcels/{parcel_id}/alerts", response_model=List[AlertResponse])
async def list_parcel_alerts(
    parcel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")

    return (
        db.query(Alert)
        .filter(Alert.parcel_id == parcel_id, Alert.resolved == False)
        .order_by(Alert.created_at.desc())
        .all()
    )


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
async def mark_alert_resolved(
    alert_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerte introuvable.")

    alert.resolved = True
    db.commit()
    db.refresh(alert)
    return alert