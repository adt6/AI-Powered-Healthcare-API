from sqlalchemy import Column, Date, Integer, String

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    birth_date = Column(Date)
