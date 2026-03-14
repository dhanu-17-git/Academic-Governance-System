import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance.services import auth_service, notification_service
from tests.postgres_test_utils import postgres_test_app


def main() -> None:
    with postgres_test_app():
        auth_service.store_otp("student@college.edu", "123456", "2099-01-01 00:00:00")
        otp_record = auth_service.get_otp_record("student@college.edu")
        assert otp_record is not None, "Expected OTP record to exist."
        assert otp_record["otp"] == "123456", f"Unexpected OTP value: {otp_record['otp']}"
        assert otp_record["attempts"] == 0, f"Unexpected initial attempts: {otp_record['attempts']}"

        auth_service.increment_otp_attempts("student@college.edu")
        otp_record = auth_service.get_otp_record("student@college.edu")
        assert otp_record["attempts"] == 1, f"Unexpected OTP attempts after increment: {otp_record['attempts']}"

        auth_service.record_rate_limit_attempt("login", "127.0.0.1")
        auth_service.record_rate_limit_attempt("login", "127.0.0.1")
        count = auth_service.get_rate_limit_count("login", "127.0.0.1", 60)
        assert count == 2, f"Unexpected rate limit count: {count}"

        auth_service.reset_rate_limit("login", "127.0.0.1")
        count = auth_service.get_rate_limit_count("login", "127.0.0.1", 60)
        assert count == 0, f"Expected rate limit reset to clear entries, got: {count}"

        notification_id = notification_service.create_notification(
            "Maintenance Window",
            "The portal will be briefly unavailable tonight.",
            "/status",
        )
        assert isinstance(notification_id, int) and notification_id > 0, (
            f"Unexpected notification id: {notification_id}"
        )

        notifications = notification_service.get_notifications(limit=5)
        assert notifications, "Expected at least one notification."
        assert notifications[0]["title"] == "Maintenance Window", (
            f"Unexpected latest notification title: {notifications[0]['title']}"
        )

    print("test_auth_notifications.py: PASS")


if __name__ == "__main__":
    main()
