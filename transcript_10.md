# AI Bubble Detector — Final Comprehensive Audit

## Overview

After 9 engineering passes spanning bug fixes, architectural hardening, production middleware, frontend decoupling, and Docker optimization, this transcript documents a final holistic audit of the codebase. The goal: identify remaining gaps between the committed baseline and the working tree, flag documentation drift, assess test coverage, and catalog any lingering issues across all layers.

---

## Findings

### A. Uncommitted Delta (Working Tree vs HEAD)

The working directory has drifted significantly from the latest commit (`0060ff9`, "Phase 2"). Across 14 files, 448 lines added, 532 removed — representing passes 3 through 9 of development.

**Modified files:**

| File | Delta |
|------|-------|
| `architecture.md` | Rewritten to reflect current package structure, domain separation, observability middleware, API mappers, 20 tests |
| `backend/Dockerfile` | `python:3.12-slim`, non-root `appuser`, `HEALTHCHECK`, `app.main:app` entrypoint |
| `backend/.env.example` | Added `RATE_LIMIT_MAX`, `RATE_LIMIT_WINDOW` |
| `backend/tests/test_api.py` | Rewritten: mocked yfinance, 6 tests (was 5 with live network), added health endpoint tests |
| `backend/tests/test_finance.py` | Rewritten: mocked yfinance, 4 tests (was 2), cache hit, empty data, hist type assertion |
| `backend/tests/test_indicators.py` | Expanded: 10 tests (was 8), added contract + snapshot tests |
| `frontend/Dockerfile` | Multi-stage: node build → nginx serve (was single-stage dev image) |
| `frontend/src/components/StockAnalyzer.vue` | Extensively rewritten: uses `api.js` service layer, `mappers.js` for display formatting, `riskLabel` support, removed `API_BASE` inline constant |
| `docker-compose.yml` | Added env vars, healthcheck, restart policy, `depends_on` |
| `.gitignore` | Added `backend/venv/`, `backend/package-lock.json` |

**Deleted files (replaced by `backend/app/` package):**

| File | Fate |
|------|------|
| `backend/finance.py` | Moved to `backend/app/finance.py` |
| `backend/indicators.py` | Moved to `backend/app/indicators.py` (now a facade) |
| `backend/main.py` | Moved to `backend/app/main.py` |
| `backend/package-lock.json` | Deleted (accidental npm artifact) |

**Untracked files (new in working tree):**

| File | Purpose |
|------|---------|
| `backend/app/__init__.py` | Package marker |
| `backend/app/domain/__init__.py` | Package marker |
| `backend/app/domain/features.py` | Pure feature extraction |
| `backend/app/domain/scoring.py` | Pure rule evaluation |
| `frontend/src/services/api.js` | Centralized HTTP layer |
| `frontend/src/services/mappers.js` | API → UI transform layer |
| `frontend/src/components/CompanyList.vue` | Searchable sector-based company picker |
| `frontend/src/data/companies.json` | 59 companies across 9 sectors |
| `transcript_3.md` through `transcript_9.md` | Engineering journal entries 3–9 |

### B. Documentation Drift

1. **README.md claims "15 tests / 3 passes"** — The working tree has 20 tests and 9 passes worth of changes. The README's testing table references `tests/test_api.py`: 5, `tests/test_finance.py`: 2, `tests/test_indicators.py`: 8. Current counts are 6, 4, and 10 respectively. The scoring methodology table is accurate, but the architecture diagram and run commands are stale (still reference `uvicorn main:app` instead of `uvicorn app.main:app`).

2. **Port mismatch** — README says frontend is at `http://localhost:5173` for Docker. The Docker compose maps to port 80 (nginx) and the dev server uses 5173. The README doesn't distinguish production vs dev ports.

3. **architecture.md is up to date** — Unlike the README, `architecture.md` correctly reflects the current package structure, domain separation, middleware pipeline, 20 tests, and multi-stage Docker. It was revised during the hardening passes.

### C. Code Quality Issues

