# EK-SMS Team Guide

> **For Product Lead & Development Team**
> This document explains the architectural decisions, patterns, and guidelines for working on EK-SMS.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Why These Architectural Choices?](#why-these-architectural-choices)
3. [Protected Files (Do Not Touch)](#protected-files-do-not-touch)
4. [Development Workflow](#development-workflow)
5. [Quick Reference for Team Members](#quick-reference-for-team-members)

---

## Project Overview

**EK-SMS** (EL-KENDEH Smart School Management System) is a transparent, tamper-proof grade management system designed to prevent grade manipulation and ensure academic integrity.

### Tech Stack at a Glance

| Layer          | Technology            | Why                                                 |
| -------------- | --------------------- | --------------------------------------------------- |
| **Frontend**   | Next.js 16 + React 19 | Server-side rendering, great DX, TypeScript support |
| **Backend**    | FastAPI (Python)      | Async performance, automatic API docs, type hints   |
| **Database**   | PostgreSQL            | ACID compliance, reliability, JSON support          |
| **Cache**      | Redis                 | Session management, rate limiting, caching          |
| **Build Tool** | Turborepo             | Fast builds, caching, monorepo orchestration        |

---

## Why These Architectural Choices?

### 1. Why Monorepo with Turborepo?

**What is it?**
A monorepo means all our code (frontend, backend, shared packages) lives in ONE repository instead of separate repos.

**Why we chose it:**

| Benefit                    | Explanation                                                                 |
| -------------------------- | --------------------------------------------------------------------------- |
| **Single source of truth** | All code in one place - no version mismatches between frontend and backend  |
| **Shared code**            | Types, configs, and utilities can be shared without publishing npm packages |
| **Atomic changes**         | One PR can update both frontend AND backend together                        |
| **Easier onboarding**      | New devs clone ONE repo, not three                                          |
| **Coordinated releases**   | Deploy frontend and backend together when needed                            |

**Why Turborepo specifically?**

- **Caching**: If code hasn't changed, Turbo skips rebuilding (shows "FULL TURBO")
- **Parallelization**: Builds independent packages simultaneously
- **Task orchestration**: Ensures `shared-types` builds before `web` needs it

**Important Note TO TEAM:**

> "We use a monorepo so everyone works from the same codebase. Turborepo makes builds fast by caching unchanged code. Run `pnpm build` from root - never cd into individual apps to build."

---

### 2. Why Modular Monolithic Architecture?

**What is it?**
The API is organized into independent **modules** (auth, users, grades, etc.) that could theoretically become microservices later, but run as ONE application now.

**Why NOT microservices from day one?**

| Microservices                      | Modular Monolith (Our Choice) |
| ---------------------------------- | ----------------------------- |
| Complex deployment (many services) | Simple deployment (one API)   |
| Network latency between services   | In-process function calls     |
| Distributed debugging nightmare    | Single application logs       |
| Team of 20+ needed                 | Perfect for team of 4         |
| Premature optimization             | Right-sized for our stage     |

**Why NOT a traditional monolith?**
Traditional monoliths become "big balls of mud" - everything tangled together. Our modules have **clear boundaries**:

```
modules/
├── auth/       # Authentication only
├── users/      # User management only
├── grades/     # Grade management only
└── ...each module is self-contained
```

**IMPORTANT NOTE TO TEAM:**

> "Each module is like a mini-application. Work inside your module's folder. Don't import directly from other modules' internal files - use their public exports."

---

### 3. Why Event Sourcing for Grades?

**What is it?**
Instead of storing just the current grade, we store EVERY change as an immutable event.

**Traditional approach (BAD for us):**

```
grades table:
| student_id | subject | score |
| 123        | Math    | 85    |  ← Can be silently changed to 95!
```

**Event sourcing approach (GOOD):**

```
grade_events table:
| id | student | subject | score | event_type | recorded_by | timestamp | hash |
| 1  | 123     | Math    | 85    | DRAFT      | teacher_1   | 10:00     | a1b2 |
| 2  | 123     | Math    | 85    | SUBMIT     | teacher_1   | 10:05     | c3d4 |
| 3  | 123     | Math    | 85    | LOCK       | admin       | 11:00     | e5f6 |
| 4  | 123     | Math    | 90    | MODIFY_REQ | teacher_1   | 12:00     | g7h8 |  ← Requires approval!
```

**Why this matters for EK-SMS:**

- **Audit trail**: We can prove WHO changed WHAT and WHEN
- **Tamper-proof**: Events are immutable - you can't delete history
- **Accountability**: Every action is recorded with the user who did it
- **Legal compliance**: Full history for any disputes

**IMPORTANT NOTE TO TEAM:**

> "Never UPDATE a grade record. Always INSERT a new event. The current grade is calculated from the event history. This is how we prevent corruption."

---

### 4. Why Husky + Commitlint + lint-staged?

**What are they?**

| Tool            | Purpose                                        |
| --------------- | ---------------------------------------------- |
| **Husky**       | Runs scripts automatically when you commit     |
| **lint-staged** | Runs linters only on files you changed (fast!) |
| **commitlint**  | Enforces consistent commit message format      |

**Why enforce commit messages?**

Bad commits:

```
"fixed stuff"
"wip"
"asdfasdf"
"changes"
```

Good commits (conventional commits):

```
"feat(grades): add grade submission workflow"
"fix(auth): resolve token refresh race condition"
"docs(api): update authentication endpoint docs"
```

**Benefits:**

- **Automatic changelogs**: Tools can generate release notes from commits
- **Easy git history**: `git log` actually tells you what happened
- **Better code review**: Reviewers understand changes at a glance
- **Professional codebase**: Industry standard practice

**IMPORTANT NOTE TO TEAM:**

> "Your commits will be rejected if they don't follow the format: `type(scope): description`. Types are: feat, fix, docs, style, refactor, test, chore, ci, build. This isn't bureaucracy - it's how professional teams work."

---

### 5. Why pnpm over npm/yarn?

| Feature          | npm               | yarn   | pnpm (Our Choice)     |
| ---------------- | ----------------- | ------ | --------------------- |
| Disk space       | High (duplicates) | Medium | Low (shared store)    |
| Install speed    | Slow              | Medium | Fast                  |
| Monorepo support | Basic             | Good   | Excellent             |
| Strictness       | Loose             | Loose  | Strict (catches bugs) |

**IMPORTANT NOTE TO TEAM:**

> "Always use `pnpm`, never `npm` or `yarn`. If you see errors about missing packages, run `pnpm install` from the root directory."

---

### 6. Why Shared Types Package?

**The problem without shared types:**

```
// Backend thinks:
{ user_id: number, role: "admin" }

// Frontend thinks:
{ userId: string, role: "ADMIN" }

// Result: BUGS!
```

**Our solution - `@ek-sms/shared-types`:**

```typescript
// packages/shared-types/src/models.ts
export interface User {
  id: string;
  email: string;
  role: UserRole;
}

// Used in frontend:
import type { User } from "@ek-sms/shared-types";

// Used in backend validation too!
```

**Tell your team:**

> "All API contracts (request/response shapes) are defined in `packages/shared-types`. If you're adding a new API endpoint, define the types there FIRST, then implement."

---

## Protected Files (Do Not Touch)

### 🔴 NEVER MODIFY (Without Team Lead Approval)

These files affect the entire project. Changing them can break builds, deployments, or the entire team's workflow.

| File/Folder               | Why Protected                                        |
| ------------------------- | ---------------------------------------------------- |
| `turbo.json`              | Build orchestration - wrong config breaks all builds |
| `pnpm-workspace.yaml`     | Workspace structure - changes break package linking  |
| `package.json` (root)     | Workspace scripts - affects everyone                 |
| `.husky/*`                | Git hooks - disabling breaks code quality            |
| `commitlint.config.mjs`   | Commit rules - changes affect git history            |
| `lint-staged.config.mjs`  | Pre-commit checks - disabling allows bad code        |
| `.github/workflows/*`     | CI/CD pipelines - changes affect deployments         |
| `.env.example`            | Environment docs - incomplete docs = confused devs   |
| `docker-compose.yml`      | Local infra - changes can break everyone's setup     |
| `apps/api/src/app/core/*` | Core utilities - database, security, config          |
| `packages/config/*`       | Shared configs - affects all linting/types           |

### 🟡 MODIFY WITH CAUTION

| File/Folder               | Who Can Modify | Notes                                   |
| ------------------------- | -------------- | --------------------------------------- |
| `packages/shared-types/*` | Any dev        | Add types, don't remove/rename existing |
| `apps/api/alembic/*`      | Backend devs   | Database migrations - test thoroughly   |
| `apps/web/next.config.ts` | Frontend lead  | Build config - can break production     |
| `apps/api/pyproject.toml` | Backend lead   | Python dependencies                     |
| `apps/web/package.json`   | Frontend lead  | JS dependencies                         |

### 🟢 SAFE TO MODIFY

| File/Folder                  | Who Can Modify                           |
| ---------------------------- | ---------------------------------------- |
| `apps/api/src/app/modules/*` | Backend devs (your assigned module)      |
| `apps/web/src/app/*`         | Frontend devs                            |
| `apps/web/src/components/*`  | Frontend devs                            |
| `docs/*`                     | Anyone (documentation is everyone's job) |

---

## Development Workflow

### Daily Commands

```bash
# Start everything for development
pnpm dev

# Run linting
pnpm lint

# Run type checking
pnpm type-check

# Build everything
pnpm build

# Run tests
pnpm test
```

### Commit Workflow

```bash
# 1. Stage your changes
git add .

# 2. Commit with conventional format
git commit -m "feat(grades): add grade submission API"

# 3. If commit fails, check the error message
#    - Lint errors? Fix them
#    - Bad commit message? Follow the format

# 4. Push when ready
git push
```

### Branch Strategy

| Branch    | Purpose            | Who Merges                |
| --------- | ------------------ | ------------------------- |
| `main`    | Production code    | Team Lead only            |
| `develop` | Integration branch | Team Lead review          |
| `feat/*`  | New features       | Dev creates, Lead reviews |
| `fix/*`   | Bug fixes          | Dev creates, Lead reviews |

---

## Quick Reference for Team Members

### For Frontend Developers

```
Your workspace: apps/web/
Your types: packages/shared-types/ (read) + apps/web/src/types/ (write)
Your components: apps/web/src/components/
Your pages: apps/web/src/app/

Commands:
  pnpm dev          # Start dev server
  pnpm lint         # Check for errors
  pnpm type-check   # Verify TypeScript
```

**Don't:**

- Modify `next.config.ts` without approval
- Add dependencies without team discussion
- Create API calls without using `ApiClient` from `lib/api`

### For Backend Developers

```
Your workspace: apps/api/
Your modules: apps/api/src/app/modules/
Your migrations: apps/api/alembic/versions/

Commands:
  pnpm dev              # Start API server
  pnpm --filter api test    # Run tests
```

**Don't:**

- Modify files in `core/` without approval
- Create raw SQL queries (use SQLAlchemy)
- Store sensitive data without encryption
- UPDATE grade records (always INSERT events)

### For Everyone

**DO:**

- Run `pnpm lint` before committing
- Write meaningful commit messages
- Ask before modifying protected files
- Document your code
- Write tests for new features

**DON'T:**

- Use `npm` or `yarn`
- Skip the pre-commit hooks
- Push directly to `main` or `develop`
- Modify shared configs without approval
- Hardcode environment values

---

## Architecture Diagrams

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTS                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Browser │  │ Mobile  │  │  PWA    │  │  Admin  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
└───────┼────────────┼────────────┼────────────┼──────────────┘
        │            │            │            │
        └────────────┴─────┬──────┴────────────┘
                           │
                    ┌──────▼──────┐
                    │   VERCEL    │
                    │  (Next.js)  │
                    │   Frontend  │
                    └──────┬──────┘
                           │ API Calls
                    ┌──────▼──────┐
                    │   RENDER    │
                    │  (FastAPI)  │
                    │   Backend   │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │ PostgreSQL  │  │    Redis    │  │    SMTP     │
   │  Database   │  │    Cache    │  │   (Email)   │
   └─────────────┘  └─────────────┘  └─────────────┘
```

### Module Dependency Flow

```
┌─────────────────────────────────────────────────────────┐
│                    apps/web (Frontend)                   │
│                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌────────────┐  │
│  │    Pages    │───▶│  Components │───▶│  API Client │  │
│  └─────────────┘    └─────────────┘    └──────┬─────┘  │
└───────────────────────────────────────────────┼─────────┘
                                                │
                    imports types from          │
                           │                    │
┌──────────────────────────▼────────────────────┼─────────┐
│              packages/shared-types             │         │
│                                               │         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐       │         │
│  │  Enums  │  │ Models  │  │API Types│       │         │
│  └─────────┘  └─────────┘  └─────────┘       │         │
└───────────────────────────────────────────────┼─────────┘
                                                │
                    HTTP requests               │
                                                │
┌───────────────────────────────────────────────▼─────────┐
│                    apps/api (Backend)                    │
│                                                         │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐             │
│  │ Routers │───▶│Services │───▶│  Repos  │──▶ Database │
│  └─────────┘    └─────────┘    └─────────┘             │
│       │                                                 │
│       └──────────────────────────────────────────────▶  │
│                    Schemas (Pydantic)                   │
└─────────────────────────────────────────────────────────┘
```

---

## Glossary

| Term                     | Definition                                               |
| ------------------------ | -------------------------------------------------------- |
| **Monorepo**             | Single repository containing multiple projects           |
| **Workspace**            | A package within the monorepo (apps/web, apps/api, etc.) |
| **Turborepo**            | Build system that caches and parallelizes tasks          |
| **Event Sourcing**       | Storing all changes as immutable events                  |
| **PWA**                  | Progressive Web App - installable web application        |
| **JWT**                  | JSON Web Token - authentication mechanism                |
| **TOTP**                 | Time-based One-Time Password - 2FA method                |
| **Conventional Commits** | Standardized commit message format                       |

---

## Questions?

If something in this guide is unclear:

1. Ask in the team chat
2. Check the `docs/` folder for more details
3. Read the code comments in protected files
4. Don't guess - ask the Product Lead

---

_Last updated: January 2025_
_Maintained by: Product Lead_
