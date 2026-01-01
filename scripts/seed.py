from app.core.database import SessionLocal, Base, engine
from app.models.models import PolicyVersion
import yaml
from pathlib import Path

Base.metadata.create_all(bind=engine)
db = SessionLocal()

for policy_file in Path("policies").glob("*.yaml"):
    data = yaml.safe_load(policy_file.read_text())
    record = PolicyVersion(name=data.get("name", policy_file.stem), version=data.get("version", "v1"), rules=data)
    db.add(record)
db.commit()
db.close()
print("Seeded policies")
