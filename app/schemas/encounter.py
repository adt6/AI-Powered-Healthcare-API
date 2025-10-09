from datetime import date

from pydantic import BaseModel


class EncounterCreate(BaseModel):
    date: date
    patient_id: int
    practitioner_id: int


class EncounterResponse(EncounterCreate):
    id: int

    class Config:
        orm_mode = True
