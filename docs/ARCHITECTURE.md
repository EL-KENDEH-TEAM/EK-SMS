# EK-SMS Architecture

## Overview

EK-SMS is a modular monolith built with a clear separation between frontend and backend, designed to scale and potentially evolve into microservices.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                               │
│                    (Browser/Mobile)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                         │
│                    (apps/web - Port 3000)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Pages     │  │ Components  │  │   Hooks     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│                   (apps/api - Port 8002)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Routers   │  │  Services   │  │Repositories │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌───────────┐   ┌───────────┐   ┌───────────┐
       │PostgreSQL │   │   Redis   │   │  Mailpit  │
       │Port 5440  │   │ Port 6380 │   │ Port 8025 │
       └───────────┘   └───────────┘   └───────────┘
```

## Backend Architecture

### Layered Architecture

```
Request → Router → Service → Repository → Database
              ↓
           Schemas (validation)
```

| Layer          | Responsibility                  |
| -------------- | ------------------------------- |
| **Router**     | HTTP handling, request/response |
| **Service**    | Business logic, orchestration   |
| **Repository** | Database operations             |
| **Schemas**    | Data validation (Pydantic)      |
| **Models**     | Database structure (SQLAlchemy) |

### Module Structure

```
apps/api/src/app/
├── core/                 # Shared core functionality
│   ├── config.py         # Environment configuration
│   ├── database.py       # Database connection
│   ├── redis.py          # Redis connection
│   └── security.py       # Auth utilities
│
└── modules/              # Feature modules
    ├── auth/             # Authentication
    ├── users/            # User management
    ├── academic/         # Schools, classes, terms
    ├── grades/           # Grade management (event-sourced)
    ├── documents/        # Document management
    ├── notifications/    # Notifications
    ├── audit/            # Audit logging
    └── shared/           # Shared utilities
```

## Frontend Architecture

### Folder Structure

```
apps/web/src/
├── app/                  # Next.js App Router pages
├── components/           # Reusable components
│   ├── ui/               # Base UI components
│   └── features/         # Feature-specific components
├── hooks/                # Custom React hooks
├── lib/                  # Utilities and API client
├── stores/               # State management
└── types/                # TypeScript types
```

## Key Design Decisions

### 1. Modular Monolith

We chose a modular monolith over microservices because:

- Simpler to develop and deploy initially
- Clear module boundaries allow future extraction
- Reduced operational complexity

### 2. Event Sourcing for Grades

Grades use event sourcing to:

- Maintain complete audit trail
- Prevent unauthorized modifications
- Enable grade history reconstruction

### 3. Async Python

All database operations are async for:

- Better performance under load
- Non-blocking I/O operations
- Scalability

## Database Design

### Core Tables

| Table        | Purpose                          |
| ------------ | -------------------------------- |
| users        | User accounts and authentication |
| students     | Student profiles                 |
| teachers     | Teacher profiles                 |
| classes      | Class definitions                |
| subjects     | Subject catalog                  |
| grade_events | Immutable grade records          |
| audit_logs   | System audit trail               |

### Grade Event Sourcing

```
┌─────────────────────────────────────────┐
│             grade_events                 │
├─────────────────────────────────────────┤
│ id          │ UUID                       │
│ student_id  │ UUID                       │
│ subject_id  │ UUID                       │
│ event_type  │ SUBMITTED/MODIFIED/FINAL   │
│ score       │ DECIMAL                    │
│ recorded_by │ UUID (teacher)             │
│ recorded_at │ TIMESTAMP                  │
│ metadata    │ JSONB                      │
└─────────────────────────────────────────┘
```

## Security

### Authentication Flow

1. User submits credentials
2. Server validates and issues JWT
3. Client stores token securely
4. Token included in API requests
5. Server validates token on each request

### Two-Factor Authentication

- TOTP-based (Google Authenticator compatible)
- Required for admin roles
- Optional for other users

## Deployment

### Environments

| Environment | API            | Frontend       |
| ----------- | -------------- | -------------- |
| Development | localhost:8002 | localhost:3000 |
| Staging     | Railway        | Vercel         |
| Production  | Railway        | Vercel         |
