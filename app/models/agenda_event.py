from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from sqlalchemy import Boolean


class AgendaEvent(Base):
    __tablename__ = "agenda_event"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False, index=True)

    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), nullable=False, server_default="a_faire")
    reminder = Column(String(20), nullable=True)
    reminder_custom_minutes = Column(Integer, nullable=True)
    reminder_custom_unit = Column(String(20), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="agenda_events")
    reminder_sent = Column(Boolean, nullable=False, server_default="false")