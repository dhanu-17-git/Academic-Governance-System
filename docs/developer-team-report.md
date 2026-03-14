# Academic Governance System - Developer Team Report

**Project Overview**
The Academic Governance System is a comprehensive campus governance portal developed to streamline academic, administrative, and student life workflows. It serves as a unified platform for students and administrators, handling everything from academic tracking (attendance, marks, timetables, materials) and lab resource management to grievance redressal (complaints) and career services (placement portal). 

## 1. Technical Architecture & Tech Stack

**Backend**
- **Framework:** Python / Flask
- **Architecture:** Blueprint-based modular architecture (`student.py`, `admin.py`, `auth.py`, `health.py`). Core logic is intentionally decoupled into dedicated services (`academic_service`, `complaint_service`, `lab_service`, `auth_service`, `notification_service`).
- **Database:** PostgreSQL only. Object-Relational Mapping (ORM) provided by SQLAlchemy, and database migrations managed via Alembic.
- **Dependency Management:** Managed purely with `uv` (`pyproject.toml` and `uv.lock`) for determinism and high performance. `requirements.txt` is exported strictly for compatibility scenarios.

**Frontend**
- **Templating:** Jinja2
- **Styling:** Vanilla CSS generated via Tailwind CSS using utility-first patterns.
- **UI Frameworks:** Integrated heavily with Stitch UI components for a modern, responsive, glass-morphism aesthetic. No heavyweight monolithic JS frameworks are forced on the client, maximizing load speed.
- **Interactivity:** Lightweight Vanilla JavaScript, supplemented by micro-animations and responsive flex/grid layouts.

**Infrastructure & Deployment**
- **Dockerized Environment:** The platform uses Docker Compose, offering separate compositions for `staging` and `production`.
- **Server:** Gunicorn in production handling WSGI routing.
- **Reverse Proxy / TLS:** Nginx is optionally deployed via a Docker compose profile (`--profile proxy`) to intercept traffic on 80/443 and terminate SSL using externally provided `fullchain.pem` / `privkey.pem` Let's Encrypt certificates.
- **Monitoring:** Integrated Sentry error tracking bootstrapped on app launch.
- **CI/CD:** Automated testing and syntax validations run on GitHub Actions.

## 2. Core Modules & Features

**Authentication & Security**
- **Google OAuth 2.0:** Primary authentication mechanism mapping university Google Workspace accounts to internal student/admin roles.
- **OTP Fallback:** Standard email OTP verification system, using SMTP (SendGrid, AWS SES, or Gmail with app passwords).
- **Security Hardening (Phase 4):**
  - Robust Rate Limiting applied to login (5 requests / 60s max per IP), OTPs, and complaint submissions to mitigate abuse and bruteforce vectors.
  - Granular authorization guards preventing privilege escalation between standard student and administrative views.
  - Strict input sanitization applied to all text fields.
  - Strong MIME-type validation and isolated subdirectories (`uploads/`) for file uploads.

**Academic Tracking Module**
- **Dashboards:** Dynamic overviews for students of their grades (Internal, Assignment, Exams), class attendance percentages, and current syllabus/course plan.
- **Materials:** Secure document storage serving class notes linked explicitly to subjects. Admin bulk-upload capabilities.
- **Timetables:** Structurally normalized scheduling tool managing `room`, `day_of_week`, `subject_id`, and `time_slot`.

**Complaints & Governance Module**
- **Submission:** Allows students to lodge complaints categorized by department (Academic, Parking, Cleaning, Placement, etc.) including supporting image or document attachments.
- **Status Lifecycle:** Admins review, respond, and change resolution statuses. Every status update actively pushes a notification email back to the originating student.
- **Sentiment Analysis:** All academic feedback is routed through a localized rule-based sentiment classifier (Positive/Negative/Neutral) to generate an overarching institutional satisfaction index.

**Lab & Resource Management**
- **Visual Matrix Tracker:** Visual floor plans of labs demonstrating precise seat labels and system statuses (Working / Not Working).
- **Maintenance Overviews:** Administrators click defective systems to mark them out-of-order instantly in the DB, reflecting in real-time across student screens.

**Placement Module**
- **Career Preparation:** Dedicated sections for student profile building, job drive listings, application tracking, and career resources.

**Admin Advanced Capabilities**
- **Bulk Import Pipelines:** Rapid onboarding via bulk CSV upload tools parsing students directly into local tables.
- **At-Risk Analysis Tools:** Dedicated administrative panels automatically flag struggling demographics (e.g., highly negative sentiments, severe attendance deficits) based on centralized logic.
- **Notification Broadcaster:** Custom campus updates pushed uniformly to the global dashboard feed.

## 3. Current State & Handoff Readiness

The system stands fully developed, hardened, and deployment-ready. Recent security audits and remediation cycles have successfully removed known vulnerabilities (e.g. revoked exposed keys, patched misconfigured routing, sanitized arbitrary inputs, established the health endpoint `/health` for orchestrator probes).

The single outstanding factor before public launch is purely ops-side operational inputs on the target server:
- Generation of the production `SECRET_KEY`.
- Registration of the live domain with Google Cloud for the OAuth Client ID/Secret.
- Providing valid App Password SMTP strings for operational mail.
- Generating and lodging valid TLS certificates into `/deployment/certs`. 

All code is fully documented locally, and database tables will spin up successfully on initial `flask db upgrade` in the production container.
