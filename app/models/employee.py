"""
Employé d'un exploitant.

Un employé APPARTIENT à un compte (user_id) : chaque exploitant ne voit,
ne modifie et ne supprime que ses propres employés. Il peut travailler
dans plusieurs fermes de ce compte : le rattachement, avec le rôle
(« coordinateur » ou « membre »), est dans farm_employee.
"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    #: Compte propriétaire de l'employé
    user_id = Column(Integer, ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=True, index=True)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(30), nullable=True)

    activities = relationship("Activity", secondary="activity_employee", back_populates="employees")
    farm_links = relationship(
        "FarmEmployee",
        back_populates="employee",
        cascade="all, delete-orphan",
    )