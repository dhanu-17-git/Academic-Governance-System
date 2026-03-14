# Architecture — Academic Governance System

## Overview

The Academic Governance System is built as a modular Flask application following a **layered architecture** with clear separation of concerns. The application uses the **app factory pattern** and organises features into Flask **blueprints**.

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Client (Browser)                  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────┐
│              Nginx Reverse Proxy (optional)          │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Gunicorn WSGI Server                    │
│              (wsgi.py → create_app())                │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  Flask Application                   │
│  ┌─────────────────────────────────────────────┐    │
│  │           Middleware / Extensions            │    │
│  │  (CSRF, Session, Logging, Rate Limiting)    │    │
│  └──────────────────────┬──────────────────────┘    │
│                         │                            │
│  ┌──────────────────────▼──────────────────────┐    │
│  │          Route Layer (Blueprints)            │    │
│  │  auth.py │ student.py │ admin.py │ health.py│    │
│  └──────────────────────┬──────────────────────┘    │
│                         │                            │
│  ┌──────────────────────▼──────────────────────┐    │
│  │            Service Layer                     │    │
│  │  auth_service │ academic_service │ complaint │    │
│  │  email_service│ lab_service│ chatbot_service │    │
│  └──────────────────────┬──────────────────────┘    │
│                         │                            │
│  ┌──────────────────────▼──────────────────────┐    │
│  │          Repository Layer                    │    │
│  │  user_repo │ academic_repo │ complaint_repo │    │
│  │  lab_repo                                    │    │
│  └──────────────────────┬──────────────────────┘    │
│                         │                            │
│  ┌──────────────────────▼──────────────────────┐    │
│  │          SQLAlchemy ORM Models               │    │
│  │  (models.py → User, Complaint, Lab, etc.)   │    │
│  └──────────────────────┬──────────────────────┘    │
└─────────────────────────┼────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────┐
│                  PostgreSQL Database                  │
└──────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

### Route Layer (`academic_governance/routes/`)

Each blueprint handles a domain of the application:

| Blueprint     | File          | Responsibility                                          |
|---------------|---------------|---------------------------------------------------------|
| `auth_bp`     | `auth.py`     | Login, OTP verification, Google OAuth, logout           |
| `student_bp`  | `student.py`  | Student dashboard, academics, complaints, placements    |
| `admin_bp`    | `admin.py`    | Admin dashboard, student management, analytics          |
| `health_bp`   | `health.py`   | Health check endpoint (`/health`)                       |
| `chatbot_bp`  | `chatbot.py`  | AI chatbot interface                                    |

Routes handle: HTTP request/response, form validation, session checks, and template rendering.

### Service Layer (`academic_governance/services/`)

Services encapsulate business logic and orchestrate calls to repositories:

- **auth_service** — OTP generation, verification, and session management
- **academic_service** — Attendance, marks, timetable, course materials
- **complaint_service** — Complaint CRUD, status transitions, ownership enforcement
- **email_service** — SMTP email delivery for OTP and notifications
- **lab_service** — Lab resource queries and management
- **notification_service** — In-app notification delivery
- **chatbot_service** — Gemini API integration for AI responses
- **security** — Rate limiting and security enforcement
- **validators** — Input validation and sanitisation

### Repository Layer (`academic_governance/repositories/`)

Repositories provide a clean data-access abstraction:

- **user_repository** — User CRUD and lookup operations
- **academic_repository** — Academic data queries (attendance, marks, timetable)
- **complaint_repository** — Complaint persistence and queries
- **lab_repository** — Lab system data access

### Models (`academic_governance/models.py`)

SQLAlchemy ORM models define the database schema. Alembic manages schema migrations via the `migrations/` directory.

---

## App Factory Pattern

The application uses Flask's app factory pattern in `academic_governance/__init__.py`:

```python
def create_app():
    app = Flask(__name__)
    # Load configuration
    # Initialise extensions (SQLAlchemy, Migrate, CSRF)
    # Register blueprints
    # Configure middleware (logging, request tracking)
    return app
```

Entry points:
- **Development**: `app.py` or `uv run flask run`
- **Production**: `wsgi.py` → Gunicorn

---

## Authentication Flow

```
User → Login Page → Enter Email
  → OTP generated and emailed
  → User enters OTP → Verified against DB
  → Session created → Dashboard

User → Google Sign-In
  → OAuth redirect to Google
  → Callback with token → User lookup/creation
  → Session created → Dashboard
```

---

## Deployment Architecture

```
Docker Compose
  ├── web (Flask + Gunicorn)
  ├── postgres (PostgreSQL 15)
  └── nginx (reverse proxy, optional profile)
```

The `Dockerfile` uses a multi-stage build (builder + runtime) for minimal image size. Gunicorn serves the WSGI application with 4 workers by default.

---

## Key Design Decisions

1. **Blueprint-based modularisation** — Each feature domain is isolated in its own blueprint for maintainability.
2. **Three-layer architecture** — Route → Service → Repository separation keeps business logic testable and data access swappable.
3. **Database-backed rate limiting** — No external Redis dependency; rate limits are enforced through PostgreSQL.
4. **Dual authentication** — OTP for security, OAuth for convenience.
5. **App factory pattern** — Enables multiple app instances for testing and configuration flexibility.
