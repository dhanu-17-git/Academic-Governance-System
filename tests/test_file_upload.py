import os
import sys
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance import config
from academic_governance.services import academic_service, complaint_service
from tests.helpers import login_as, managed_temp_dir


PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n"
TEXT_BYTES = b"Course material for module 1\n"


def _set_upload_folder(app, monkeypatch, upload_root: Path) -> None:
    monkeypatch.setattr(config, "UPLOAD_FOLDER", str(upload_root))
    app.config["UPLOAD_FOLDER"] = str(upload_root)


def test_complaint_upload_owner_can_access_file(app_with_client, monkeypatch):
    app, client = app_with_client

    with managed_temp_dir("uploads_owner_") as upload_root:
        _set_upload_folder(app, monkeypatch, upload_root)

        with app.app_context():
            complaint_id = complaint_service.create_complaint(
                "Academic",
                "Projector is not working.",
                "owner@college.edu",
            )

        complaint_dir = upload_root / complaint_id
        complaint_dir.mkdir(parents=True, exist_ok=True)
        file_path = complaint_dir / "evidence.pdf"
        file_path.write_bytes(PDF_BYTES)

        login_as(client, "owner@college.edu", config.ROLE_STUDENT)
        response = client.get(f"/uploads/{complaint_id}/evidence.pdf")

        assert response.status_code == 200
        assert response.get_data() == PDF_BYTES


def test_complaint_upload_blocks_other_students_but_allows_admin(
    app_with_client,
    monkeypatch,
):
    app, client = app_with_client

    with managed_temp_dir("uploads_admin_") as upload_root:
        _set_upload_folder(app, monkeypatch, upload_root)

        with app.app_context():
            complaint_id = complaint_service.create_complaint(
                "Infrastructure",
                "Broken window.",
                "owner@college.edu",
            )

        complaint_dir = upload_root / complaint_id
        complaint_dir.mkdir(parents=True, exist_ok=True)
        (complaint_dir / "proof.pdf").write_bytes(PDF_BYTES)

        login_as(client, "other@college.edu", config.ROLE_STUDENT)
        blocked = client.get(f"/uploads/{complaint_id}/proof.pdf")
        assert blocked.status_code == 403

        login_as(client, "admin@college.edu", config.ROLE_ADMIN)
        allowed = client.get(f"/uploads/{complaint_id}/proof.pdf")
        assert allowed.status_code == 200
        assert allowed.get_data() == PDF_BYTES


def test_notes_access_requires_enrollment(app_with_client, monkeypatch):
    app, client = app_with_client

    with managed_temp_dir("uploads_notes_") as upload_root:
        _set_upload_folder(app, monkeypatch, upload_root)

        notes_dir = upload_root / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        note_file = notes_dir / "module1.txt"
        note_file.write_bytes(TEXT_BYTES)

        with app.app_context():
            academic_service.seed_student_academic_data("enrolled@college.edu")
            subject_id = academic_service.get_all_subjects()[0]["id"]
            academic_service.add_note(
                subject_id,
                "Module 1",
                "notes/module1.txt",
                "admin@college.edu",
            )

        login_as(client, "enrolled@college.edu", config.ROLE_STUDENT)
        enrolled_response = client.get("/uploads/notes/module1.txt")
        assert enrolled_response.status_code == 200
        assert enrolled_response.get_data() == TEXT_BYTES

        login_as(client, "not-enrolled@college.edu", config.ROLE_STUDENT)
        blocked_response = client.get("/uploads/notes/module1.txt")
        assert blocked_response.status_code == 403
