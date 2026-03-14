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
        lab = Lab(lab_name="Lab A")
        db.session.add(lab)
        db.session.flush()

        first = LabSystem(
            lab_id=lab.id,
            row_label="A",
            seat_number=1,
            system_code="PC01",
            status="working",
        )
        second = LabSystem(
            lab_id=lab.id,
            row_label="A",
            seat_number=2,
            system_code="PC02",
            status="not_working",
        )
        db.session.add_all([first, second])
        db.session.commit()

        labs = lab_service.get_labs()
        assert any(item["lab_name"] == "Lab A" for item in labs), f"Expected Lab A in labs list, got {labs}"

        ok_update, err_update = lab_service.update_lab_status(first.id, "working")
        assert ok_update and err_update == "", f"Expected update success, got {(ok_update, err_update)}"

        ok_invalid, err_invalid = lab_service.update_lab_status(first.id, "Invalid")
        assert (not ok_invalid) and err_invalid, f"Expected invalid status failure, got {(ok_invalid, err_invalid)}"

        summary = lab_service.get_lab_summary()
        assert isinstance(summary, dict), f"Expected dict summary, got {type(summary)}"
        for key in ("total", "working", "not_working"):
            assert key in summary, f"Missing summary key: {key}"

    print("test_labs.py: PASS")


if __name__ == "__main__":
    main()
