# Academic Governance System

A production-oriented academic operations platform built with **Flask**, **PostgreSQL**, **SQLAlchemy**, and **Alembic**. The system models a modern campus backend with secure complaint handling, OTP-based authentication, academic tracking, lab management, placement workflows, and admin analytics.

---

## Overview

The Academic Governance System streamlines academic operations for students, faculty, and administrators. It provides a unified platform for managing complaints, tracking attendance and marks, booking lab resources, coordinating placement drives, and delivering real-time notifications — all secured behind OTP and OAuth authentication.

---

## Tech Stack

| Layer         | Technology                                      |
|---------------|--------------------------------------------------|
| Backend       | Flask, Flask-WTF, Flask-SQLAlchemy, Flask-Migrate |
| Database      | PostgreSQL, SQLAlchemy ORM, Alembic migrations    |
| Auth          | OTP (email), Google OAuth via Authlib             |
| Frontend      | Jinja2 templates, TailwindCSS, static assets      |
| Deployment    | Docker, Docker Compose, Gunicorn, Nginx           |
| Dependency Mgmt | uv                                              |
| Observability | Structured logging, Sentry SDK                   |
| Testing       | pytest with PostgreSQL-backed integration tests   |
| CI/CD         | GitHub Actions                                    |

---

## Features

- **Student Dashboard** — Attendance, marks, timetable, course materials, and academic progress at a glance.
- **Complaint Management** — Anonymous-feeling complaint flow with status tracking, admin responses, file attachments, and email notifications.
- **Lab Resource Tracking** — View and manage lab systems, equipment status, and booking availability.
- **Placement Portal** — Browse active placement drives, manage placement profiles, and track application status.
- **Admin Analytics** — Administrative dashboards for attendance management, marks entry, bulk student creation, and at-risk student visibility.
- **Authentication** — Dual-mode auth with email OTP and Google OAuth sign-in for accelerated onboarding.
- **Notifications** — Real-time notification system for complaint updates, academic alerts, and system messages.
- **AI Chatbot** — Gemini-powered chatbot for student support queries.

---

## Architecture

The application follows a **blueprint-based Flask architecture** with clear separation of concerns:

```
Client Request
  → Flask Blueprint (Route Layer)
    → Service Layer (Business Logic)
      → Repository Layer (Data Access)
        → SQLAlchemy Models
          → PostgreSQL
```

- **Routes** handle HTTP requests, form validation, and response rendering.
- **Services** encapsulate business logic, orchestrate repository calls, and enforce rules.
- **Repositories** provide a clean data-access abstraction over SQLAlchemy models.
- **Models** define the database schema using SQLAlchemy ORM.

The app factory pattern (`create_app()`) initialises extensions, registers blueprints, and configures middleware.

---

## Local Setup

### Prerequisites

- Python 3.11+
- PostgreSQL running locally
- [uv](https://docs.astral.sh/uv/) package manager

### Quick Start

```bash
# Install uv (if not already installed)
pip install uv

# Install all dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your database URL and secret key

# Run database migrations
uv run flask --app wsgi:app db upgrade

# Start the development server
uv run flask run
```

The application will be available at `http://localhost:5000`.

---

## Project Structure

```
academic-governance-system/
│
├── academic_governance/          # Main application package
│   ├── __init__.py               # App factory (create_app)
│   ├── config.py                 # Configuration management
│   ├── db.py                     # Database initialisation
│   ├── models.py                 # SQLAlchemy ORM models
│   ├── auth/                     # Authentication helpers
│   ├── routes/                   # Blueprint route handlers
│   ├── services/                 # Business logic layer
│   ├── repositories/             # Data access layer
│   └── utils/                    # Logging, Sentry, request middleware
│
├── templates/                    # Jinja2 HTML templates
├── static/                       # CSS, JS, images
├── tests/                        # pytest test suite
├── migrations/                   # Alembic migration scripts
│
├── docs/                         # Project documentation
│   ├── developer-team-report.md
│   ├── architecture.md
│   └── screenshots/
│
├── deployment/                   # Deployment configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── gunicorn.conf.py
│   ├── nginx.conf
│   └── backup.sh
│
├── .github/workflows/ci.yml     # GitHub Actions CI pipeline
├── pyproject.toml                # Project metadata & dependencies
├── uv.lock                      # Locked dependency versions
├── wsgi.py                       # WSGI entrypoint (Gunicorn)
├── .env.example                  # Environment variable template
├── .gitignore                    # Git ignore rules
├── LICENSE                       # MIT License
└── README.md                     # This file
```

---

## Security Features

- **Input Validation** — Server-side form validation with Flask-WTF and custom validators for file uploads, email formats, and text sanitisation.
- **Rate Limiting** — Database-backed rate limiting on login, OTP, complaint, and feedback endpoints.
- **Secure Uploads** — File type validation, size limits, and secure filename handling for complaint attachments.
- **OAuth Authentication** — Google OAuth integration via Authlib with CSRF state verification.
- **Session Security** — Secure session cookies, CSRF protection, and hardened security headers.
- **Observability** — Structured logging, request tracing, and optional Sentry error reporting.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.