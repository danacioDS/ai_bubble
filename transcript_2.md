# AI Bubble Detector — Phase 2: Architectural Hardening & Production Readiness

## Overview

After the initial bugfix pass (transcript.md covers rounds 1–2), the project underwent a structural review targeting systemic issues: contract enforcement, testing discipline, deployment awareness, and production hardening.

---

## Part 1: Architectural Review Feedback

### What Was Assessed

The review evaluated the fixes across five dimensions:

| Layer | Issues Found |
|-------|-------------|
| Backend contracts | 3-value unpack crash, missing response models |
| Frontend rendering | Flat vs nested metric access |
| Docker networking | `localhost` doesn't resolve across containers |
| Scoring semantics | Weights double-counted, calibration off |
| UX failure modes | Missing error states, race conditions |

### Strongest Decisions Identified

#### 1. Schema mismatch treated as a contract problem

The `data.pe` vs `data.metrics.pe` bug was not a surface-level frontend issue. It exposed:
- Backend response shape was undocumented
- Frontend assumptions were implicit
- No contract tests existed

The recommendation: Pydantic models + OpenAPI-generated typings + centralized API client.

#### 2. Scoring calibration, not syntax

The documented 0–9 scale vs effective ~14 scale meant:
- Score interpretation was meaningless
- UI colors/categories drifted
- Historical comparisons inconsistent

The `clamp(10)` vs `clamp(9)` mismatch was flagged as especially dangerous — it silently corrupts metric trust.

#### 3. Docker networking

The `VITE_API_URL=http://backend:8000` fix demonstrated understanding of container DNS, isolated network namespaces, and build/runtime separation — production-oriented debugging.

### Hidden Class of Bug Prevented

The `histRes.ok` check prevented chart corruption. Without it, malformed payloads could propagate NaN into SVG rendering.

### Overall Capability Assessment

| Capability | Evidence |
|------------|----------|
| Systems thinking | Docker/network + frontend/backend contracts |
| Reliability focus | Error handling + score bounds + tests |
| Model integrity awareness | Calibration drift + scoring normalization |

---

## Part 2: Improvements Implemented

### A. Pydantic Response Models (`backend/main.py`)

Replaced ad-hoc dicts with typed `BaseModel` classes:

```python
class Metrics(BaseModel):
    pe: float | None = None
    forwardPe: float | None = None
    revenueGrowth: float | None = None
    priceToBook: float | None = None
    marketCap: int | None = None

class StockResponse(BaseModel):
    ticker: str
    name: str | None = None
    price: float | None = None
    metrics: Metrics
    score: int
    reasons: list[str]

class PricePoint(BaseModel):
    date: str
    close: float

class HistoryResponse(BaseModel):
    prices: list[PricePoint]
```

Endpoints use `response_model=StockResponse` / `response_model=HistoryResponse`, providing runtime validation, OpenAPI schema generation, and self-documenting contracts. The old `{"success": true, "data": {...}}` wrapper was removed — the response now matches the frontend's expected flat shape.

**Bonus fix:** The history endpoint had `str(idx.date())` where `idx` was an integer row index (after `reset_index()`), not a DatetimeIndex. Fixed to `str(row["Date"].date())`.

### B. Integration Tests (`backend/tests/`)

