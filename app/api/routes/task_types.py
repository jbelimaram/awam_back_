"""
Routes des types de tâche : les prédéfinis (lecture seule) et les types
LIBRES du compte (créer, voir, renommer, supprimer), valables pour toutes
ses fermes. Ces types nomment les équipes (farm_employee.team).

Règles :
  - un nom ne peut pas reprendre celui d'un autre type, prédéfini compris ;
  - renommer un type libre renomme aussi les équipes qui le portent, et les
    tâches enregistrées sous l'ancien nom ;
  - supprimer un type libre est refusé tant qu'une équipe le porte ; les
    tâches déjà enregistrées gardent leur nom, pour l'historique.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.activity import Activity
from app.models.farm import Farm
from app.models.farm_employee import FarmEmployee
from app.models.parcel import Parcel
from app.models.task_type import TaskType
from app.models.utilisateur import User
from app.schemas.task_type import TaskTypeCreate, TaskTypeResponse, TaskTypeUpdate
from app.services.task_types import PREDEFINED_TASK_TYPES, custom_types, is_name_taken

router = APIRouter(prefix="/task-types", tags=["task-types"])


def _get_owned_type(type_id: int, user: User, db: Session) -> TaskType:
    task_type = (
        db.query(TaskType)
        .filter(TaskType.id == type_id, TaskType.user_id == user.id)
        .first()
    )
    if not task_type:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Type de tâche introuvable.")
    return task_type


def _farm_links_of_user(user: User, db: Session):
    """Rattachements employé-ferme de toutes les fermes du compte."""
    return (
        db.query(FarmEmployee)
        .join(Farm, FarmEmployee.farm_id == Farm.id)
        .filter(Farm.user_id == user.id)
    )


def _to_response(task_type: TaskType) -> TaskTypeResponse:
    return TaskTypeResponse(id=task_type.id, code=task_type.name, label=task_type.name, predefined=False)


@router.get("", response_model=List[TaskTypeResponse])
async def list_task_types(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Types prédéfinis, puis types libres du compte."""
    predefined = [
        TaskTypeResponse(code=code, label=label, predefined=True)
        for code, label in PREDEFINED_TASK_TYPES
    ]
    return predefined + [_to_response(t) for t in custom_types(db, user.id)]


@router.post("", response_model=TaskTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_task_type(
    payload: TaskTypeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if is_name_taken(db, user.id, payload.name):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Le type « {payload.name} » existe déjà.")
    task_type = TaskType(user_id=user.id, name=payload.name)
    db.add(task_type)
    db.commit()
    db.refresh(task_type)
    return _to_response(task_type)


@router.put("/{type_id}", response_model=TaskTypeResponse)
async def rename_task_type(
    type_id: int,
    payload: TaskTypeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task_type = _get_owned_type(type_id, user, db)
    old_name, new_name = task_type.name, payload.name
    if new_name == old_name:
        return _to_response(task_type)
    if is_name_taken(db, user.id, new_name, exclude_id=task_type.id):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Le type « {new_name} » existe déjà.")

    task_type.name = new_name
    # Les équipes et les tâches portant l'ancien nom suivent le renommage
    for link in _farm_links_of_user(user, db).filter(FarmEmployee.team == old_name).all():
        link.team = new_name
    activities = (
        db.query(Activity)
        .join(Parcel, Activity.parcel_id == Parcel.id)
        .join(Farm, Parcel.farm_id == Farm.id)
        .filter(Farm.user_id == user.id, Activity.activity_type == old_name)
        .all()
    )
    for activity in activities:
        activity.activity_type = new_name

    db.commit()
    db.refresh(task_type)
    return _to_response(task_type)


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_type(
    type_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task_type = _get_owned_type(type_id, user, db)
    members = _farm_links_of_user(user, db).filter(FarmEmployee.team == task_type.name).count()
    if members:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"L'équipe « {task_type.name} » compte encore {members} employé"
            f"{'s' if members > 1 else ''} : changez-les d'équipe avant de supprimer ce type.",
        )
    db.delete(task_type)
    db.commit()
    return None