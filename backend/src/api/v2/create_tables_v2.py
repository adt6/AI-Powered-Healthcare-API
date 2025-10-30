from app_v2.database import Base, engine
from app_v2.models import (
    ConditionV2,
    EncounterV2,
    ObservationV2,
    OrganizationV2,
    PatientV2,
    PractitionerV2,
)


def main():
    print("Creating v2 tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")


if __name__ == "__main__":
    main()
