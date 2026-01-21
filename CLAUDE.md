# EK-SMS - Claude Code Guide

> **IMPORTANT**: Always read this entire file before starting ANY task on this project. This contains critical patterns, conventions, and architectural decisions that must be followed.

---

## Quick Reference

### Project

- **What**: Multi-tenant school management SaaS (anti-corruption focus)
- **Tenants**: Schools across West Africa
- **Key principle**: All grade changes are immutable and auditable

### Ports

| Service    | Port |
| ---------- | ---- |
| PostgreSQL | 5440 |
| Redis      | 6380 |
| API        | 8002 |
| Web        | 3000 |

### File Locations

| What                | Where                                     |
| ------------------- | ----------------------------------------- |
| Backend modules     | `apps/api/src/app/modules/{module_name}/` |
| Backend core        | `apps/api/src/app/core/`                  |
| Migrations          | `apps/api/alembic/versions/`              |
| Frontend pages      | `apps/web/src/app/`                       |
| Frontend components | `apps/web/src/components/`                |
| Shared types        | `apps/web/src/types/`                     |
| API client          | `apps/web/src/lib/api/`                   |

### Brand Colors

| Name               | Hex       | Usage                                    |
| ------------------ | --------- | ---------------------------------------- |
| Primary Blue       | `#1a365d` | Buttons, headers, links, primary actions |
| Primary Blue Hover | `#1e4976` | Button hover states                      |
| White              | `#ffffff` | Backgrounds, text on primary             |
| Light Gray         | `#f5f5f5` | Page backgrounds                         |
| Border Gray        | `#e5e7eb` | Borders, dividers                        |
| Text Dark          | `#1f2937` | Headings, primary text                   |
| Text Gray          | `#4b5563` | Body text                                |
| Text Light         | `#6b7280` | Secondary text, hints                    |
| Text Muted         | `#9ca3af` | Placeholders, disabled                   |
| Success Green      | `#22c55e` | Success states, confirmations            |
| Warning Yellow     | `#f59e0b` | Warnings, pending states                 |
| Error Red          | `#dc2626` | Errors, required markers                 |
| Info Blue          | `#3b82f6` | Info alerts, links                       |

### UI Patterns

- **Buttons**: Rounded corners (`border-radius: 8px`), padding `14px`
- **Cards**: White background, subtle shadow, `border-radius: 12px`
- **Inputs**: Border `#d1d5db`, focus border `#3b82f6` with light shadow
- **Font**: System UI (`system-ui, -apple-system, sans-serif`)
- **Spacing**: Use multiples of 4px (4, 8, 12, 16, 24, 32)

### Naming Conventions

**Python (Backend)**

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

**TypeScript (Frontend)**

- Components: `PascalCase.tsx`
- Utilities: `camelCase.ts`
- Types/Interfaces: `PascalCase`
- Variables: `camelCase`

**Database**

- Tables: `snake_case` plural (`users`, `schools`, `grade_events`)
- Columns: `snake_case` (`first_name`, `school_id`)
- Foreign keys: `{table_singular}_id` (`user_id`, `school_id`)

---

## Mini Task Patterns

### Adding a Field to a Model

1. Update model in `models.py`:

```python
new_field = Column(String(100), nullable=True)
```

2. Update schemas in `schemas.py`:

```python
new_field: str | None = None
```

3. Create migration:

```bash
cd apps/api
alembic revision --autogenerate -m "add new_field to table_name"
alembic upgrade head
```

---

### Adding a New API Endpoint

In the module's `router.py`:

```python
@router.get("/{id}", response_model=schemas.ItemResponse)
async def get_item(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.ItemResponse:
    """Get item by ID."""
    item = await service.get_by_id(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

---

### Adding a New Frontend Page

Create `apps/web/src/app/{route}/page.tsx`:

```typescript
export default function PageName(): JSX.Element {
  return (
    <div>
      <h1>Page Title</h1>
    </div>
  );
}
```

---

### Adding a New Component

Create `apps/web/src/components/{feature}/{ComponentName}.tsx`:

```typescript
export interface ComponentNameProps {
  title: string;
  onClick?: () => void;
}

