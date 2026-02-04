"""
Data Quality Check Script
Analyzes imported data to check for null values, redundant columns, and data quality issues.
"""
import os
import sys
from pathlib import Path
from collections import defaultdict
from sqlalchemy import inspect, func
from sqlalchemy.orm import Session

# Add backend/src to Python path
script_dir = Path(__file__).parent
backend_src = script_dir.parent
sys.path.insert(0, str(backend_src))

from api.v2.database import SessionLocal, engine
from api.v2.models import (
    ConditionV2,
    EncounterV2,
    ObservationV2,
    OrganizationV2,
    PatientV2,
    PractitionerV2,
)

# Map model classes to their display names
MODELS = {
    "patients": PatientV2,
    "organizations": OrganizationV2,
    "practitioners": PractitionerV2,
    "encounters": EncounterV2,
    "conditions": ConditionV2,
    "observations": ObservationV2,
}


def get_table_columns(model_class):
    """Get all columns for a model."""
    return inspect(model_class).columns


def check_null_values(db: Session, model_class, table_name: str):
    """Check null values for each column in a table."""
    print(f"\n{'='*80}")
    print(f"Table: {table_name.upper()}")
    print(f"{'='*80}")
    
    # Get total row count
    total_rows = db.query(model_class).count()
    print(f"Total Rows: {total_rows}")
    
    if total_rows == 0:
        print("⚠️  Table is empty!")
        return
    
    columns = get_table_columns(model_class)
    null_stats = {}
    
    print(f"\n{'Column Name':<40} {'Null Count':<15} {'Null %':<15} {'Status'}")
    print("-" * 80)
    
    for column in columns:
        column_name = column.name
        # Count nulls
        null_count = db.query(func.count()).filter(
            column.is_(None)
        ).scalar()
        
        null_percent = (null_count / total_rows * 100) if total_rows > 0 else 0
        null_stats[column_name] = {
            "null_count": null_count,
            "null_percent": null_percent,
            "total_rows": total_rows
        }
        
        # Status indicator
        if null_percent == 0:
            status = "✓ All populated"
        elif null_percent < 10:
            status = "⚠️  Mostly populated"
        elif null_percent < 50:
            status = "⚠️  Many nulls"
        else:
            status = "❌ Mostly null (redundant?)"
        
        print(f"{column_name:<40} {null_count:<15} {null_percent:>6.2f}%      {status}")
    
    return null_stats


def check_foreign_key_integrity(db: Session):
    """Check if foreign key relationships are valid."""
    print(f"\n{'='*80}")
    print("FOREIGN KEY INTEGRITY CHECKS")
    print(f"{'='*80}")
    
    # Check encounters -> patients
    encounters = db.query(EncounterV2).all()
    orphaned_encounters = 0
    for enc in encounters:
        if enc.patient_id:
            patient = db.query(PatientV2).filter(PatientV2.id == enc.patient_id).first()
            if not patient:
                orphaned_encounters += 1
    
    if orphaned_encounters > 0:
        print(f"❌ Found {orphaned_encounters} encounters with invalid patient_id")
    else:
        print("✓ All encounters have valid patient references")
    
    # Check encounters -> practitioners
    encounters_with_practitioners = db.query(EncounterV2).filter(
        EncounterV2.practitioner_id.isnot(None)
    ).count()
    total_encounters = db.query(EncounterV2).count()
    
    if total_encounters > 0:
        practitioner_percent = (encounters_with_practitioners / total_encounters) * 100
        print(f"ℹ️  {encounters_with_practitioners}/{total_encounters} encounters have practitioners ({practitioner_percent:.1f}%)")
    
    # Check encounters -> organizations
    encounters_with_orgs = db.query(EncounterV2).filter(
        EncounterV2.organization_id.isnot(None)
    ).count()
    
    if total_encounters > 0:
        org_percent = (encounters_with_orgs / total_encounters) * 100
        print(f"ℹ️  {encounters_with_orgs}/{total_encounters} encounters have organizations ({org_percent:.1f}%)")
    
    # Check conditions -> patients
    conditions = db.query(ConditionV2).all()
    orphaned_conditions = 0
    for cond in conditions:
        if cond.patient_id:
            patient = db.query(PatientV2).filter(PatientV2.id == cond.patient_id).first()
            if not patient:
                orphaned_conditions += 1
    
    if orphaned_conditions > 0:
        print(f"❌ Found {orphaned_conditions} conditions with invalid patient_id")
    else:
        print("✓ All conditions have valid patient references")
    
    # Check observations -> patients
    observations = db.query(ObservationV2).all()
    orphaned_observations = 0
    for obs in observations:
        if obs.patient_id:
            patient = db.query(PatientV2).filter(PatientV2.id == obs.patient_id).first()
            if not patient:
                orphaned_observations += 1
    
    if orphaned_observations > 0:
        print(f"❌ Found {orphaned_observations} observations with invalid patient_id")
    else:
        print("✓ All observations have valid patient references")


