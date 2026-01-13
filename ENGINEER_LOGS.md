# 🛠️ Debug Log: Fatal Next.js Crash - "Next.js package not found"

**Date:** 2026-01-06  
**Status:** Resolved ✅  
**Environment:** Windows 11, pnpm Monorepo, Next.js 15+

---

## 🛑 Error Symptoms

When running standard `pnpm dev`, the process crashed with a "FATAL" error. The browser entered an infinite refresh loop and failed to render the page.

**Terminal Output:**

```text
✓ Ready in 7.1s
GET / 200 in 3.8s (compile: 2.8s, render: 1047ms)
FATAL: An unexpected Turbopack error occurred.
A panic log has been written to ...\AppData\Local\Temp\next-panic-xxx.log
```

**Panic Log Content:**

```text
Failed to write app endpoint /page
Caused by:
- Next.js package not found
Debug info:
- Execution of Project::hmr_version_state failed
- Next.js package not found
```

---

## 🔍 Root Cause

The error was caused by the Next.js underlying compiler (Turbopack) failing to resolve the `next` package within a pnpm monorepo on Windows.

Even when running a standard `dev` command, Next.js internal resolution engine can get "lost" because pnpm stores packages in a hidden "Virtual Store" (`node_modules/.pnpm/...`) and uses symlinks to expose them. On Windows, these deep symlink chains often break, leading the compiler to believe the Next.js framework itself is missing.

---

## 💡 Solution & Resolution Steps

### 1. Force Dependency Visibility (Hoisting)

To fix the resolution bug, Next.js needs to find the package source more easily. Adding a hoist pattern forces pnpm to place `next` at the top level of `node_modules`.

**Action:** Create/Edit `.npmrc` in the project root.

**Content:**

```text
public-hoist-pattern[]=next
```

### 2. Nuclear Reset (PowerShell)

Clear the corrupted build cache and the broken symlink references that were causing the loop.

```powershell
# Delete the Next.js build and HMR cache
Remove-Item -Path "apps/web/.next" -Recurse -Force

# Delete all node_modules (Root and App level) to clear bad symlinks
Remove-Item -Path "node_modules" -Recurse -Force
Remove-Item -Path "apps/web/node_modules" -Recurse -Force

# Re-install and re-link the workspace
pnpm install
```

### 3. Verification

Restart the development server:

```bash
pnpm dev
```

---

**Result:** The application successfully started without errors, and the infinite refresh loop was eliminated.

---

# 🛠️ Debug Log: Ruff Linter - Unused Import in `__init__.py`

**Date:** 2026-01-12
**Status:** Resolved ✅
**Environment:** Windows 11, pnpm Monorepo, FastAPI + Ruff

---

## 🛑 Error Symptoms

When trying to commit with `git commit`, the pre-commit hook (lint-staged + ruff) failed with an unused import error.

**Terminal Output:**

```text
✖ apps/api/.venv/Scripts/ruff check --fix:
F401 `.router.router` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
 --> apps/api/src/app/modules/school_applications/__init__.py:1:31
  |
1 | from .router import router as school_applications_router
  |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  |
help: Use an explicit re-export: `router as router`

Found 5 errors (4 fixed, 1 remaining).
husky - pre-commit script failed (code 1)
```

---

## 🔍 Root Cause

In Python, when you import something in `__init__.py` purely for **re-exporting** (so other modules can import it from the package), linters like Ruff flag it as "unused" because the imported name isn't actually used within that file.

**Problematic Code:**

```python
# __init__.py
from .router import router as school_applications_router  # ← Alias not used HERE
```

The alias `school_applications_router` was meant to be imported by `api.py`, but since it's not used within `__init__.py` itself, Ruff considers it an unused import (F401).

---

## 💡 Solution & Resolution Steps

### Option 1: Use `__all__` (Recommended)

Explicitly declare what the module exports using `__all__`. This tells Python and linters that the import is intentional for re-export.

**Fixed Code:**

```python
# __init__.py
from .router import router

__all__ = ["router"]
```

### Option 2: Redundant Alias

Use the same name for the alias to signal explicit re-export:

```python
from .router import router as router  # Explicit re-export
```

### Option 3: Keep Aliasing in the Consumer

Keep `__init__.py` simple and do the aliasing where it's actually used:

```python
# __init__.py
from .router import router

__all__ = ["router"]

# api.py (consumer)
from app.modules.school_applications import router as school_applications_router
```

---

## 📝 Key Takeaway

When re-exporting in `__init__.py`, always use `__all__` to explicitly declare exports. This:

- Satisfies linters (Ruff, Pylint, Pyright)
- Documents the public API of your module
- Follows Python best practices (PEP 8)

**Result:** Commit succeeded after adding `__all__ = ["router"]` to `__init__.py`.
