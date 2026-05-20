# AI Bubble Detector — Senior Engineering Review Implementation

## Overview

Implemented the recommendations from a senior engineering code review. Changes focus on production-grade architecture: proper package structure, domain separation, observability, frontend decoupling, and Docker hardening. 20/20 tests pass, frontend builds in 704ms.

---

## Changes Applied

### 1. Production Package Structure (`backend/app/`)

**Problem:** The backend had a flat module layout but used `from backend.finance import ...` imports. Running `uvicorn main:app` (from backend dir) produced `ModuleNotFoundError: No module named 'backend'` — the Dockerfile ran `uvicorn backend.main:app` which expected a package that didn't properly exist.

```
Before:                        After:
backend/                       backend/
  main.py          ← flat       app/
  finance.py                     main.py
  indicators.py                  finance.py
  tests/                         indicators.py
                                 domain/
                                   features.py
                                   scoring.py
                               tests/
```

**Fix:** Created `backend/app/` as the canonical Python package:

```
backend/
  app/
    __init__.py
    main.py          → FastAPI + middleware + routes
    finance.py       → yfinance wrapper + cache
    indicators.py    → facade for domain pipeline
    domain/
      __init__.py
      features.py    → raw data → clean features
      scoring.py     → features → bubble score
  tests/
    ...
```

**Run commands:**
- Local dev: `uvicorn app.main:app --reload` (from `backend/`)
- Docker: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Tests: `python -m pytest tests/ -v`

---

### 2. Domain Separation (`backend/app/domain/`)

**Problem:** The scoring module mixed data access (`info.get(...)`, `hist["Close"].iloc[...]`) with business logic (threshold evaluation). Any change to data source or scoring required modifying the same file.

**Fix:** Split into two pure layers:

**`features.py`** — takes raw Yahoo Finance data, returns clean feature dict:
```python
def extract_features(info, hist):
    return {
        "pe": info.get("trailingPE"),
        "revenue_growth": info.get("revenueGrowth"),
        "pb": info.get("priceToBook"),
        "volatility": _calc_volatility(hist),
        "momentum": _calc_momentum(hist),
    }
```

**`scoring.py`** — pure function over feature dict, no data access:
```python
def evaluate_features(features):
    for rule in INFO_RULES:
        value = features.get(rule["field"])
        if value is None:
            score += rule["missing_penalty"]
        else:
            for threshold, points, msg in rule["thresholds"]:
                if value > threshold:
                    score += points
```

**`indicators.py`** — thin backward-compatible facade:
```python
def bubble_score(info, hist=None):
    features = extract_features(info, hist)
    return evaluate_features(features)
```

**Benefits:**
- Feature engineering can be swapped independently of scoring rules
- Scoring rules can be loaded from config/DB in the future
- Both layers are independently testable with zero dependencies

---

### 3. Observability: Request ID + Latency Tracking (`backend/app/main.py`)

**Problem:** JSON logs existed but had no correlation ID or latency data. Tracing a single request across logs was impossible.

**Fix:** Added `observability_middleware` that runs before the rate limiter:

```python
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.time()
    response = await call_next(request)
    elapsed_ms = int((time.time() - start) * 1000)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    logger.info("Request completed", extra={"request_id": request_id, "latency_ms": elapsed_ms})
```

**JSON log output:**
```json
{"time": "...", "level": "INFO", "name": "...", "message": "Request completed", "request_id": "...", "latency_ms": 42}
```

Updated `JSONFormatter` to include `request_id` and `latency_ms` from log record extras.

---

### 4. Frontend API Mappers (`frontend/src/services/mappers.js`)

**Problem:** The UI depended directly on the backend's `StockResponse` JSON shape. Any backend change would break the frontend. Formatting logic (`marketCap`, `revenueGrowth`) was mixed into the Vue template.

**Fix:** Created a mapper layer that decouples API data from UI model:

