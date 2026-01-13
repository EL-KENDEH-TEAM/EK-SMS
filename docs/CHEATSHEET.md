# EK-SMS Developer Cheat Sheet

## Quick Start (New Developer)

```bash
# 1. Clone and install
git clone <repo-url>
cd EK-SMS
pnpm install

# 2. Setup environment
cp .env.example .env.local

# 3. Start Docker services
docker-compose up -d

# 4. Setup API virtual environment
cd apps/api
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt

# 5. Run migrations
alembic upgrade head

# 6. Start development (from root)
cd ../..
pnpm dev
```

## Working on Web Only (Frontend)

```bash
# Start Docker (for API if needed) + Web
docker-compose up -d
pnpm --filter web dev

# Build for production
pnpm --filter web build

# Run tests
pnpm --filter web test

# Lint
pnpm --filter web lint
```

## Working on API Only (Backend)

```bash
# 1. Start Docker services
docker-compose up -d

# 2. Activate virtual environment (from project root)
# Windows (PowerShell):
apps\api\.venv\Scripts\Activate.ps1
# Windows (CMD):
apps\api\.venv\Scripts\activate.bat
# macOS/Linux:
source apps/api/.venv/bin/activate

# 3. Navigate to API and run
cd apps/api
pnpm dev

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/path/to/test_file.py -v

# Run with coverage
pytest --cov=src tests/

# Install new package
pip install <package>
pip freeze > requirements.txt

# Deactivate venv when done
deactivate
```

## Working on Both (Full Stack)

```bash
# 1. Start Docker services
docker-compose up -d

# 2. Start both API and Web (from project root)
pnpm dev

# Build everything
pnpm build

# Lint all code
pnpm lint

# Check TypeScript
pnpm type-check

# Run all tests
pnpm test
```

## Docker Commands

```bash
# Start infrastructure (PostgreSQL, Redis, Mailpit, pgAdmin)
docker-compose up -d

# Stop all services
docker-compose down

# View running containers
docker ps

# View logs
docker-compose logs -f           # All services
docker-compose logs -f postgres  # Specific service

# Restart a service
docker-compose restart postgres

# Reset database (delete volume)
docker-compose down -v
docker-compose up -d
```

## Database & Migrations

```bash
# Must be in apps/api with venv activated

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description of change"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Connect to database directly
docker exec -it eksms-postgres psql -U eksms -d eksms_dev
```

## Commit Message Format

```
type(scope): description

# Types:
feat     # New feature
fix      # Bug fix
docs     # Documentation
style    # Formatting only
refactor # Code restructuring
test     # Adding tests
chore    # Maintenance
ci       # CI/CD changes

# Examples:
feat(auth): add password reset flow
fix(grades): resolve calculation error
docs(api): update endpoint documentation
```

## Project Structure

```
EK-SMS/
├── apps/
│   ├── api/          # FastAPI backend (Python)
│   └── web/          # Next.js frontend (React)
├── packages/
│   ├── config/       # Shared ESLint/TS configs
│   └── shared-types/ # Shared TypeScript types
├── docs/             # Documentation
└── infra/            # Docker configs
```

## File Permissions

| 🔴 NEVER TOUCH       | 🟡 ASK FIRST        | 🟢 SAFE             |
| -------------------- | ------------------- | ------------------- |
| turbo.json           | shared-types/\*     | modules/\*          |
| .husky/\*            | alembic/\*          | components/\*       |
| _.config._ (root)    | next.config.ts      | app/\* pages        |
| .github/workflows/\* | pyproject.toml      | Your assigned areas |
| core/\*              | package.json (apps) | docs/\*             |

## Branch Naming

```
feat/description    # New features
fix/description     # Bug fixes
docs/description    # Documentation
refactor/description # Refactoring
```

## Environment Variables

| Variable        | Used By               |
| --------------- | --------------------- |
| `POSTGRES_*`    | API only              |
| `REDIS_*`       | API only              |
| `JWT_*`         | API only              |
| `NEXT_PUBLIC_*` | Web (browser-exposed) |

## Don'ts

- ❌ Use `npm` or `yarn` (use `pnpm`)
- ❌ Push to `main` directly
- ❌ Skip pre-commit hooks
- ❌ UPDATE grade records (INSERT events only)
- ❌ Hardcode secrets
- ❌ Modify core/\* without approval

## Dos

- ✅ Run `pnpm lint` before committing
- ✅ Write conventional commits
- ✅ Ask before touching configs
- ✅ Document your code
- ✅ Write tests for new features
