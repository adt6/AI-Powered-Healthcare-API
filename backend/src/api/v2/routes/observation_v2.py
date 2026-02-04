from typing import List, Optional

from api.v2.database import get_db
from api.v2.models.observation import ObservationV2
from api.v2.schemas.observation import ObservationResponse
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/observations", response_model=List[ObservationResponse])
def get_observations(
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    encounter_id: Optional[int] = Query(None, description="Filter by encounter ID"),
    practitioner_id: Optional[int] = Query(
        None, description="Filter by practitioner ID"
    ),
    code: Optional[str] = Query(
        None, description="Filter by observation code (e.g., LOINC code)"
    ),
    code_display: Optional[str] = Query(
        None,
        description="Filter by observation type name (e.g., 'hemoglobin', 'blood pressure')",
    ),
    db: Session = Depends(get_db),
):
    """
    Get observations with optional filtering.

    Supports filtering by:
    - patient_id: Get observations for a specific patient
    - encounter_id: Get observations from a specific encounter
    - practitioner_id: Get observations by a specific practitioner
    - code: Filter by observation code (e.g., "718-7" for hemoglobin)
    - code_display: Filter by observation type name (partial match, case-insensitive)

    Examples:
    - /observations?patient_id=3&code_display=hemoglobin
    - /observations?patient_id=3&code_display=blood pressure
    - /observations?patient_id=3&code=718-7
    """
    query = db.query(ObservationV2)

    if patient_id:
        query = query.filter(ObservationV2.patient_id == patient_id)
    if encounter_id:
        query = query.filter(ObservationV2.encounter_id == encounter_id)
    if practitioner_id:
        query = query.filter(ObservationV2.practitioner_id == practitioner_id)
    if code:
        # Exact or partial match on code
        query = query.filter(ObservationV2.code.ilike(f"%{code}%"))
    if code_display:
        # Partial match on code_display (case-insensitive)
        query = query.filter(ObservationV2.code_display.ilike(f"%{code_display}%"))

    # Sort by effective_time (most recent first) for better clinical relevance
    observations = query.order_by(ObservationV2.effective_time.desc()).all()
    return observations


@router.get("/observations/{observation_id}", response_model=ObservationResponse)
def get_observation(observation_id: int, db: Session = Depends(get_db)):
    """Get a specific observation by ID."""
    observation = (
        db.query(ObservationV2).filter(ObservationV2.id == observation_id).first()
    )
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    return observation
