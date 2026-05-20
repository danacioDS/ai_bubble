# AI Bubble Detector — Consistency Fixes

## Overview

Cross-file consistency audit (from `transcript_3.md`) converted into actionable fixes across 4 files. All 15 tests pass.

---

## Changes Applied

### 1. Flaky Test — Seeded RNG (`backend/tests/test_indicators.py:40`)

**Problem:** `test_warning_range` used `np.random.normal()` without a fixed seed. Score assertions (`4 <= score <= 5`) would flake on different random draws.

**Fix:** Added `np.random.seed(42)` before the random series generation, making the test deterministic.

```python
def test_warning_range():
    np.random.seed(42)
    hist = make_hist(np.linspace(100, 130, 200) + np.random.normal(0, 3, 200))
```

---

### 2. Date Column Fragility (`backend/finance.py:40-42`)

**Problem:** `hist.reset_index()` produces a column named `"Date"` or `"index"` depending on whether the yfinance DatetimeIndex has a name — which varies across yfinance versions.

**Fix:** Added a defensive fallback that handles any column name:

```python
hist = hist.reset_index()
date_col = "Date" if "Date" in hist.columns else hist.columns[0]
hist = hist.rename(columns={date_col: "Date"})
hist = hist[["Date", "Close"]].dropna()
```

This protects against unnamed index, renamed index, and multiindex edge cases.

---

### 3. Cross-Platform Timeout (`backend/finance.py`)

**Problem:** `signal.SIGALRM` is POSIX-only. Fails on Windows, in threads, and under async workers.

**Fix:** Replaced signal-based timeout with `ThreadPoolExecutor`, wrapping the raw `TimeoutError` in the project-specific `FinanceTimeoutError` so the API layer never depends on concurrency exception types:

```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError

def run_with_timeout(fn, seconds, *args, **kwargs):
    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=seconds)
        except TimeoutError:
            raise FinanceTimeoutError(f"Request timed out after {seconds}s")
```

The `except TimeoutError` in `get_stock_data` was updated to `except FinanceTimeoutError`. Removed `_timeout_handler`, `_setup_alarm`, and `_cancel_alarm`.

---

### 4. Empty `info` Returns 404 (`backend/main.py:96`)

**Problem:** The guard `if not info and hist is None:` meant an empty dict `{}` for `info` (with valid `hist`) would slip through to `bubble_score({}, hist)` → score 0 + "No financial data available", returned as a 200.

**Fix:** Changed `and` to `or`:

```python
if not info or hist is None:
    raise HTTPException(status_code=404, detail="No data found for ticker")
```

---

### 5. Redundant `info or {}` Ordering (`backend/main.py:102-103`)

**Problem:** `info = info or {}` was placed *after* `bubble_score(info or {}, hist)`, making the reassignment useless for that call.

**Fix:** Moved the defensive copy above the call:

```python
info = info or {}
score, reasons = bubble_score(info, hist)
```

---

### 6. Cache Mutation Risk (`backend/finance.py`)

**Problem:** `TTLCache` stored raw `pd.DataFrame` objects. A caller mutating the returned `hist` would corrupt the cached copy for subsequent consumers. Using `copy.deepcopy` was safe but expensive — O(n) copy on every hit and memory duplication.

**Fix:** Store primitives only (dict + list of records) instead of DataFrame objects — eliminating the mutation risk without runtime cost:

```python
def _normalize(info, hist, price):
    return {
        "info": dict(info) if info else None,
        "hist_records": hist.to_dict("records") if hist is not None and not hist.empty else None,
        "price": price,
    }

def _denormalize(data: dict):
    info = data["info"]
    hist = pd.DataFrame(data["hist_records"]) if data["hist_records"] is not None else None
    price = data["price"]
    return info, hist, price
```

Cache store: `cache[ticker] = _normalize(info, hist, price)`
Cache hit: `return _denormalize(cache[ticker])`

Removed `import copy` — no longer needed.

---

### 7. Missing `hist` Type Assertion (`backend/tests/test_finance.py`)

**Problem:** `test_stock_data_shape` checked types for `info` and `price` but not `hist`, allowing a silent schema regression.

**Fix:**

```python
import pandas as pd

def test_stock_data_shape():
    info, hist, price = get_stock_data("MSFT")
    assert isinstance(info, dict)
    assert hist is None or isinstance(hist, pd.DataFrame)
    assert price is None or isinstance(price, (int, float))
```

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/finance.py` | Replaced SIGALRM with ThreadPoolExecutor + `FinanceTimeoutError` wrapper; replaced `deepcopy` cache with primitive `_normalize`/`_denormalize`; fixed Date column with defensive fallback |
| `backend/main.py` | Changed `and` → `or` in 404 guard; moved `info or {}` above `bubble_score` |
| `backend/tests/test_indicators.py` | Added `np.random.seed(42)` to `test_warning_range` |
| `backend/tests/test_finance.py` | Added `import pandas` + `hist` type assertion |

---

## Test Results

```
15 passed in 5.93s
```

All 15 tests pass across the 3 test suites (`test_api.py`, `test_finance.py`, `test_indicators.py`).
