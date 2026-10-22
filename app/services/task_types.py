"""
Types de tâche : la liste qui nomme à la fois les ÉQUIPES (Équipe
irrigation, Équipe plantation…) et, aux étapes suivantes, les tâches.

Deux sortes de types :
  - PRÉDÉFINIS : ceux du référentiel, en lecture seule. Leur code est celui
    déjà utilisé par les activités (activity.activity_type) ;
  - LIBRES : créés par l'utilisateur (table task_type), valables pour
    toutes ses fermes, et modifiables (créer, renommer, supprimer).

Un type est désigné par son CODE : le code du référentiel pour un type
prédéfini (« irrigation »), le nom saisi pour un type libre (« Paillage »).
C'est ce code qui est enregistré dans farm_employee.team.
"""

from __future__ import annotations

import re
import unicodedata

from sqlalchemy.orm import Session

from app.models.task_type import TaskType

#: Types prédéfinis : (code, libellé). Les codes sont ceux des activités.
PREDEFINED_TASK_TYPES: list[tuple[str, str]] = [
    ("plantation", "Plantation"),
    ("irrigation", "Irrigation"),
    ("traitement", "Traitement"),
    ("fertilisation", "Fertilisation"),
    ("recolte", "Récolte"),
    ("taille", "Taille"),
    ("desherbage", "Désherbage"),
]

PREDEFINED_CODES = {code for code, _ in PREDEFINED_TASK_TYPES}


def normalize(name: str) -> str:
    """Minuscules, sans accents ni espaces superflus : « Récolte » = « recolte »."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().lower()


#: Formes normalisées des types prédéfinis, codes et libellés
_PREDEFINED_FORMS = {normalize(code) for code, _ in PREDEFINED_TASK_TYPES} | {
    normalize(label) for _, label in PREDEFINED_TASK_TYPES
}


def custom_types(db: Session, user_id: int) -> list[TaskType]:
    """Types libres du compte, par ordre alphabétique."""
    return (
        db.query(TaskType)
        .filter(TaskType.user_id == user_id)
        .order_by(TaskType.name)
        .all()
    )


def is_name_taken(db: Session, user_id: int, name: str, exclude_id: int | None = None) -> bool:
    """Vrai si un type prédéfini ou un autre type libre porte déjà ce nom."""
    wanted = normalize(name)
    if wanted in _PREDEFINED_FORMS:
        return True
    return any(
        normalize(t.name) == wanted
        for t in custom_types(db, user_id)
        if t.id != exclude_id
    )


def is_valid_code(db: Session, user_id: int, code: str) -> bool:
    """Vrai si `code` désigne un type prédéfini ou un type libre du compte."""
    if code in PREDEFINED_CODES:
        return True
    return any(t.name == code for t in custom_types(db, user_id))