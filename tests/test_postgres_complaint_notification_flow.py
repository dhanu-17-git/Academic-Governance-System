import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance.services import complaint_service, notification_service
from tests.postgres_test_utils import postgres_test_app


def main() -> None:
    with postgres_test_app():
        complaint_id = complaint_service.create_complaint(
            category="Infrastructure",
            description="Projector is offline.",
            student_email="student@college.edu",
        )
        complaint = complaint_service.get_complaint_by_id(complaint_id)
        assert complaint is not None
        assert complaint["student_email"] == "student@college.edu"

        ok, err = complaint_service.update_complaint_status(
            complaint_id,
            "Under Review",
            "Investigating now.",
        )
        assert ok and not err

        notification_id = notification_service.create_notification(
            "Lab maintenance",
            "Lab A will reopen tomorrow.",
        )
        assert notification_id > 0
        notifications = notification_service.get_notifications(limit=5)
        assert notifications and notifications[0]["title"] == "Lab maintenance"

    print("test_postgres_complaint_notification_flow.py: PASS")


if __name__ == "__main__":
    main()
