import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance.services import complaint_service
from tests.postgres_test_utils import postgres_test_app


def main() -> None:
    with postgres_test_app():
        complaint_id = complaint_service.create_complaint(
            category="Academic",
            description="Projector not working in classroom.",
            student_email="student@college.edu",
            url="https://example.com/details",
        )
        assert complaint_id.startswith("CMP"), (
            f"Unexpected complaint id: {complaint_id}"
        )

        stats = complaint_service.get_student_complaints("student@college.edu")
        assert stats["total"] == 1, f"Unexpected total complaints: {stats}"
        assert stats["pending"] == 1, f"Unexpected pending complaints: {stats}"
        assert stats["resolved"] == 0, f"Unexpected resolved complaints: {stats}"

        complaint = complaint_service.get_complaint_by_id(complaint_id)
        assert complaint is not None, "Expected complaint lookup to succeed."
        assert complaint["student_email"] == "student@college.edu", (
            f"Unexpected complaint owner: {complaint['student_email']}"
        )

        ok, err = complaint_service.update_complaint_status(
            complaint_id,
            "Under Review",
            "We are checking the issue.",
        )
        assert ok and not err, f"Expected valid status transition, got {(ok, err)}"

        ok, err = complaint_service.update_complaint_status(
            complaint_id,
            "Submitted",
            "",
        )
        assert not ok and err, "Expected invalid reverse transition to fail."

        complaint_service.create_feedback("Mathematics", 4, "good support", "Positive")
        avg_rating = complaint_service.get_average_rating()
        assert avg_rating == 4.0, f"Unexpected average rating: {avg_rating}"

        sentiments = complaint_service.get_sentiment_distribution()
        assert sentiments, "Expected sentiment distribution rows."

        complaint_service.log_admin_action("admin@college.edu", "Updated complaint")

    print("test_complaint_service.py: PASS")


if __name__ == "__main__":
    main()
