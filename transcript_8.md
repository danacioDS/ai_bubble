# AI Bubble Detector — Production Hardening from Code Review

## Overview

Implemented the recommendations from the comprehensive code review. 18/18 tests pass, frontend builds in 711ms. Changes span backend, frontend, Docker, and CI.

---

## Changes Applied

### 1. Data-Driven Scoring Rules (`backend/indicators.py`)

**Problem:** Five hardcoded if/else chains with magic thresholds. Every tuning required editing source code. No way to A/B test or evolve the model without touching business logic.

**Fix:** Extracted all rules into declarative data structures:

```python
INFO_RULES = [
    {
        "name": "P/E",
        "field": "trailingPE",
        "thresholds": [
            (40, 2, "P/E very high ({:.1f})"),
            (30, 1, "P/E elevated ({:.1f})"),
        ],
        "missing_penalty": 0.5,
        "missing_msg": "Missing P/E data",
    },
    # ... Revenue Growth, P/B
]

HIST_RULES = [
    {
        "name": "Volatility",
        "type": "volatility",
        "threshold": 0.5,
        "score": 1,
        "min_obs": 10,
        "reason_msg": "Very high volatility ({:.1%})",
        "missing_penalty": 0.3,
    },
    # ... Momentum
]
```

**Benefits:**
- Tuning thresholds no longer requires code changes
- Rules can be loaded from config/DB in the future
- Same scoring output (verified by existing tests)
- Clear single source of truth for bubble heuristics

---

### 2. Mocked Yahoo Finance in Tests (`backend/tests/`)

**Problem:** Integration tests made real HTTP calls to Yahoo Finance. CI was flaky — network outages, rate limits, or API changes caused test failures unrelated to code changes.

**Fix:** Used `unittest.mock.patch` to mock `yf.Ticker` in both `test_api.py` and `test_finance.py`:

```python
@patch("backend.finance.yf.Ticker")
def test_stock_endpoint_shape(mock_ticker):
    mock_ticker.return_value = _make_mock_stock()
    res = client.get("/stock/AAPL")
    assert res.status_code == 200
```

**Results:**
- 18 tests run in ~0.8s (vs ~7s with real network calls)
- Zero network dependency
- Deterministic — same data every run
- Added tests: cache hit, empty data, health endpoints

---

### 3. Rate Limiting & Stricter Validation (`backend/main.py`)

**Problem:** No rate limiting — 100 concurrent users would overwhelm the cache and yfinance. Ticker validation was a weak length check (`len(ticker) > 10`) that allowed garbage input.

**Fix:**
- Custom in-memory `RateLimiter` middleware (default: 60 req/min per IP)
- Env-configurable via `RATE_LIMIT_MAX` / `RATE_LIMIT_WINDOW`
- Ticker regex: `^[A-Z]{1,5}$` — rejects invalid symbols early
- Returns 429 when rate limit exceeded

---

### 4. Structured JSON Logging (`backend/main.py`)

**Problem:** Plain-text logs (`2024-01-01 [INFO] __main__: message`) are hard to parse in production. No machine-readable format for log aggregation.

**Fix:** Custom `JSONFormatter` that serializes all log records as JSON:

```json
{"time": "2024-01-01 12:00:00", "level": "INFO", "name": "__main__", "message": "Analysis request for AAPL"}
```

Includes `exception` key when exc_info is present.

---

### 5. Health Endpoints (`backend/main.py`)

Added Kubernetes-style health checks:
- `/health/live` → `{"status": "alive"}` (liveness probe)
- `/health/ready` → `{"status": "ready"}` (readiness probe)

---

### 6. Frontend API Service Layer (`frontend/src/services/api.js`)

**Problem:** `StockAnalyzer.vue` had raw `fetch()` calls with inline URL construction, mixing concerns.

**Fix:** Extracted API calls into a dedicated module:

```js
export async function fetchStockData(ticker, { signal } = {}) {
  const res = await fetch(`${API_BASE}/stock/${ticker}`, { signal })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}
```

**Benefits:**
- Single place to add headers, error handling, retry logic
- Components don't know about URL construction
- Easier to mock in tests

---

### 7. Fixed CompanyList Auto-Expand Bug (`frontend/src/components/CompanyList.vue`)

**Problem:** `computedOpen` was defined but never used in the template — the template referenced `openSectors` directly. When searching, sectors stayed collapsed instead of auto-expanding.

**Fix:** Changed template from `openSectors[sector.name]` to `computedOpen[sector.name]`. The computed property already had the correct logic; it was just disconnected from the template.

---

### 8. Docker Multi-Stage & Hardening

**Frontend** (`frontend/Dockerfile`):
- Two-stage build: `node:22-alpine` build → `nginx:alpine` serve
- Build stage produces static assets in `/app/dist`
- Nginx stage serves them on port 5173 with SPA fallback
- Drops from ~400MB dev image to ~25MB production image

**Backend** (`backend/Dockerfile`):
- Changed from `python:3.11-slim` to `python:3.12-slim` (matching CI/docs)
- Added `appuser` non-root user with chown
- Runs as non-root user (security best practice)

**docker-compose.yml**:
- Added environment variables for rate limiting, timeouts, cache TTL
- Sets `VITE_API_URL=http://backend:8000` for container-to-container DNS

---

### 9. Repo Cleanup

- Removed `backend/package-lock.json` (accidental npm artifact)
- Updated `.gitignore` to exclude `backend/venv/` and `backend/package-lock.json`

---

## Files Changed

| File | Status | Changes |
|------|--------|---------|
| `backend/indicators.py` | Rewritten | Declarative `INFO_RULES` / `HIST_RULES`; same scoring output |
| `backend/main.py` | Rewritten | JSON logging, rate limiter, regex ticker validation, health endpoints |
| `backend/tests/test_api.py` | Rewritten | Mocked yfinance, no network, +health endpoint tests (18 total) |
| `backend/tests/test_finance.py` | Rewritten | Mocked yfinance, cache hit test, empty data test |
| `backend/tests/test_indicators.py` | Unchanged | All synthetic data, works with new rules engine |
| `frontend/src/services/api.js` | **Created** | Centralized fetch layer with AbortController support |
| `frontend/src/components/StockAnalyzer.vue` | Modified | Uses `api.js` instead of raw fetch; removed `API_BASE` const |
| `frontend/src/components/CompanyList.vue` | Fixed | `computedOpen` now wired to template (auto-expand on search) |
| `frontend/Dockerfile` | Rewritten | Multi-stage: node build → nginx serve |
| `backend/Dockerfile` | Modified | Python 3.12-slim, non-root user |
| `docker-compose.yml` | Modified | Added env vars for backend/frontend |
| `backend/.env.example` | Modified | Added rate limit config |
| `backend/package-lock.json` | **Deleted** | Accidental npm artifact |
| `.gitignore` | Modified | Added `backend/venv/`, `backend/package-lock.json` |

---

## Verification

```
Backend tests:  18 passed in 0.81s (was 7.30s with network)
Frontend build: passed (711ms, 3 assets, ~29KB gzipped)
```
