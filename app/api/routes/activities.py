from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.utilisateur import User
from app.models.parcel import Parcel
from app.models.employee import Employee
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityResponse
from datetime import datetime, timezone

router = APIRouter(tags=["activities"])


@router.get("/parcels/{parcel_id}/activities", response_model=List[ActivityResponse])
async def list_parcel_activities(
    parcel_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")

    return (
        db.query(Activity)
        .filter(Activity.parcel_id == parcel_id)
        .order_by(Activity.performed_at.desc())
        .all()
    )


@router.post("/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    payload: ActivityCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parcel = db.query(Parcel).filter(Parcel.id == payload.parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable.")

    employees = db.query(Employee).filter(Employee.id.in_(payload.employee_ids)).all()
    if len(employees) != len(set(payload.employee_ids)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Un ou plusieurs employés sont introuvables.",
        )

    new_activity = Activity(
    parcel_id=payload.parcel_id,
    activity_type=payload.activity_type,
    performed_at=payload.performed_at or datetime.now(timezone.utc),
    )
    new_activity.employees = employees

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity