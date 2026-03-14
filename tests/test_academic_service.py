import io
import os
import sys

from werkzeug.datastructures import FileStorage

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance import config
from academic_governance.repositories import user_repository
from academic_governance.services import academic_service


class TestAcademicService:
    def test_dashboard_context_seeds_student_academic_data(self, app):
        with app.app_context():
            context = academic_service.get_student_dashboard_context("student@college.edu")

        assert context["has_academic_data"] is True
        assert context["attendance_records"]
        assert context["timetable"]
        assert context["overall_attendance_pct"] >= 0

    def test_apply_attendance_and_mark_updates_modify_existing_records(self, app):
        email = "student@college.edu"
        with app.app_context():
            academic_service.seed_student_academic_data(email)
            attendance_record = academic_service.get_student_attendance(email)[0]
            mark_record = academic_service.get_student_marks(email)[0]

            attendance_updated = academic_service.apply_attendance_updates(
                {
                    f"total_{email}_{attendance_record['subject_id']}": "60",
                    f"attended_{email}_{attendance_record['subject_id']}": "48",
                }
            )
            marks_updated = academic_service.apply_mark_updates(
                {
                    f"internal_{email}_{mark_record['subject_id']}": "29",
                    f"assignment_{email}_{mark_record['subject_id']}": "18",
                    f"exam_{email}_{mark_record['subject_id']}": "44",
                }
            )

            updated_attendance = academic_service.get_student_attendance_record(
                email,
                attendance_record["subject_id"],
            )
            updated_marks = next(
                item
                for item in academic_service.get_student_marks(email)
                if item["subject_id"] == mark_record["subject_id"]
            )

        assert attendance_updated == 1
        assert marks_updated == 1
        assert updated_attendance["total_classes"] == 60
        assert updated_attendance["attended_classes"] == 48
        assert updated_marks["internal_marks"] == 29
        assert updated_marks["assignment_marks"] == 18
        assert updated_marks["exam_marks"] == 44

    def test_bulk_create_users_from_csv_creates_and_skips_expected_rows(self, app):
        csv_bytes = io.BytesIO(
            b"email,role\nstudent1@college.edu,student\nadmin1@college.edu,admin\ninvalid-email,student\n"
        )
        file_storage = FileStorage(stream=csv_bytes, filename="users.csv", content_type="text/csv")

        with app.app_context():
            result = academic_service.bulk_create_users_from_csv(file_storage)
            created_student = user_repository.get_user_by_email("student1@college.edu")
            created_admin = user_repository.get_user_by_email("admin1@college.edu")

        assert result["success"] is True
        assert result["created"] == 2
        assert result["error_count"] == 1
        assert created_student is not None
        assert created_admin is not None