export function ComponentName({ title, onClick }: ComponentNameProps): JSX.Element {
  return (
    <button onClick={onClick}>
      {title}
    </button>
  );
}
```

---

### Adding Form Validation (Frontend)

```typescript
const [errors, setErrors] = useState<Record<string, string>>({});

function validate(): boolean {
  const newErrors: Record<string, string> = {};

  if (!formData.email) {
    newErrors.email = "Email is required";
  }

  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
}
```

---

### Making an API Call (Frontend)

```typescript
async function fetchData() {
  try {
    const response = await fetch(`${API_URL}/endpoint`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) throw new Error("Failed to fetch");

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error:", error);
    throw error;
  }
}
```

---

### Adding a Database Query (Backend)

In `repository.py`:

```python
async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
    """Get user by email."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()
```

---

### Adding Tenant Scoping

**IMPORTANT**: Most tables need `school_id` for multi-tenant isolation.

Model:

```python
school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
```

Query (always filter by school):

```python
async def get_all_for_school(self, db: AsyncSession, school_id: UUID) -> list[Item]:
    result = await db.execute(
        select(Item).where(Item.school_id == school_id)
    )
    return result.scalars().all()
```

---

### Creating a Migration

```bash
cd apps/api
source .venv/bin/activate  # Windows: .venv\Scripts\activate
alembic revision --autogenerate -m "description of change"
alembic upgrade head
```

---

### Running Tests

```bash
# Backend
cd apps/api
pytest tests/path/to/test_file.py -v

# Frontend
pnpm --filter web test
```

---

### Commit Message Format

```
<type>(<scope>): <subject>

# Examples:
feat(auth): add email verification
fix(grades): correct average calculation
style(ui): update button colors
refactor(api): extract validation helper
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

---

## Key Rules

### Always Do

- Add `school_id` to tenant-scoped tables
- Use async/await for database operations
- Add type hints to Python functions
- Use TypeScript strict mode
- Filter queries by `school_id` for tenant data

### Never Do

- Allow grade modifications without audit trail
- Skip `school_id` on tenant data
- Use `any` type in TypeScript
- Commit directly to `main` branch
- Store passwords in plain text

---

## Module Structure (Backend)

When creating a new module, create this structure:

```
apps/api/src/app/modules/{module_name}/
├── __init__.py      # Exports
├── models.py        # SQLAlchemy models
├── schemas.py       # Pydantic schemas
├── repository.py    # Database operations
├── service.py       # Business logic
└── router.py        # API endpoints
```

---

## Response Formats

### Success (single)

```json
{
  "id": "uuid",
  "name": "value",
  "created_at": "2025-01-10T..."
}
```

### Success (list)

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

### Error

```json
{
  "error": "ERROR_CODE",
  "message": "Human readable message",
  "details": {}
}
```

---

## Full Context (Reference)

### Multi-Tenant Architecture

**Platform Level** (no school_id):

- `schools` - tenant records
- `school_applications` - registration applications
- Platform admin users

**School Level** (requires school_id):

- `users`, `students`, `teachers`, `parents`
- `classes`, `subjects`
- `grades`, `grade_events`, `report_cards`
- `audit_logs`

### Admin Types

1. **Platform Admin**: EK-SMS team, reviews school applications, can see all data
2. **School Admin**: Manages one school, creates users, configures settings

### Grade Lifecycle

```
DRAFT → SUBMITTED → LOCKED
```

- Draft: Teacher edits freely
- Submitted: Visible, awaiting lock
- Locked: Immutable, needs modification request to change

### School Registration Flow

1. Applicant fills 6-step form
2. Applicant verifies email (72h expiry)
3. Principal confirms (if different person)
4. Platform admin reviews
5. Approved → school + admin account created

### Verification Timing

- Links expire: 72 hours
- Reminder sent: 48 hours
- Rejected schools can reapply: after 30 days