1. **`backend/__init__.py` is vestigial** — An empty `__init__.py` at `backend/__init__.py` was left behind after the flat-to-package migration. The package is now `backend/app/`. This file has no purpose and adds an unnecessary namespace level.

2. **`frontend/pnpm-workspace.yaml` is cosmetic** — Contains only `allowBuilds: esbuild: true`. The project is not a monorepo workspace. This file has no functional effect but is misleading.

3. **`notebooks/yahoo_finance.ipynb` has stale imports** — References `from finance import get_stock_data` (flat path from the old structure). The notebook won't execute against the current codebase.

4. **Rate limiter is synchronous** — `RateLimiter.is_allowed()` does blocking dict operations (`time.time()`, list filtering, append) inside an `@app.middleware("http")` handler. FastAPI wraps sync middleware as ASGI, but under high concurrency the GIL + list operations could block the async event loop.

5. **`sys.path` hacks in tests** — All three test files use `sys.path.insert(0, ...)` to resolve imports. This works but is fragile. Proper package installation (`pip install -e .`) or `PYTHONPATH` would be more maintainable.

6. **`test_warning_range` still uses random noise** — Despite `np.random.seed(42)`, the test relies on a random series. A fully deterministic fixture would be more robust.

7. **No frontend tests** — CI only verifies the frontend builds. There are zero unit or component tests for the Vue components or services layer.

8. **No linting or formatting in CI** — No ruff, mypy, ESLint, or Prettier in the pipeline.

### D. Configuration Drift

- `docker-compose.yml` sets env vars for backend (`YAHOO_TIMEOUT`, `CACHE_TTL`, `RATE_LIMIT_*`, `PYTHONUNBUFFERED`) but does not pass `VITE_API_URL` to the frontend service. The old compose did — it was lost in a rewrite. Without it, Docker frontend → backend calls will use `http://127.0.0.1:8000` which resolves to the frontend container, not the backend.

- CI runs `pnpm install` without `--frozen-lockfile`. The Dockerfile uses it (correctly), but CI doesn't — allowing accidental lockfile drift.

---

## Files Changed in This Pass

| File | Status | Change |
|------|--------|--------|
| This transcript | **Created** | Final audit documentation |

No source files were modified in this pass — this transcript is a read-only audit.

---

## Current State Summary

| Metric | Value |
|--------|-------|
| Backend tests | 20 passed in ~1s |
| Frontend build | ~700ms, 3 assets, ~29KB gzipped |
| Committed state (HEAD) | Phase 2 — 15 tests, flat structure |
| Working tree state | Phase 9 — 20 tests, domain-separated, production-hardened |
| Documentation gap | README matches HEAD, not working tree |
| Uncommitted files | 9 new files, 6 modified, 4 deleted |
| Frontend test coverage | 0% |
| CI linting/formatting | None |

---

## Recommended Actions

| Priority | Action | Rationale |
|----------|--------|-----------|
| P0 | Commit working tree | All hardening work is uncommitted; HEAD is dangerously behind |
| P0 | Update README to match current state | Stale docs erode trust; 15→20 tests, `app.main:app`, port docs |
| P1 | Re-add `VITE_API_URL` to docker-compose frontend | Docker containers can't reach each other without it |
| P1 | Remove `backend/__init__.py` | Vestigial file from flat-to-package migration |
| P1 | Add `--frozen-lockfile` to CI `pnpm install` | Prevents accidental lockfile drift |
| P2 | Replace `sys.path` with `pip install -e .` in tests | More maintainable, no path hacks |
| P2 | Add ruff linting to CI | Catch basic Python errors automatically |
| P2 | Add frontend component tests | Current test gap leaves Vue components untested |
| P3 | Remove `pnpm-workspace.yaml` or add real workspace config | Eliminates misleading artifact |
| P3 | Fix notebook imports or remove | Stale notebook will confuse future readers |
| P3 | Make rate limiter async | Event loop blocking under load |
| P3 | Replace random fixture in `test_warning_range` | Fully deterministic data would be more robust |

---

## Verification

```
Backend tests:  20 passed in 0.96s
Frontend build: passed (704ms, 3 assets, ~29KB gzipped)
```
