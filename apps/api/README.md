# EK-SMS API

Backend API for the EL-KENDEH Smart School Management System.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Cache**: Redis
- **Authentication**: JWT + 2FA (TOTP)

## Development

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis 7+

### Setup

1. Create a virtual environment:
```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
   pip install -e ".[dev]"
```

3. Run the development server:
```bash
   pnpm dev
```

4. Open http://localhost:8000/docs for API documentation.

## Project Structure
```
src/app/
├── core/           # Core utilities, config, security
├── modules/        # Feature modules (modular monolith)
│   ├── auth/       # Authentication & sessions
│   ├── users/      # User management & RBAC
│   ├── academic/   # Students, classes, subjects
│   ├── grades/     # Grade management (event-sourced)
│   ├── documents/  # Report cards, transcripts
│   ├── notifications/  # Alerts, emails, SMS
│   ├── audit/      # Logging & forensics
│   └── shared/     # Shared utilities
└── main.py         # Application entry point
```