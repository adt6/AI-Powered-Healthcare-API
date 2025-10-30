from sqlalchemy import Column, Date, ForeignKey, Integer
from sqlalchemy.orm import relationship

from api.v1.database import Base


class Encounter(Base):
    __tablename__ = "encounters"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)

    patient_id = Column(Integer, ForeignKey("patients.id"))
    practitioner_id = Column(Integer, ForeignKey("practitioners.id"))

    # Relationships
    patient = relationship("Patient")
    practitioner = relationship("Practitioner")
