from sqlalchemy import Column, Integer, String

from api.v1.database import Base


class Practitioner(Base):
    __tablename__ = "practitioners"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    specialty = Column(String)
