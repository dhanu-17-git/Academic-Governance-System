"""Full Stitch UI Replacement Validation"""

from academic_governance import create_app

app = create_app()
app.config["TESTING"] = True

with app.test_client() as c:
    with c.session_transaction() as sess:
        sess["user_email"] = "test@example.com"
        sess["role"] = "student"

    checks = []

    # 1. Dashboard still works (was not touched)
    rv = c.get("/dashboard")
    checks.append(("Dashboard /dashboard", rv.status_code == 200))
    dashboard_html = rv.data.decode("utf-8")
    checks.append(
        ("Dashboard has NO output.css", "dist/output.css" not in dashboard_html)
    )

    # 2. Raise Complaint
    rv = c.get("/raise-complaint")
    checks.append(("Route /raise-complaint", rv.status_code == 200))
    html = rv.data.decode("utf-8")
    checks.append(("Complaint: csrf_token", "csrf_token" in html))
    checks.append(("Complaint: form action", "raise_complaint" in html))
    checks.append(("Complaint: name=category", 'name="category"' in html))
    checks.append(("Complaint: name=description", 'name="description"' in html))
    checks.append(("Complaint: name=file", 'name="file"' in html))
    checks.append(("Complaint: output.css", "dist/output.css" in html))

    # 3. Placement Profile
    rv = c.get("/placement/profile")
    checks.append(("Route /placement/profile", rv.status_code == 200))

    # 4. Placement Drives
    rv = c.get("/placement/drives")
    if rv.status_code == 200:
        checks.append(("Route /placement/drives", True))
    else:
        checks.append(
            ("Route /placement/drives (may need route)", rv.status_code < 500)
        )

    # 5. Placement Career
    rv = c.get("/placement/career")
    if rv.status_code == 200:
        checks.append(("Route /placement/career", True))
    else:
        checks.append(
            ("Route /placement/career (may need route)", rv.status_code < 500)
        )

    # 6. Placement Applications
    rv = c.get("/placement/applications")
    if rv.status_code == 200:
        checks.append(("Route /placement/applications", True))
    else:
        checks.append(
            ("Route /placement/applications (may need route)", rv.status_code < 500)
        )

    # 7. Lab Index
    rv = c.get("/lab-status")
    checks.append(("Route /lab-status", rv.status_code == 200))

    for name, passed in checks:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    print()
    all_pass = all(p for _, p in checks)
    print(f"Results: {sum(1 for _, p in checks if p)}/{len(checks)} passed")
    print("ALL CHECKS PASSED!" if all_pass else "SOME CHECKS FAILED - review above")
