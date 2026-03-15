"""Lab repository layer."""

from __future__ import annotations

from datetime import datetime

from academic_governance.db import db
from academic_governance.models import Lab, LabSystem


def list_labs() -> list[Lab]:
    return db.session.query(Lab).order_by(Lab.lab_name).all()


def get_lab(lab_id: int) -> Lab | None:
    return db.session.get(Lab, lab_id)


def list_lab_systems(lab_id: int) -> list[LabSystem]:
    return (
        db.session.query(LabSystem)
        .filter(LabSystem.lab_id == lab_id)
        .order_by(LabSystem.row_label, LabSystem.seat_number)
        .all()
    )


def count_lab_systems() -> int:
    return db.session.query(LabSystem).count()


def count_lab_systems_by_status(status: str) -> int:
    return db.session.query(LabSystem).filter(LabSystem.status == status).count()


def get_lab_system(system_id: int) -> LabSystem | None:
    return db.session.get(LabSystem, system_id)


def update_lab_system_status(
    system: LabSystem, status: str, last_updated: datetime
) -> LabSystem:
    system.status = status
    system.last_updated = last_updated
    db.session.commit()
    return system
