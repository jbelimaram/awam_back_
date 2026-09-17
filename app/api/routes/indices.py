from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.utilisateur import User
from app.models.parcel import Parcel
from app.models.indice_reading import IndiceReading
from app.schemas.indice_reading import IndiceReadingResponse

router = APIRouter(tags=["indices"])


@router.get("/parcels/{parcel_id}/indices", response_model=List[IndiceReadingResponse])
async def list_parcel_indices(
    parcel_id: int,
    indice_name: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")

    query = db.query(IndiceReading).filter(IndiceReading.parcel_id == parcel_id)
    if indice_name:
        query = query.filter(IndiceReading.indice_name == indice_name)

    return query.order_by(IndiceReading.recorded_at).all()


@router.get("/parcels/{parcel_id}/indices/available", response_model=List[str])
async def list_available_indices(
    parcel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")

    rows = (
        db.query(IndiceReading.indice_name)
        .filter(IndiceReading.parcel_id == parcel_id)
        .distinct()
        .all()
    )
    return [r[0] for r in rows]