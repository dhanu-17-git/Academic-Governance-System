"""Preload sample PostgreSQL data for demos and local testing."""

from __future__ import annotations

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from academic_governance import create_app
from academic_governance.db import db
from academic_governance.models import CampusUpdate, Lab, LabSystem
from academic_governance.services import (
    academic_service,
    complaint_service,
    notification_service,
)


def _seed_campus_updates() -> None:
    if db.session.query(CampusUpdate).count() > 0:
        return

    db.session.add_all(
        [
            CampusUpdate(
                title="Library Hours Extended",
                content="The main library will remain open until midnight during exam weeks.",
                category="Facility",
            ),
            CampusUpdate(
                title="New Parking Rules",
                content="Updated parking regulations take effect next Monday.",
                category="Parking",
            ),
            CampusUpdate(
                title="WiFi Upgrade Complete",
                content="Campus-wide WiFi has been upgraded for faster speeds.",
                category="Infrastructure",
            ),
        ]
    )
    db.session.commit()


def _seed_labs() -> None:
    if db.session.query(Lab).count() > 0:
        return

    labs = [
        ("Computer Lab A", [("A", 4), ("B", 4)]),
        ("Computer Lab B", [("A", 4), ("B", 4)]),
        ("Computer Lab C", [("A", 5)]),
    ]
    pc_index = 1

    for lab_name, row_specs in labs:
        lab = Lab(lab_name=lab_name)
        db.session.add(lab)
        db.session.flush()

        for row_label, seats in row_specs:
            for seat_number in range(1, seats + 1):
                status = "not_working" if pc_index % 5 == 0 else "working"
                db.session.add(
                    LabSystem(
                        lab_id=lab.id,
                        row_label=row_label,
                        seat_number=seat_number,
                        system_code=f"PC{pc_index:02d}",
                        status=status,
                    )
                )
                pc_index += 1

    db.session.commit()


def seed() -> None:
    app = create_app()

    with app.app_context():
        print("Seeding complaints...")
        complaint_one = complaint_service.create_complaint(
            category="Academic",
            description=(
                "The schedule for next semester's computer architecture course "
                "conflicts with the algorithms lab."
            ),
            student_email="student@college.edu",
        )
        complaint_service.create_complaint(
            category="Infrastructure",
            description="The air conditioning in the main auditorium is not working.",
            student_email="student@college.edu",
        )
        complaint_three = complaint_service.create_complaint(
            category="Hostel",
            description="Wi-Fi connectivity in block B is unstable during evening hours.",
            student_email="student@college.edu",
        )
        complaint_service.create_complaint(
            category="Other",
            description="Need more vegetarian options in the campus cafeteria.",
            student_email="student2@college.edu",
        )

        print("Updating complaint statuses...")
        complaint_service.update_complaint_status(
            complaint_one,
            "Under Review",
            "We are reviewing the timetable conflict and will adjust lab timings.",
        )
        complaint_service.update_complaint_status(
            complaint_three,
            "Under Review",
            "Networking team is investigating the unstable connection.",
        )
        complaint_service.update_complaint_status(
            complaint_three,
            "Resolved",
            "The block B routers were updated and connectivity has stabilized.",
        )

        print("Seeding feedback and notifications...")
        complaint_service.create_feedback(
            "Course Curriculum",
            4,
            "The new AI electives are great, but they need more practical assignments.",
            "Positive",
        )
        complaint_service.create_feedback(
            "Campus Facilities",
            3,
            "The library is good but needs more copies of reference textbooks.",
            "Neutral",
        )
        complaint_service.create_feedback(
            "Administration",
            2,
            "The fee payment portal is often down on the last day.",
            "Negative",
        )
        notification_service.create_notification(
            "Career Fair",
            "Annual placement drive registrations are now open.",
            "/placement/drives",
        )

        print("Seeding academic data...")
        academic_service.seed_student_academic_data("john.doe@college.edu")
        academic_service.seed_student_academic_data("student@college.edu")

        print("Seeding campus updates and lab inventory...")
        _seed_campus_updates()
        _seed_labs()

        print("Database seeding completed successfully.")


if __name__ == "__main__":
    seed()