| File | Type | Tests | Purpose |
|------|------|-------|---------|
| `test_api.py` | FastAPI `TestClient` | 5 | Endpoint shape, metrics shape, history shape, 400 validation, nullable fields |
| `test_finance.py` | Contract | 2 | Return count (would've caught unpack bug), value types |
| `test_indicators.py` | Deterministic fixtures | 8 | Extreme bubble, safe, warning range, missing penalties, high PE, high growth, bounds fuzz, hist integration |

Key design decisions:
- `test_api.py` hits real endpoints (not mocked) — catches serialization errors and schema drift
- `test_indicators.py` uses synthetic `pd.DataFrame` fixtures — no network calls
- `test_score_bounds` fuzzes 100 parameter combinations to verify 0–9 range

### C. Request Cancellation (`frontend/src/components/StockAnalyzer.vue`)

```javascript
let currentController = null

async function analyze() {
  if (currentController) currentController.abort()
  currentController = new AbortController()
  const { signal } = currentController
  fetch(`${API_BASE}/stock/${ticker.value}`, { signal })
  fetch(`${API_BASE}/stock/${ticker.value}/history`, { signal })
}
```

Prevents stale-response race conditions during rapid typing (e.g., `AAPL → AAP → AA → AMD`). Aborted requests are silently ignored via `if (e.name === 'AbortError') return`.

---

## Part 3: Phase 1–3 Stabilization

### 1. Professional README (`README.md`)

Complete rewrite covering:
- Features overview
- Architecture diagram (ASCII)
- Full API documentation with example JSON responses
- Local development setup (backend + frontend)
- Docker one-command deployment
- Environment configuration reference
- Testing instructions
- Scoring methodology with full threshold table
- Score interpretation (Stable / Elevated / Speculative / Bubble Risk)
- CI documentation
- Future improvements roadmap

### 2. Environment Configuration

| File | Variables |
|------|-----------|
| `backend/.env.example` | `YAHOO_TIMEOUT=10`, `CACHE_TTL=300` |
| `frontend/.env.example` | `VITE_API_URL=http://localhost:8000` |

Both loaded via `python-dotenv` at startup. No more guessing required.

### 3. Deterministic Dependencies

```txt
anyio==4.13.0
cachetools==7.1.3
fastapi==0.136.1
httpx==0.28.1
numpy==2.4.4
pandas==3.0.3
pydantic==2.13.4
pydantic-core==2.46.4
pytest==9.0.3
python-dotenv==1.2.2
starlette==1.0.0
uvicorn==0.46.0
yfinance==1.3.0
```

All 13 packages pinned to exact versions. Frontend already deterministic via `pnpm-lock.yaml`.

### 4. Backend Caching (`cachetools.TTLCache`)

- 128-entry LRU with configurable TTL (default 300s)
- Cache key: ticker symbol (uppercased)
- Cache hit/miss logged at debug/info
- Configurable via `CACHE_TTL` env variable

### 5. Request Timeout Handling

- POSIX `SIGALRM`-based timeout for Yahoo Finance requests
- Default 10s, configurable via `YAHOO_TIMEOUT`
- Gracefully degrades outside main thread (TestClient, threaded servers)
- Dedicated `FinanceTimeoutError` → returns `(None, None, None)` → endpoint returns 404

### 6. Structured Logging

Replaced all `print()` with Python `logging`:

```
2025-01-15 14:30:22 [INFO] finance: Fetching data for NVDA
2025-01-15 14:30:32 [INFO] finance: Successfully fetched data for NVDA
2025-01-15 14:30:32 [INFO] __main__: Score for NVDA: 8/9
2025-01-15 14:30:35 [DEBUG] finance: Cache hit for AAPL
```

Logger hierarchy: `__main__`, `finance`. Full tracebacks on errors via `logger.exception()`.

### 7. Health Check Endpoint

`GET /health` → `{"status": "ok"}`

### 8. GitHub Actions CI (`.github/workflows/ci.yml`)

Two parallel jobs:

**Backend:**
```yaml
- uses: actions/setup-python@v5
  with: { python-version: "3.12" }
- run: pip install -r requirements.txt
- run: python -m pytest tests/ -v
```

**Frontend:**
```yaml
- uses: actions/setup-node@v4
  with: { node-version: "18" }
- run: npm install -g pnpm@11.1.3 && pnpm install && pnpm build
```

Runs on every push/PR to `main`.

### 9. `.dockerignore`

Excludes `__pycache__/`, `venv/`, `.env`, `.git/`, `.github/` from build context.

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/tests/__init__.py` | Test package |
| `backend/tests/test_api.py` | Integration tests (TestClient) |
| `backend/tests/test_finance.py` | Contract tests |
| `backend/tests/test_indicators.py` | Scoring fixture tests |
| `backend/.env.example` | Backend environment template |
| `backend/.dockerignore` | Docker build exclusions |
| `frontend/.env.example` | Frontend environment template |
| `.github/workflows/ci.yml` | CI pipeline |

## Files Modified (Round 3)

| File | Change |
|------|--------|
| `README.md` | Complete professional rewrite |
| `backend/finance.py` | Full rewrite: caching, timeouts, structured logging, signal-safe timeout handling |
| `backend/main.py` | Added logging setup, health endpoint, Pydantic response models, env loading via dotenv |
| `backend/requirements.txt` | Pinned exact versions (13 packages) |

## Test Results

```
15 passed in 6.56s
```

Frontend build: **passed** (830ms, 68KB JS + 3KB CSS gzipped to ~28KB total).
