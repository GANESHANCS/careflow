from typing import List
from sqlalchemy.orm import Session
from backend.app.db.models.indicator import Indicator
from backend.app.services.data_pipeline.indicator_catalog import STANDARD_INDICATORS


def seed_standard_indicators(db: Session) -> List[Indicator]:
    """
    Seeds the standard core HMIS indicators into the database.
    Idempotent: skips indicators already present.
    """
    seeded = []
    for code, meta in STANDARD_INDICATORS.items():
        existing = db.query(Indicator).filter(Indicator.code == code).first()
        if not existing:
            ind_id = f"IND_{code}"
            indicator = Indicator(
                id=ind_id,
                code=code,
                name=meta.name,
                category=meta.category,
                unit=meta.unit,
                description=f"Standard HMIS indicator for {meta.name}",
                source_system="HMIS",
                active=True
            )
            db.add(indicator)
            seeded.append(indicator)
        else:
            seeded.append(existing)

    db.commit()
    return seeded
