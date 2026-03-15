import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance.db import db
from academic_governance.models import Lab, LabSystem
from academic_governance.services import lab_service
from tests.postgres_test_utils import postgres_test_app


def main() -> None:
    with postgres_test_app():
        lab = Lab(lab_name="Computer Lab A")
        db.session.add(lab)
        db.session.flush()
        db.session.add_all(
            [
                LabSystem(
                    lab_id=lab.id,
                    row_label="A",
                    seat_number=1,
                    system_code="PC01",
                    status="working",
                ),
                LabSystem(
                    lab_id=lab.id,
                    row_label="A",
                    seat_number=2,
                    system_code="PC02",
                    status="not_working",
                ),
            ]
        )
        db.session.commit()

        layout = lab_service.get_lab_layout(lab.id)
        assert layout is not None, "Expected lab layout."
        assert layout["lab_name"] == "Computer Lab A"
        assert "A" in layout["rows"], "Expected row A in lab layout."

        first_system = layout["rows"]["A"][0]
        assert "id" in first_system
        assert "system_code" in first_system
        assert "status" in first_system

        empty = lab_service.get_lab_layout(999999)
        assert empty is None, "Unknown lab should return None"

    print("test_lab_systems.py: PASS")


if __name__ == "__main__":
    main()
