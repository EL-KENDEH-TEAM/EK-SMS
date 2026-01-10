# EK-SMS Developer Cheat Sheet

## Commands (Run from Root)

```bash
pnpm dev          # Start all services
pnpm build        # Build everything
pnpm lint         # Lint all code
pnpm type-check   # Check TypeScript
pnpm test         # Run all tests
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
