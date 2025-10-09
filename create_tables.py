from app.database import Base, engine
from app.models import Condition, Encounter, Patient, Practitioner

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
