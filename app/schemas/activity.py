from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator

from app.schemas.employee import EmployeeResponse


class ActivityCreate(BaseModel):
    parcel_id: int
    activity_type: str
    performed_at: Optional[datetime] = None
    employee_ids: List[int] = []

    @field_validator("activity_type")
    @classmethod
    def activity_type_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le type d'activité est requis.")
        if len(v) > 100:
            raise ValueError("Le type d'activité ne doit pas dépasser 100 caractères.")
        return v

    @field_validator("employee_ids")
    @classmethod
    def employee_ids_not_empty(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError("Au moins un employé doit être associé à l'activité.")
        return v


class ActivityResponse(BaseModel):
    id: int
    parcel_id: int
    activity_type: str
    performed_at: datetime
    employees: List[EmployeeResponse] = []

    class Config:
        from_attributes = True