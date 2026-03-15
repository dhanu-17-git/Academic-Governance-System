import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance.db import db
from academic_governance.models import Subject
from academic_governance.services import academic_service
from tests.postgres_test_utils import postgres_test_app


def main() -> None:
    with postgres_test_app():
        subject = Subject(subject_name="Test Subject", credits=3)
        db.session.add(subject)
        db.session.commit()

        note_id = academic_service.add_note(
            subject_id=subject.id,
            title="Test Note",
            file_path="notes/test.pdf",
            admin_email="admin@test.com",
        )
        assert isinstance(note_id, int) and note_id > 0, (
            f"Unexpected note_id: {note_id}"
        )

        notes = academic_service.get_notes_for_subject(subject.id)
        assert any(int(note["id"]) == note_id for note in notes), (
            "Inserted note not found in subject notes."
        )

        deleted_file_path = academic_service.delete_note(note_id)
        assert deleted_file_path == "notes/test.pdf", (
            f"Unexpected deleted file path: {deleted_file_path}"
        )

    print("test_notes.py: PASS")


if __name__ == "__main__":
    main()
