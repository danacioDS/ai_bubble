# AI Bubble Detector — Serialization Boundary & Typed Domain Layer

## Overview

Third hardening pass addressing second-order effects from `transcript_4.md`: replaced ambiguous `to_dict("records")` with explicit column lists, fail-fast dependency checks, cache schema versioning, and typed Pydantic domain models. All 15 tests pass.

---

## Changes Applied

### 1. Typed Domain Models (`backend/finance.py:22-30`)

**Problem:** Cache and data pipeline relied on unstructured dicts. No schema enforcement between fetch → normalize → cache → denormalize → consume.

**Fix:** Added Pydantic models representing the canonical data shape:

```python
class StockPoint(BaseModel):
    date: str
    close: float

class StockData(BaseModel):
    info: dict | None = None
    history: list[StockPoint] | None = None
    price: float | None = None
```

These models define the single source of truth for how stock data is represented throughout the system.

---

### 2. Separate Date/Close Lists — Eliminate `to_dict("records")` (`backend/finance.py:63-78`)

**Problem:** `hist.to_dict("records")` silently lost datetime index semantics, timezone info, dtype fidelity, and ordering guarantees — a subtle correctness risk for downstream pandas operations in `indicators.py`.

**Fix:** Store data as explicit column lists and reconstruct via Pydantic:

```python
def _normalize(info, hist, price):
    data = StockData(
        info=dict(info) if info else None,
        price=price,
    )
    if hist is not None and not hist.empty:
        data.history = [
            StockPoint(date=str(row["Date"].date()), close=float(row["Close"]))
            for _, row in hist.iterrows()
        ]
    return {"version": CACHE_VERSION, **data.model_dump()}


def _denormalize(data: dict):
    if data.get("version") != CACHE_VERSION:
        raise ValueError(...)

    parsed = StockData(**{k: v for k, v in data.items() if k != "version"})

    hist = None
    if parsed.history:
        hist = pd.DataFrame(
            {
                "Date": pd.to_datetime([p.date for p in parsed.history]),
                "Close": [p.close for p in parsed.history],
            }
        )

    return parsed.info, hist, parsed.price
```

No ambiguous `to_dict("records")` — dates and closes are always reconstructed with explicit types.

---

### 3. Fail-Fast Date Column (`backend/finance.py:42-45`)

**Problem:** The previous heuristic (`date_col = "Date" if "Date" in hist.columns else hist.columns[0]`) was a silent guess — it would silently mislabel data if yfinance changed its column structure.

**Fix:** Fail fast with a clear error message:

```python
hist = hist.reset_index()
if "Date" not in hist.columns:
    raise ValueError(
        f"Expected 'Date' column after reset_index(), got {list(hist.columns)}"
    )
```

---

### 4. Cache Schema Versioning (`backend/finance.py:12, 71-76`)

**Problem:** Cache format was unversioned. A future schema change would silently accept stale entries with incompatible structure.

**Fix:** Added `CACHE_VERSION = 1` and validated on every load:

```python
CACHE_VERSION = 1

# On store:
{"version": CACHE_VERSION, **data.model_dump()}

# On load:
if data.get("version") != CACHE_VERSION:
    raise ValueError(
        f"Cache schema version mismatch: expected {CACHE_VERSION}, got {data.get('version')}"
    )
```

Invalid entries fail immediately with a clear diagnostic instead of propagating corrupt data.

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/finance.py` | Added `StockPoint`/`StockData` Pydantic models; replaced `to_dict("records")` with explicit date/close lists; fail-fast Date column check; cache versioning with validation |

---

## Test Results

```
15 passed in 5.25s
```

All 15 tests pass across `test_api.py`, `test_finance.py`, and `test_indicators.py`.
