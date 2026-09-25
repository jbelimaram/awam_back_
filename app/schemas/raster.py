from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel

# Source unique des types de raster valides (utilisée aussi par app/api/routes/raster.py)
RasterType = Literal["cog", "landsat_rgb", "landsat_ndvi"]


class RasterUploadResponse(BaseModel):
    id: int
    parcel_id: int
    raster_type: RasterType
    nom: Optional[str] = None
    url: str


class RasterResponse(BaseModel):
    id: int
    raster_type: RasterType
    nom: Optional[str] = None
    url: str
    created_at: datetime


class RasterCurrentResponse(BaseModel):
    url: Optional[str] = None