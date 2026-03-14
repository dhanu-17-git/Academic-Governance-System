import io
import os
import sys
from pathlib import Path

from werkzeug.datastructures import FileStorage

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance import config
from academic_governance.services import complaint_service
from tests.helpers import managed_temp_dir


PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n"


def _set_upload_folder(monkeypatch, upload_root: Path) -> None:
    monkeypatch.setattr(config, "UPLOAD_FOLDER", str(upload_root))


class TestComplaintService:
    def test_create_complaint_tracks_owner_and_stats(self, app):
        with app.app_context():
            complaint_id = complaint_service.create_complaint(
                "Academic",
                "Need help with timetable clash.",
                "student@college.edu",
            )
            complaint = complaint_service.get_complaint_by_id(complaint_id)
            owner = complaint_service.get_complaint_owner(complaint_id)
            stats = complaint_service.get_student_complaints("student@college.edu")

        assert complaint["status"] == "Submitted"
        assert complaint["student_email"] == "student@college.edu"
        assert owner == "student@college.edu"
        assert stats == {"total": 1, "pending": 1, "resolved": 0}

    def test_update_complaint_status_enforces_valid_transitions(self, app):
        with app.app_context():
            complaint_id = complaint_service.create_complaint(
                "Infrastructure",
                "Classroom fan is not working.",
                "student@college.edu",
            )

            invalid_success, invalid_error = complaint_service.update_complaint_status(
                complaint_id,
                "Resolved",
            )
            review_success, _ = complaint_service.update_complaint_status(
                complaint_id,
                "Under Review",
                "Team is checking the issue.",
            )
            resolved_success, _ = complaint_service.update_complaint_status(
                complaint_id,
                "Resolved",
                "Issue fixed.",
            )
            updated = complaint_service.get_complaint_by_id(complaint_id)
            stats = complaint_service.get_student_complaints("student@college.edu")

        assert invalid_success is False
        assert "Cannot move" in invalid_error
        assert review_success is True
        assert resolved_success is True
        assert updated["status"] == "Resolved"
        assert updated["admin_response"] == "Issue fixed."
        assert stats == {"total": 1, "pending": 0, "resolved": 1}

    def test_update_complaint_status_sends_email_when_configured(self, app, monkeypatch):
        delivered = {}
        monkeypatch.setattr(complaint_service.email_service, "is_email_configured", lambda: True)

        def fake_send(recipient, complaint_id, status, *, admin_response=""):
            delivered["recipient"] = recipient
            delivered["complaint_id"] = complaint_id
            delivered["status"] = status
            delivered["admin_response"] = admin_response

        monkeypatch.setattr(
            complaint_service.email_service,
            "send_complaint_status_email",
            fake_send,
        )

        with app.app_context():
            complaint_id = complaint_service.create_complaint(
                "Placement",
                "Placement cell response delayed.",
                "student@college.edu",
            )
            success, _ = complaint_service.update_complaint_status(
                complaint_id,
                "Under Review",
                "We have escalated this to the team.",
            )

        assert success is True
        assert delivered == {
            "recipient": "student@college.edu",
            "complaint_id": complaint_id,
            "status": "Under Review",
            "admin_response": "We have escalated this to the team.",
        }

    def test_create_complaint_with_upload_moves_file_into_complaint_folder(self, app, monkeypatch):
        with managed_temp_dir("complaint_upload_") as upload_root:
            _set_upload_folder(monkeypatch, upload_root)
            file_storage = FileStorage(
                stream=io.BytesIO(PDF_BYTES),
                filename="evidence.pdf",
                content_type="application/pdf",
            )

            with app.app_context():
                complaint_id = complaint_service.create_complaint_with_upload(
                    "Academic",
                    "Uploaded proof for the issue.",
                    "student@college.edu",
                    file_storage,
                )
                complaint = complaint_service.get_complaint_by_id(complaint_id)

            assert complaint["file_path"] is not None
            assert complaint_id in complaint["file_path"]
            complaint_dir = upload_root / complaint_id
            assert complaint_dir.exists()
            saved_files = list(complaint_dir.iterdir())
            assert len(saved_files) == 1
            assert saved_files[0].read_bytes() == PDF_BYTES