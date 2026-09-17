from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class Parcel(Base):
    __tablename__ = "parcel"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farm.id"), nullable=False, index=True)

    name = Column(String(150), nullable=False)
    culture_type = Column(String(100), nullable=False)
    area_ha = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, server_default="active")
    soil_type = Column(String(100), nullable=True)
    irrigation_type = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    polygon_geojson = Column(Text, nullable=True)

    farm = relationship("Farm", back_populates="parcels")
    activities = relationship("Activity", back_populates="parcel", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="parcel", cascade="all, delete-orphan")
    indice_readings = relationship("IndiceReading", back_populates="parcel", cascade="all, delete-orphan")