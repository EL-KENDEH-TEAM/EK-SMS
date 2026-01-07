# Contributing to EK-SMS

Thank you for contributing to EK-SMS! This guide will help you get started.

## 🌿 Branch Strategy

```
main      → Production-ready code (protected)
develop   → Active development
feature/* → New features (branch from develop)
fix/*     → Bug fixes (branch from develop)
```

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### Submitting Changes

1. Push your branch: `git push origin feature/your-feature-name`
2. Open a Pull Request to `develop`
3. Wait for CI to pass
4. Request review from a team member

## 💻 Development Workflow

### Daily Workflow

```bash
# Start infrastructure (if not running)
docker-compose up -d

# Start development servers
pnpm dev
```

### Before Committing

Pre-commit hooks will automatically:

- Lint your code
- Format Python files with Ruff
- Validate commit message format

### Commit Message Format

```
<type>(<scope>): <subject>

Examples:
feat(auth): add two-factor authentication
fix(grades): correct calculation for GPA
docs(api): update endpoint documentation
```

**Types:** feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert

## 🏗️ Code Standards

### Python (Backend)

- Follow PEP 8 (enforced by Ruff)
- Use type hints for all functions
- Maximum line length: 100 characters
- Use async/await for database operations

```python
# Good
async def get_user(user_id: str) -> User | None:
    """Get user by ID."""
    return await repository.get_by_id(user_id)

# Bad
def get_user(user_id):
    return repository.get_by_id(user_id)
```

### TypeScript (Frontend)

- Use TypeScript strict mode
- Prefer functional components with hooks
- Use named exports

```typescript
// Good
export function UserCard({ user }: UserCardProps): JSX.Element {
  return <div>{user.name}</div>;
}

// Bad
export default function({ user }) {
  return <div>{user.name}</div>;
}
```

## 🧪 Testing

### Backend Tests

```bash
cd apps/api
.venv\Scripts\activate
pytest                    # Run all tests
pytest --cov=src          # With coverage
pytest tests/test_file.py # Specific file
```

### Frontend Tests

```bash
pnpm --filter web test
```

## 📁 Module Structure (Backend)

Each module in `apps/api/src/app/modules/` follows this structure:

```
module_name/
├── __init__.py      # Exports
├── models.py        # SQLAlchemy models
├── schemas.py       # Pydantic schemas
├── repository.py    # Database operations
├── service.py       # Business logic
└── router.py        # API endpoints
```

## 🔧 Useful Commands

| Command                  | Description           |
| ------------------------ | --------------------- |
| `pnpm dev`               | Start all dev servers |
| `pnpm build`             | Build all packages    |
| `pnpm lint`              | Lint all packages     |
| `pnpm test`              | Run all tests         |
| `docker-compose up -d`   | Start infrastructure  |
| `docker-compose down`    | Stop infrastructure   |
| `docker-compose logs -f` | View logs             |

## ❓ Getting Help

- Check existing documentation in `/docs`
- Ask in the team chat
- Create an issue on GitHub