```javascript
export function mapStockResponse(data) {
  return {
    ...data,
    metrics: {
      ...data.metrics,
      revenueGrowthDisplay: m.revenueGrowth != null
        ? (m.revenueGrowth * 100).toFixed(1) + '%' : '--',
      marketCapDisplay: formatMarketCap(m.marketCap),
    }
  }
}

export function toErrorMessage(error) {
  if (error.message.includes('404')) return 'No data found for this ticker'
  if (error.message.includes('429')) return 'Too many requests. Please wait.'
  ...
}
```

**Template changes:**
- `{{ data.metrics.revenueGrowthDisplay }}` replaces inline ternary
- `{{ data.metrics.marketCapDisplay }}` replaces `formatMarketCap()` call
- `toErrorMessage(e)` replaces raw `e.message`
- Removed `formatMarketCap` from component script

---

### 5. Contract & Snapshot Tests (`backend/tests/test_indicators.py`)

**Problem:** No contract validation — API schema could drift from OpenAPI spec without detection. No snapshot tests — scoring changes could silently alter known outputs.

**Fix:** Added two tests:

**OpenAPI schema validation:**
```python
def test_contract_openapi_schema():
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert "/stock/{ticker}" in schema["paths"]
    assert "/health" in schema["paths"]
    assert "/health/live" in schema["paths"]
    assert "/health/ready" in schema["paths"]
```

**Scoring snapshot:**
```python
def test_scoring_snapshot_known_input():
    score, reasons = bubble_score({
        "trailingPE": 45, "revenueGrowth": 0.35, "priceToBook": 15,
    })
    assert score == 5
    assert len(reasons) == 5
```

---

### 6. Docker Hardening (`backend/Dockerfile`, `docker-compose.yml`)

**Problem:** No healthcheck, no restart policy, no non-root user in Docker.

**Fix:**
- Added `HEALTHCHECK --interval=30s --timeout=5s --start-period=10s` checking `/health/live`
- Added `restart: unless-stopped` to both services in docker-compose
- `appuser` non-root user (already done in earlier pass)
- `depends_on` with `condition: service_started` for frontend

---

## Files Changed

| File | Status | Changes |
|------|--------|---------|
| `backend/app/__init__.py` | **Created** | Package marker |
| `backend/app/domain/__init__.py` | **Created** | Package marker |
| `backend/app/domain/features.py` | **Created** | Pure feature extraction from raw Yahoo data |
| `backend/app/domain/scoring.py` | **Created** | Pure rule evaluation against features |
| `backend/app/main.py` | **Moved** | From `backend/main.py`; added observability middleware |
| `backend/app/finance.py` | **Moved** | From `backend/finance.py`; unchanged content |
| `backend/app/indicators.py` | **Moved** | From `backend/indicators.py`; now a facade over domain |
| `backend/main.py` | **Deleted** | Replaced by `app/main.py` |
| `backend/finance.py` | **Deleted** | Replaced by `app/finance.py` |
| `backend/indicators.py` | **Deleted** | Replaced by `app/indicators.py` |
| `backend/tests/test_api.py` | Modified | Updated imports + patch targets to `app.` |
| `backend/tests/test_finance.py` | Modified | Updated imports + patch targets to `app.` |
| `backend/tests/test_indicators.py` | Modified | Updated imports; added contract + snapshot tests |
| `backend/Dockerfile` | Modified | `app.main:app`, healthcheck |
| `docker-compose.yml` | Modified | `restart: unless-stopped`, `depends_on` |
| `frontend/src/services/mappers.js` | **Created** | `mapStockResponse()`, `toErrorMessage()` |
| `frontend/src/components/StockAnalyzer.vue` | Modified | Uses mapper; removed `formatMarketCap` |

---

## Verification

```
Backend tests:  20 passed in 0.96s
Frontend build: passed (704ms, 3 assets, ~29KB gzipped)
Uvicorn start:  OK (uvicorn app.main:app)
```
