# Academic Governance System

[![CI](https://github.com/dhanu-17-git/Academic-Governance-System/actions/workflows/ci.yml/badge.svg)](https://github.com/dhanu-17-git/Academic-Governance-System/actions/workflows/ci.yml)
![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=flat&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-style academic governance platform built with Flask, PostgreSQL, OAuth authentication, and containerized deployment using Docker. The system models a modern campus backend with secure complaint handling, academic tracking, lab management, placement workflows, and admin analytics.

---

## Overview

The Academic Governance System streamlines academic operations for students, faculty, and administrators. It provides a unified platform for managing complaints, tracking attendance and marks, booking lab resources, coordinating placement drives, and delivering real-time notifications — all secured behind OTP and OAuth authentication.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Authentication Flow](#authentication-flow)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Environment Variables](#environment-variables)
- [Local Development Setup](#local-development-setup)
- [Docker Setup](#docker-setup)
- [Running Tests](#running-tests)
- [CI/CD Pipeline](#cicd-pipeline)
- [Security Features](#security-features)
- [Demo Login](#demo-login-development-mode)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## System Architecture

The system follows a layered architecture using Flask Blueprints for routing, service logic for business operations, and repository-based patterns for database interaction.

```mermaid
graph TD
    User["User Browser"] --> Flask["Flask Application (Gunicorn)"]
    
    subgraph App ["Application Layers"]
        AuthLayer["Authentication Layer"]
        ServiceLayer["Service Layer"]
        RepoLayer["Repository Layer"]
    end
    
    Flask --> AuthLayer
    AuthLayer --> EmailOTP["Email + OTP Login"]
    AuthLayer --> GoogleOAuth["Google OAuth Login"]
    
    Flask --> ServiceLayer
    ServiceLayer --> AcademicService["Academic Service"]
    ServiceLayer --> ComplaintService["Complaint Service"]
    ServiceLayer --> LabService["Lab Resource Service"]
    ServiceLayer --> ChatbotService["Chatbot Service"]
    
    ServiceLayer --> RepoLayer
    RepoLayer --> SAModels["SQLAlchemy Models"]
    
    RepoLayer --> DB[("PostgreSQL Database")]
```

*Note: The system diagram below illustrates the high-level flow:*

```text
User Browser
↓
Flask Application (Gunicorn)
│
├── Authentication Layer
│   ├─ Email + OTP Login
│   └─ Google OAuth Login
│
├── Service Layer
│   ├─ Academic Service
│   ├─ Complaint Service
│   ├─ Lab Resource Service
│   └─ Chatbot Service
│
├── Repository Layer
│   └─ SQLAlchemy Models
│
↓
PostgreSQL Database
```

---

## Quick Start

Clone the repository and start the application locally:

```bash
git clone https://github.com/dhanu-17-git/Academic-Governance-System.git
cd Academic-Governance-System
```

Install dependencies:

```bash
pip install uv
uv sync
```

Run database migrations:

```bash
uv run flask db upgrade
```

Start the application:

```bash
uv run flask run
```

Then open: [http://127.0.0.1:5000](http://127.0.0.1:5000)


---




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

## Authentication

The platform implements a **Hybrid Authentication System** to balance security and convenience:

• **Email + Password login with OTP verification**  
• **Google OAuth login for instant sign-in**  
• **Unified authentication handler using `_complete_login()`**  
• **Role-based dashboard routing (Student / Admin)**

### Login Methods

| Method | Description |
|------|-------------|
| Email + OTP | Secure login using email verification code |
| Google OAuth | Instant login using Google account |

---

## Authentication Flow

### Email Login Flow

1. User enters email and password
2. OTP is generated and printed in the development terminal
3. User enters OTP
4. OTP is validated
5. `_complete_login()` creates the session and redirects to the dashboard

### Google Login Flow

1. User clicks "Continue with Google"
2. OAuth authentication occurs through Google
3. Verified email is returned to the application
4. `_complete_login()` creates the session and redirects to the dashboard


---

## Backend Architecture
The project follows a **layered backend architecture** for maintainability and testability.

```text
academic_governance/
│
├── routes/        # HTTP endpoints (Flask Blueprints)
├── services/      # Business logic layer
├── repositories/  # Database access layer
├── models.py      # SQLAlchemy ORM models
├── utils/         # Logging, monitoring, helpers
│
deployment/
│
├── Dockerfile
├── docker-compose.yml
└── nginx.conf
```

**Flow:** Request → Route → Service → Repository → Database



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

## Screenshots

Screenshots of the system interface are available in:

`docs/screenshots/`

---


---

## Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask cryptographic key | Yes | `super-secret-key` |
| `DATABASE_URL` | PostgreSQL connection string | Yes | `postgresql+psycopg://user:pass@localhost:5432/db` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | Yes | `12345-xyz.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | Yes | `--------` |
| `SMTP_USERNAME` | SMTP User for emails | Yes | `alerts@campus.edu` |
| `SMTP_PASSWORD` | SMTP Password | Yes | `smtp-secret-pass` |
| `SENTRY_DSN` | Sentry DSN for error tracking | No | `https://abc@o123.ingest.sentry.io/456` |


---

## Local Development Setup

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

## Docker Setup

To run the full stack (Flask app, PostgreSQL, Nginx reverse proxy) in containers:

```bash
docker-compose up --build
```

**Running migrations inside Docker:**

```bash
docker-compose exec web uv run flask db upgrade
```


---

## Running Tests

Run the test suite using `uv`:

```bash
uv run pytest tests/
```

*Note: Integration tests require a running PostgreSQL database.*


---

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration. On every push and pull request, it automatically runs:

- **Ruff** lint and format checks
- **pytest** test suite
- **Security scans**

This ensures code quality and reliability before merging changes into the main branch.


---

## Security Features

• Google OAuth 2.0 authentication  
• OTP-based email verification  
• Rate limiting on authentication endpoints  
• CSRF protection via Flask-WTF  
• Secure session cookies and hardened security headers  
• File upload validation and sanitisation  
• Structured logging with optional Sentry monitoring


---

## Roadmap

- Mobile companion application
- REST API endpoints for third-party integrations
- Advanced analytics dashboards
- Role-based reporting tools
- Redis-backed caching and rate limiting


---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes following conventional commits (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


---

## Acknowledgements

- Flask
- PostgreSQL
- SQLAlchemy
- Authlib
- Tailwind CSS
- Google Gemini API


---

## Demo Login (Development Mode)

Email: `student@college.edu`  
Password: `demo@123`  

After login, the OTP will appear in the server terminal.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
