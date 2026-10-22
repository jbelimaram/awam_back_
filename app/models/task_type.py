"""
Type de tâche LIBRE, créé par l'utilisateur et valable pour toutes ses
fermes (ex. « Paillage »). Les types prédéfinis du référentiel ne sont pas
ici : voir app/services/task_types.py.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.db.database import Base


class TaskType(Base):
    __tablename__ = "task_type"

    id = Column(Integer, primary_key=True, index=True)
    #: Compte propriétaire : le type est proposé dans toutes ses fermes
    user_id = Column(Integer, ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(60), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_task_type_user_name"),)