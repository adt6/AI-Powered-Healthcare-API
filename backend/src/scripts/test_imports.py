"""
Test script to verify import scripts work correctly with sample data.
This script uses a test SQLite database to avoid affecting production data.
"""

import os
import sys
from pathlib import Path

# Add backend/src to Python path
script_dir = Path(__file__).parent
backend_src = script_dir.parent
sys.path.insert(0, str(backend_src))

# Override DATABASE_URL to use SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///./test_imports.db"

# Import after setting DATABASE_URL and path
from api.v2.database import Base, SessionLocal
from api.v2.models import (
    ConditionV2,
    EncounterV2,
    ObservationV2,
    OrganizationV2,
    PatientV2,
    PractitionerV2,
)
from scripts.import_conditions_v2 import import_path as import_conditions
from scripts.import_encounters_v2 import import_encounters_from_bundle
from scripts.import_observations_v2 import import_path as import_observations

# Import the import scripts
from scripts.import_organizations_v2 import import_path as import_organizations
from scripts.import_patients_v2 import import_patient_from_bundle
from scripts.import_practitioners_v2 import import_path as import_practitioners


def setup_test_db():
    """Create test database and tables."""
    print("=" * 60)
    print("Setting up test database...")
    print("=" * 60)

    # Create tables
    Base.metadata.create_all(bind=SessionLocal().bind)
    print("✓ Test database tables created\n")


def test_import_sample_bundle(bundle_path: Path):
    """Test importing a single sample bundle through all import scripts."""
    print("=" * 60)
    print(f"Testing import with bundle: {bundle_path.name}")
    print("=" * 60)

    if not bundle_path.exists():
        print(f"❌ Bundle file not found: {bundle_path}")
        return False

    # Track counts before and after
    db = SessionLocal()
    try:
        initial_counts = {
            "organizations": db.query(OrganizationV2).count(),
            "patients": db.query(PatientV2).count(),
            "practitioners": db.query(PractitionerV2).count(),
            "encounters": db.query(EncounterV2).count(),
            "conditions": db.query(ConditionV2).count(),
            "observations": db.query(ObservationV2).count(),
        }
    finally:
        db.close()

    print(f"\nInitial counts: {initial_counts}\n")

    # Test 1: Import Organizations
    print("\n[1/6] Testing Organizations import...")
    try:
        import_organizations(bundle_path)
        db = SessionLocal()
        org_count = db.query(OrganizationV2).count()
        db.close()
        print(f"✓ Organizations imported. Total: {org_count}")
    except Exception as e:
        print(f"❌ Organizations import failed: {e}")
        return False

    # Test 2: Import Patients
    print("\n[2/6] Testing Patients import...")
    try:
        import_patient_from_bundle(bundle_path)
        db = SessionLocal()
        patient_count = db.query(PatientV2).count()
        db.close()
        print(f"✓ Patients imported. Total: {patient_count}")
    except Exception as e:
        print(f"❌ Patients import failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 3: Import Practitioners
    print("\n[3/6] Testing Practitioners import...")
    try:
        import_practitioners(bundle_path)
        db = SessionLocal()
        practitioner_count = db.query(PractitionerV2).count()
        db.close()
        print(f"✓ Practitioners imported. Total: {practitioner_count}")
    except Exception as e:
        print(f"❌ Practitioners import failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 4: Import Encounters
    print("\n[4/6] Testing Encounters import...")
    try:
        import_encounters_from_bundle(bundle_path)
        db = SessionLocal()
        encounter_count = db.query(EncounterV2).count()
        db.close()
        print(f"✓ Encounters imported. Total: {encounter_count}")
    except Exception as e:
        print(f"❌ Encounters import failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 5: Import Conditions
    print("\n[5/6] Testing Conditions import...")
    try:
        import_conditions(bundle_path)
        db = SessionLocal()
        condition_count = db.query(ConditionV2).count()
        db.close()
        print(f"✓ Conditions imported. Total: {condition_count}")
    except Exception as e:
        print(f"❌ Conditions import failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 6: Import Observations
    print("\n[6/6] Testing Observations import...")
    try:
        import_observations(bundle_path)
        db = SessionLocal()
        observation_count = db.query(ObservationV2).count()
        db.close()
        print(f"✓ Observations imported. Total: {observation_count}")
    except Exception as e:
        print(f"❌ Observations import failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Final counts
    db = SessionLocal()
    try:
        final_counts = {
            "organizations": db.query(OrganizationV2).count(),
            "patients": db.query(PatientV2).count(),
            "practitioners": db.query(PractitionerV2).count(),
            "encounters": db.query(EncounterV2).count(),
            "conditions": db.query(ConditionV2).count(),
            "observations": db.query(ObservationV2).count(),
        }

        print("\n" + "=" * 60)
        print("Final Results:")
        print("=" * 60)
        for key in final_counts:
            added = final_counts[key] - initial_counts[key]
            print(
                f"  {key.capitalize()}: {initial_counts[key]} → {final_counts[key]} (+{added})"
            )

        # Verify data integrity
        print("\n" + "=" * 60)
        print("Data Integrity Checks:")
        print("=" * 60)

        # Check if patients have required fields
        patients = db.query(PatientV2).all()
        if patients:
            sample_patient = patients[0]
            print(
                f"✓ Sample Patient: {sample_patient.first_name} {sample_patient.last_name}"
            )
            print(f"  - ID: {sample_patient.id}")
            print(f"  - Identifier: {sample_patient.identifier}")
            print(f"  - Birth Date: {sample_patient.birth_date}")
            print(f"  - Gender: {sample_patient.gender}")

        # Check if encounters reference patients
        encounters = db.query(EncounterV2).all()
        if encounters:
            sample_encounter = encounters[0]
            print(f"\n✓ Sample Encounter:")
            print(f"  - ID: {sample_encounter.id}")
            print(f"  - Patient ID: {sample_encounter.patient_id}")
            print(f"  - Status: {sample_encounter.status}")
            print(f"  - Start Time: {sample_encounter.start_time}")

            # Verify foreign key relationship
            if sample_encounter.patient_id:
                patient = (
                    db.query(PatientV2)
                    .filter(PatientV2.id == sample_encounter.patient_id)
                    .first()
                )
                if patient:
                    print(f"  - Patient exists: ✓")
                else:
                    print(f"  - Patient exists: ❌ (Foreign key issue!)")

    finally:
        db.close()

    print("\n" + "=" * 60)
    print("✅ All import tests completed successfully!")
    print("=" * 60)
    return True


def cleanup_test_db():
    """Remove test database file."""
    test_db_path = Path("./test_imports.db")
    if test_db_path.exists():
        test_db_path.unlink()
        print(f"\n✓ Cleaned up test database: {test_db_path}")


def main():
    """Main test function."""
    # Get sample bundle (we're already in project root)
    bundles_dir = Path("data") / "bundles"

    # Find first bundle file
    bundle_files = list(bundles_dir.glob("*.json"))
    if not bundle_files:
        print("❌ No bundle files found in data/bundles/")
        return 1

    sample_bundle = bundle_files[0]
    print(f"Using sample bundle: {sample_bundle.name}\n")

    try:
        # Setup
        setup_test_db()

        # Run tests
        success = test_import_sample_bundle(sample_bundle)

        if success:
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed. Check errors above.")
            return 1

    except Exception as e:
        print(f"\n❌ Test script failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        cleanup_test_db()


if __name__ == "__main__":
    # Change to project root for data access
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    os.chdir(project_root)

    sys.exit(main())
