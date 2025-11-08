"""
Import all data into Cloud SQL database.
Supports both local file system and Cloud Storage as data sources.
Run this script to import all FHIR bundles in the correct order.
"""
import os
import sys
import tempfile
from pathlib import Path

# Add backend/src to Python path
script_dir = Path(__file__).parent
backend_src = script_dir.parent
sys.path.insert(0, str(backend_src))

from import_organizations_v2 import import_path as import_organizations
from import_patients_v2 import import_folder as import_patients
from import_practitioners_v2 import import_path as import_practitioners
from import_encounters_v2 import import_path as import_encounters
from import_conditions_v2 import import_path as import_conditions
from import_observations_v2 import import_path as import_observations


def download_from_cloud_storage(bucket_name: str, prefix: str = "bundles/") -> Path:
    """
    Download files from Cloud Storage to a temporary directory.
    
    Args:
        bucket_name: Name of the Cloud Storage bucket
        prefix: Prefix/path in the bucket (default: "bundles/")
    
    Returns:
        Path to temporary directory containing downloaded files
    """
    try:
        from google.cloud import storage
    except ImportError:
        raise ImportError(
            "google-cloud-storage is required for Cloud Storage support. "
            "Install it with: pip install google-cloud-storage"
        )
    
    print(f"📦 Downloading files from gs://{bucket_name}/{prefix}...")
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="gcs_bundles_"))
    print(f"   Temporary directory: {temp_dir}")
    
    # Download files from Cloud Storage
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    downloaded_count = 0
    for blob in blobs:
        if blob.name.endswith('.json'):
            # Create local file path
            local_path = temp_dir / Path(blob.name).name
            # Download the file
            blob.download_to_filename(str(local_path))
            downloaded_count += 1
            if downloaded_count % 100 == 0:
                print(f"   Downloaded {downloaded_count} files...")
    
    print(f"✓ Downloaded {downloaded_count} files to {temp_dir}")
    return temp_dir


def get_bundles_directory() -> Path:
    """
    Get the bundles directory path.
    Supports both local files and Cloud Storage.
    
    Returns:
        Path to directory containing bundle files
    """
    # Check if using Cloud Storage
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if bucket_name:
        print("📦 Using Cloud Storage as data source")
        prefix = os.getenv("GCS_BUNDLES_PREFIX", "bundles/")
        return download_from_cloud_storage(bucket_name, prefix)
    
    # Default to local files
    print("📁 Using local file system as data source")
    project_root = Path(__file__).parent.parent.parent.parent
    bundles_dir = project_root / "data" / "bundles"
    
    if not bundles_dir.exists():
        raise FileNotFoundError(
            f"Bundles directory not found: {bundles_dir}\n"
            "Either set GCS_BUCKET_NAME environment variable for Cloud Storage, "
            "or ensure data/bundles directory exists locally."
        )
    
    return bundles_dir


def main():
    """Import all data in the correct order."""
    try:
        # Get bundles directory (local or Cloud Storage)
        bundles_dir = get_bundles_directory()
        
        # Count bundles
        bundle_count = len(list(bundles_dir.glob("*.json")))
        
        print("=" * 80)
        print("IMPORTING DATA TO CLOUD SQL")
        print("=" * 80)
        print(f"Database: {os.getenv('DATABASE_URL', 'Not set - using default')}")
        print(f"Data source: {bundles_dir}")
        print(f"Bundles to process: {bundle_count}")
        print("=" * 80)
        
        if bundle_count == 0:
            print("⚠️  No JSON files found. Nothing to import.")
            return 1
        
        # Step 1: Import Organizations (no dependencies)
        print("\n[1/6] Importing Organizations...")
        print("-" * 80)
        import_organizations(bundles_dir)
        print("✓ Organizations import completed\n")
        
        # Step 2: Import Patients (no dependencies)
        print("\n[2/6] Importing Patients...")
        print("-" * 80)
        import_patients(bundles_dir)
        print("✓ Patients import completed\n")
        
        # Step 3: Import Practitioners (may reference organizations)
        print("\n[3/6] Importing Practitioners...")
        print("-" * 80)
        import_practitioners(bundles_dir)
        print("✓ Practitioners import completed\n")
        
        # Step 4: Import Encounters (references patients, practitioners, organizations)
        print("\n[4/6] Importing Encounters...")
        print("-" * 80)
        import_encounters(bundles_dir)
        print("✓ Encounters import completed\n")
        
        # Step 5: Import Conditions (references patients)
        print("\n[5/6] Importing Conditions...")
        print("-" * 80)
        import_conditions(bundles_dir)
        print("✓ Conditions import completed\n")
        
        # Step 6: Import Observations (references patients, encounters)
        print("\n[6/6] Importing Observations...")
        print("-" * 80)
        import_observations(bundles_dir)
        print("✓ Observations import completed\n")
        
        print("=" * 80)
        print("✅ ALL DATA IMPORTED SUCCESSFULLY!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Run check_data_quality.py to verify the import")
        print("2. Test your API endpoints to confirm data is accessible")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Change to project root for data access (if using local files)
    if not os.getenv("GCS_BUCKET_NAME"):
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        os.chdir(project_root)
    
    sys.exit(main())

