import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance.db import db
from academic_governance.models import Lab, LabSystem
from academic_governance.services import academic_service, lab_service
from tests.postgres_test_utils import postgres_test_app


def main() -> None:
    with postgres_test_app():
        email = "student@college.edu"
        academic_service.seed_student_academic_data(email)

        attendance = academic_service.get_student_attendance(email)
        marks = academic_service.get_student_marks(email)
        assert attendance, "Expected seeded attendance records."
        assert marks, "Expected seeded marks records."

        first_subject_id = attendance[0]["subject_id"]
        academic_service.update_attendance(email, first_subject_id, 50, 40)
        updated_attendance = academic_service.get_student_attendance(email)
        changed = next(row for row in updated_attendance if row["subject_id"] == first_subject_id)
        assert changed["total_classes"] == 50, f"Unexpected total classes: {changed['total_classes']}"
        assert changed["attended_classes"] == 40, (
            f"Unexpected attended classes: {changed['attended_classes']}"
        )

        academic_service.update_marks(email, first_subject_id, 20, 15, 35)
        updated_marks = academic_service.get_student_marks(email)
        changed_marks = next(row for row in updated_marks if row["subject_id"] == first_subject_id)
        assert changed_marks["internal_marks"] == 20, f"Unexpected internal marks: {changed_marks['internal_marks']}"

        note_id = academic_service.add_note(first_subject_id, "Unit 1", "notes/unit1.pdf", "admin@college.edu")
        assert note_id > 0, f"Unexpected note id: {note_id}"
        notes = academic_service.get_notes_for_subject(first_subject_id)
        assert any(note["id"] == note_id for note in notes), "Expected new note in subject notes."

        timetable = academic_service.get_full_timetable()
        assert isinstance(timetable, list), "Expected timetable list."

        lab = Lab(lab_name="Computer Lab A")
        db.session.add(lab)
        db.session.flush()
        db.session.add_all(
            [
                LabSystem(lab_id=lab.id, row_label="A", seat_number=1, system_code="PC01", status="working"),
                LabSystem(lab_id=lab.id, row_label="A", seat_number=2, system_code="PC02", status="not_working"),
            ]
        )
        db.session.commit()

        labs = lab_service.get_labs()
        assert labs, "Expected seeded labs."
        layout = lab_service.get_lab_layout(lab.id)
        assert layout is not None, "Expected lab layout."
        summary = lab_service.get_lab_summary()
        assert summary["total"] >= 1, f"Unexpected lab summary: {summary}"

        first_row = next(iter(layout["rows"].values()))
        first_system = first_row[0]
        ok, err = lab_service.update_lab_status(first_system["id"], "working")
        assert ok and not err, f"Expected valid lab status update, got {(ok, err)}"

    print("test_academic_lab_services.py: PASS")


if __name__ == "__main__":
    main()
