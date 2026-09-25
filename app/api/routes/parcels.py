from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import shape, mapping

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.utilisateur import User
from app.models.farm import Farm
from app.models.parcel import Parcel
from app.models.raster import Raster
from app.services.b2_storage import generate_presigned_url
from app.schemas.parcel import ParcelCreate, ParcelUpdate, ParcelResponse

router = APIRouter(prefix="/parcels", tags=["parcels"])

RASTER_TYPE_TO_FIELD = {
    "cog": "cog_url",
    "landsat_rgb": "landsat_rgb_url",
    "landsat_ndvi": "landsat_ndvi_url",
}


def _get_latest_rasters_by_type(parcel_id: int, db: Session) -> dict[str, Raster]:
    """Retourne, pour une parcelle, le raster le plus récent par type
    (cog / landsat_rgb / landsat_ndvi), à partir de l'historique complet stocké en base."""
    latest: dict[str, Raster] = {}
    rasters = (
        db.query(Raster)
        .filter(Raster.parcel_id == parcel_id)
        .order_by(Raster.created_at.desc())
        .all()
    )
    for raster in rasters:
        if raster.raster_type not in latest:
            latest[raster.raster_type] = raster
    return latest


def _parcel_to_response(parcel: Parcel, db: Session) -> dict:
    """Convertit une Parcel (avec son geom PostGIS) en dict compatible ParcelResponse,
    en reconvertissant geom -> GeoJSON, et en résolvant les URLs de rasters les plus récentes."""
    geojson = mapping(to_shape(parcel.geom)) if parcel.geom is not None else None

    latest_rasters = _get_latest_rasters_by_type(parcel.id, db)
    urls = {"cog_url": None, "landsat_rgb_url": None, "landsat_ndvi_url": None}
    for raster_type, field_name in RASTER_TYPE_TO_FIELD.items():
        raster = latest_rasters.get(raster_type)
        if raster:
            urls[field_name] = generate_presigned_url(raster.b2_key)

    return {
        "id": parcel.id,
        "farm_id": parcel.farm_id,
        "name": parcel.name,
        "culture_type": parcel.culture_type,
        "area_ha": parcel.area_ha,
        "status": parcel.status,
        "geometry": geojson,
        **urls,
    }


def _compute_area_ha(parcel_id: int, db: Session) -> float | None:
    """Calcule l'aire géodésique d'une parcelle en hectares via PostGIS
    (geometry -> geography pour obtenir des m², puis conversion en ha)."""
    return db.scalar(
        select(func.ST_Area(func.geography(Parcel.geom)) / 10000.0).where(Parcel.id == parcel_id)
    )


@router.get("", response_model=List[ParcelResponse])
async def list_parcels(
    farm_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Parcel).join(Farm).filter(Farm.user_id == user.id)
    if farm_id is not None:
        query = query.filter(Parcel.farm_id == farm_id)
    parcels = query.order_by(Parcel.name).all()
    return [_parcel_to_response(p, db) for p in parcels]


@router.get("/{parcel_id}", response_model=ParcelResponse)
async def get_parcel(
    parcel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = (
        db.query(Parcel)
        .join(Farm)
        .filter(Parcel.id == parcel_id, Farm.user_id == user.id)
        .first()
    )
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")
    return _parcel_to_response(parcel, db)


@router.post("", response_model=ParcelResponse, status_code=status.HTTP_201_CREATED)
async def create_parcel(
    payload: ParcelCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == payload.farm_id, Farm.user_id == user.id).first()
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ferme introuvable.")

    shapely_geom = shape(payload.geometry)
    geom_value = from_shape(shapely_geom, srid=4326)

    new_parcel = Parcel(
        farm_id=payload.farm_id,
        name=payload.name,
        culture_type=payload.culture_type,
        soil_type=payload.soil_type,
        irrigation_type=payload.irrigation_type,
        geom=geom_value,
    )
    db.add(new_parcel)
    db.flush()  # génère l'id sans valider la transaction
    new_parcel.area_ha = _compute_area_ha(new_parcel.id, db)
    db.commit()
    db.refresh(new_parcel)
    return _parcel_to_response(new_parcel, db)


@router.put("/{parcel_id}", response_model=ParcelResponse)
async def update_parcel(
    parcel_id: int,
    payload: ParcelUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = (
        db.query(Parcel)
        .join(Farm)
        .filter(Parcel.id == parcel_id, Farm.user_id == user.id)
        .first()
    )
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")

    update_data = payload.model_dump(exclude_unset=True)
    geometry_changed = "geometry" in update_data

    if geometry_changed:
        geojson_value = update_data.pop("geometry")
        shapely_geom = shape(geojson_value)
        parcel.geom = from_shape(shapely_geom, srid=4326)

    for field, value in update_data.items():
        setattr(parcel, field, value)

    if geometry_changed:
        db.flush()  # envoie la nouvelle géométrie à PostGIS avant de recalculer l'aire
        parcel.area_ha = _compute_area_ha(parcel.id, db)

    db.commit()
    db.refresh(parcel)
    return _parcel_to_response(parcel, db)


@router.delete("/{parcel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parcel(
    parcel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = (
        db.query(Parcel)
        .join(Farm)
        .filter(Parcel.id == parcel_id, Farm.user_id == user.id)
        .first()
    )
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")

    db.delete(parcel)
    db.commit()
    return None