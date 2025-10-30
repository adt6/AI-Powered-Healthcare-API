from api.v1.database import Base, engine
from api.v1.models import Condition, Encounter, Patient, Practitioner

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
