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
