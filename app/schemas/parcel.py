from typing import Optional
from pydantic import BaseModel, field_validator

ALLOWED_STATUSES = {"active", "inactive"}


class ParcelCreate(BaseModel):
    farm_id: int
    name: str
    culture_type: str
    area_ha: float
    status: str = "active"
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    latitude: float
    longitude: float
    polygon_geojson: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le nom de la parcelle est requis.")
        if len(v) > 150:
            raise ValueError("Le nom de la parcelle ne doit pas dépasser 150 caractères.")
        return v

    @field_validator("culture_type")
    @classmethod
    def culture_type_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le type de culture est requis.")
        if len(v) > 100:
            raise ValueError("Le type de culture ne doit pas dépasser 100 caractères.")
        return v

    @field_validator("area_ha")
    @classmethod
    def area_ha_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("La superficie doit être supérieure à 0.")
        return v

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: str) -> str:
        if v not in ALLOWED_STATUSES:
            raise ValueError(f"Statut invalide. Valeurs autorisées : {', '.join(ALLOWED_STATUSES)}.")
        return v

    @field_validator("soil_type")
    @classmethod
    def soil_type_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Le type de sol ne doit pas dépasser 100 caractères.")
        return v or None

    @field_validator("irrigation_type")
    @classmethod
    def irrigation_type_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Le type d'irrigation ne doit pas dépasser 100 caractères.")
        return v or None

    @field_validator("latitude")
    @classmethod
    def latitude_valid(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("La latitude doit être comprise entre -90 et 90.")
        return v

    @field_validator("longitude")
    @classmethod
    def longitude_valid(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("La longitude doit être comprise entre -180 et 180.")
        return v


class ParcelUpdate(BaseModel):
    farm_id: Optional[int] = None
    name: Optional[str] = None
    culture_type: Optional[str] = None
    area_ha: Optional[float] = None
    status: Optional[str] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    polygon_geojson: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Le nom de la parcelle est requis.")
        if len(v) > 150:
            raise ValueError("Le nom de la parcelle ne doit pas dépasser 150 caractères.")
        return v

    @field_validator("culture_type")
    @classmethod
    def culture_type_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Le type de culture est requis.")
        if len(v) > 100:
            raise ValueError("Le type de culture ne doit pas dépasser 100 caractères.")
        return v

    @field_validator("area_ha")
    @classmethod
    def area_ha_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("La superficie doit être supérieure à 0.")
        return v

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in ALLOWED_STATUSES:
            raise ValueError(f"Statut invalide. Valeurs autorisées : {', '.join(ALLOWED_STATUSES)}.")
        return v

    @field_validator("soil_type")
    @classmethod
    def soil_type_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Le type de sol ne doit pas dépasser 100 caractères.")
        return v or None

    @field_validator("irrigation_type")
    @classmethod
    def irrigation_type_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Le type d'irrigation ne doit pas dépasser 100 caractères.")
        return v or None

    @field_validator("latitude")
    @classmethod
    def latitude_valid(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if not -90 <= v <= 90:
            raise ValueError("La latitude doit être comprise entre -90 et 90.")
        return v

    @field_validator("longitude")
    @classmethod
    def longitude_valid(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if not -180 <= v <= 180:
            raise ValueError("La longitude doit être comprise entre -180 et 180.")
        return v


class ParcelResponse(BaseModel):
    id: int
    farm_id: int
    name: str
    culture_type: str
    area_ha: float
    status: str
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    latitude: float
    longitude: float
    polygon_geojson: Optional[str] = None

    class Config:
        from_attributes = True