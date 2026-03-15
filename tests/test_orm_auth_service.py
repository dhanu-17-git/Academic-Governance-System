import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance.services import auth_service
from tests.postgres_test_utils import postgres_test_app


def main() -> None:
    with postgres_test_app():
        auth_service.store_otp("student@college.edu", "654321", "2099-01-01 00:00:00")
        otp_record = auth_service.get_otp_record("student@college.edu")
        assert otp_record is not None, "Expected OTP record to exist."
        assert otp_record["otp"] == "654321", (
            f"Unexpected OTP value: {otp_record['otp']}"
        )
        assert otp_record["attempts"] == 0, (
            f"Unexpected initial attempts: {otp_record['attempts']}"
        )

        auth_service.increment_otp_attempts("student@college.edu")
        otp_record = auth_service.get_otp_record("student@college.edu")
        assert otp_record["attempts"] == 1, (
            f"Unexpected OTP attempts after increment: {otp_record['attempts']}"
        )

        auth_service.record_rate_limit_attempt("login", "127.0.0.1")
        auth_service.record_rate_limit_attempt("login", "127.0.0.1")
        count = auth_service.get_rate_limit_count("login", "127.0.0.1", 60)
        assert count == 2, f"Unexpected rate limit count: {count}"

        auth_service.reset_rate_limit("login", "127.0.0.1")
        count = auth_service.get_rate_limit_count("login", "127.0.0.1", 60)
        assert count == 0, f"Expected rate limit reset to clear entries, got: {count}"

        auth_service.delete_otp("student@college.edu")
        assert auth_service.get_otp_record("student@college.edu") is None

    print("test_orm_auth_service.py: PASS")


if __name__ == "__main__":
    main()
