"""Lab domain service layer."""

from __future__ import annotations

from datetime import datetime, timezone

from academic_governance.repositories import lab_repository


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_labs() -> list[dict]:
    labs = lab_repository.list_labs()
    return [{"id": lab.id, "lab_name": lab.lab_name} for lab in labs]


def get_lab_layout(lab_id: int) -> dict | None:
    lab = lab_repository.get_lab(lab_id)
    if lab is None:
        return None
    systems = lab_repository.list_lab_systems(lab_id)
    rows: dict[str, list[dict]] = {}
    for system in systems:
        rows.setdefault(system.row_label, []).append(
            {
                "id": system.id,
                "row_label": system.row_label,
                "seat_number": system.seat_number,
                "system_code": system.system_code,
                "status": system.status,
            }
        )
    return {"id": lab.id, "lab_name": lab.lab_name, "rows": rows}


def get_lab_summary() -> dict[str, int]:
    total = lab_repository.count_lab_systems()
    working = lab_repository.count_lab_systems_by_status("working")
    not_working = lab_repository.count_lab_systems_by_status("not_working")
    return {"total": total, "working": working, "not_working": not_working}


def update_lab_status(system_id: int, status: str) -> tuple[bool, str]:
    if status not in ("working", "not_working"):
        return False, "Invalid status value."
    system = lab_repository.get_lab_system(system_id)
    if system is None:
        return False, "Lab system not found."
    lab_repository.update_lab_system_status(system, status, _now())
    return True, ""