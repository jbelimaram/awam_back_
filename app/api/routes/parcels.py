from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.utilisateur import User
from app.models.farm import Farm
from app.models.parcel import Parcel
from app.schemas.parcel import ParcelCreate, ParcelUpdate, ParcelResponse

router = APIRouter(prefix="/parcels", tags=["parcels"])


@router.get("", response_model=List[ParcelResponse])
async def list_parcels(
    farm_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Parcel)
    if farm_id is not None:
        query = query.filter(Parcel.farm_id == farm_id)
    return query.order_by(Parcel.name).all()


@router.get("/{parcel_id}", response_model=ParcelResponse)
async def get_parcel(
    parcel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")
    return parcel


@router.post("", response_model=ParcelResponse, status_code=status.HTTP_201_CREATED)
async def create_parcel(
    payload: ParcelCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == payload.farm_id).first()
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ferme introuvable.")

    new_parcel = Parcel(
        farm_id=payload.farm_id,
        name=payload.name,
        culture_type=payload.culture_type,
        area_ha=payload.area_ha,
        status=payload.status,
        soil_type=payload.soil_type,
        irrigation_type=payload.irrigation_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        polygon_geojson=payload.polygon_geojson,
    )
    db.add(new_parcel)
    db.commit()
    db.refresh(new_parcel)
    return new_parcel


@router.put("/{parcel_id}", response_model=ParcelResponse)
async def update_parcel(
    parcel_id: int,
    payload: ParcelUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")

    update_data = payload.model_dump(exclude_unset=True)

    if "farm_id" in update_data:
        farm = db.query(Farm).filter(Farm.id == update_data["farm_id"]).first()
        if not farm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ferme introuvable.")

    for field, value in update_data.items():
        setattr(parcel, field, value)

    db.commit()
    db.refresh(parcel)
    return parcel


@router.delete("/{parcel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parcel(
    parcel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")

    db.delete(parcel)
    db.commit()
    return None