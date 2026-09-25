from typing import Any, Optional
from pydantic import BaseModel


class ParcelCreate(BaseModel):
    farm_id: int
    name: str
    geometry: dict[str, Any]  # objet GeoJSON brut (Polygon)
    culture_type: Optional[str] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None


class ParcelUpdate(BaseModel):
    name: Optional[str] = None
    geometry: Optional[dict[str, Any]] = None
    culture_type: Optional[str] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None


class ParcelResponse(BaseModel):
    id: int
    farm_id: int
    name: str
    culture_type: Optional[str] = None
    area_ha: Optional[float] = None
    status: str
    geometry: Optional[dict[str, Any]] = None  # forme du polygone renvoyée au frontend

    cog_url: Optional[str] = None
    landsat_rgb_url: Optional[str] = None
    landsat_ndvi_url: Optional[str] = None

    model_config = {"from_attributes": True}