def check_data_completeness(db: Session):
    """Check overall data completeness."""
    print(f"\n{'='*80}")
    print("DATA COMPLETENESS SUMMARY")
    print(f"{'='*80}")
    
    total_stats = defaultdict(int)
    
    for table_name, model_class in MODELS.items():
        total_rows = db.query(model_class).count()
        total_stats[table_name] = total_rows
        
        columns = get_table_columns(model_class)
        non_nullable_cols = [col for col in columns if not col.nullable]
        
        # Check if required columns have data
        missing_required = 0
        for col in non_nullable_cols:
            null_count = db.query(func.count()).filter(
                col.is_(None)
            ).scalar()
            if null_count > 0:
                missing_required += 1
        
        status = "✓" if missing_required == 0 else "❌"
        print(f"{status} {table_name.capitalize():<20} Rows: {total_rows:<10} Required columns missing: {missing_required}")
    
    print(f"\n{'Total Records:':<30} {sum(total_stats.values()):,}")


def identify_redundant_columns(db: Session):
    """Identify columns that are mostly null (potentially redundant)."""
    print(f"\n{'='*80}")
    print("POTENTIALLY REDUNDANT COLUMNS (>50% null)")
    print(f"{'='*80}")
    
    redundant_found = False
    
    for table_name, model_class in MODELS.items():
        total_rows = db.query(model_class).count()
        if total_rows == 0:
            continue
        
        columns = get_table_columns(model_class)
        redundant_cols = []
        
        for column in columns:
            if column.nullable:  # Only check nullable columns
                null_count = db.query(func.count()).filter(
                    column.is_(None)
                ).scalar()
                null_percent = (null_count / total_rows * 100) if total_rows > 0 else 0
                
                if null_percent > 50:
                    redundant_cols.append((column.name, null_percent))
        
        if redundant_cols:
            redundant_found = True
            print(f"\n{table_name.upper()}:")
            for col_name, null_pct in sorted(redundant_cols, key=lambda x: x[1], reverse=True):
                print(f"  - {col_name:<40} {null_pct:>6.2f}% null")
    
    if not redundant_found:
        print("✓ No redundant columns found (all columns have <50% null values)")


def show_sample_data(db: Session):
    """Show sample data from each table."""
    print(f"\n{'='*80}")
    print("SAMPLE DATA")
    print(f"{'='*80}")
    
    # Sample patient
    patient = db.query(PatientV2).first()
    if patient:
        print(f"\nSample Patient:")
        print(f"  ID: {patient.id}")
        print(f"  Name: {patient.first_name} {patient.last_name}")
        print(f"  Identifier: {patient.identifier}")
        print(f"  Birth Date: {patient.birth_date}")
        print(f"  Gender: {patient.gender}")
        print(f"  Phone: {patient.phone or 'N/A'}")
        print(f"  Email: {patient.email or 'N/A'}")
        print(f"  Address: {patient.address_line or 'N/A'}, {patient.city or 'N/A'}")
    
    # Sample encounter
    encounter = db.query(EncounterV2).first()
    if encounter:
        print(f"\nSample Encounter:")
        print(f"  ID: {encounter.id}")
        print(f"  Patient ID: {encounter.patient_id}")
        print(f"  Status: {encounter.status}")
        print(f"  Start Time: {encounter.start_time}")
        print(f"  End Time: {encounter.end_time or 'N/A'}")
        print(f"  Practitioner ID: {encounter.practitioner_id or 'N/A'}")
        print(f"  Organization ID: {encounter.organization_id or 'N/A'}")
    
    # Sample condition
    condition = db.query(ConditionV2).first()
    if condition:
        print(f"\nSample Condition:")
        print(f"  ID: {condition.id}")
        print(f"  Patient ID: {condition.patient_id}")
        print(f"  Code: {condition.code or 'N/A'}")
        print(f"  Display: {condition.display or 'N/A'}")
        print(f"  Onset Time: {condition.onset_time or 'N/A'}")


def main():
    """Main function to run all data quality checks."""
    print("=" * 80)
    print("DATA QUALITY CHECK REPORT")
    print("=" * 80)
    print(f"Database: {os.getenv('DATABASE_URL', 'Not set')}")
    
    db = SessionLocal()
    try:
        # Check each table for null values
        all_stats = {}
        for table_name, model_class in MODELS.items():
            stats = check_null_values(db, model_class, table_name)
            if stats:
                all_stats[table_name] = stats
        
        # Check foreign key integrity
        check_foreign_key_integrity(db)
        
        # Check data completeness
        check_data_completeness(db)
        
        # Identify redundant columns
        identify_redundant_columns(db)
        
        # Show sample data
        show_sample_data(db)
        
        print(f"\n{'='*80}")
        print("✅ Data quality check completed!")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"\n❌ Error during data quality check: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

