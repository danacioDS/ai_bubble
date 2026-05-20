# AI Bubble Detector — Consistency Analysis

## Scope

Cross-file consistency audit of `backend/main.py`, `backend/finance.py`, `backend/indicators.py`, and the test suite.

---

## Findings

### 1. Flaky Test: `test_warning_range` (`backend/tests/test_indicators.py:39-47`)

```python
def test_warning_range():
    hist = make_hist(np.linspace(100, 130, 200) + np.random.normal(0, 3, 200))
    score, reasons = bubble_score({
        "trailingPE": 35,
        "revenueGrowth": 0.2,
        "priceToBook": 12,
    }, hist)
    assert 4 <= score <= 5
```

The test injects `np.random.normal(0, 3, 200)` noise into the price series. The volatility and momentum scores depend on this randomness, so the raw score can vary run-to-run. A tight `4 <= score <= 5` assertion will flake under certain random seeds.

**Fix:** Relax the bound to a range that accounts for noise (e.g. `3 <= score <= 6`), or seed the RNG, or use a deterministic price series.

---

### 2. `Date` Column Fragility (`backend/finance.py:52-53`, `backend/main.py:140`)

```python
# finance.py:52-53
hist = hist.reset_index()
hist = hist[["Date", "Close"]].dropna()

# main.py:138-141
PricePoint(
    date=str(row["Date"].date()),
    close=float(row["Close"])
)
```

`yfinance.Ticker.history()` returns a DataFrame with a `DatetimeIndex`. Whether the index is named `"Date"` or `None` depends on the yfinance version. If unnamed, `reset_index()` creates a column named `"index"` instead of `"Date"`, and both lines above will throw `KeyError`.

**Fix:** Explicitly rename the index before resetting: `hist = hist.rename_axis("Date").reset_index()`. Or, do: `hist.reset_index(inplace=True); hist.rename(columns={"index": "Date"}, inplace=True)` as a fallback.

---

### 3. Redundant `info or {}` Ordering (`backend/main.py:102-103`)

```python
score, reasons = bubble_score(info or {}, hist)
info = info or {}
```

`info or {}` is passed to `bubble_score` on line 102, then `info` is reassigned to the same expression on line 103. The reassignment does not affect the call already made. Not a bug, but the ordering is misleading — the defensive copy should logically come before it's consumed.

**Fix:** Move `info = info or {}` above the `bubble_score` call.

---

### 4. Incomplete Return Type Check (`backend/tests/test_finance.py:14-17`)

```python
def test_stock_data_shape():
    info, hist, price = get_stock_data("MSFT")
    assert isinstance(info, dict)
    assert price is None or isinstance(price, (int, float))
```

Only `info` and `price` are type-checked from the 3-tuple. `hist` (the second return value, a `pd.DataFrame` or `None`) is never asserted. A regression that broke `hist`'s shape would pass this test.

**Fix:** Add `assert hist is None or isinstance(hist, pd.DataFrame)` and import `pandas` at the top.

---

### 5. Empty `info` Silently Returns Score 0 Instead of 404 (`backend/main.py:96-103`)

```python
if not info and hist is None:
    raise HTTPException(status_code=404, detail="No data found for ticker")

score, reasons = bubble_score(info or {}, hist)
info = info or {}

return StockResponse(
    ticker=ticker,
    ...
    score=score,
    reasons=reasons,
)
```

The 404 guard fires only when **both** `info` is falsy **and** `hist` is `None`. If `info` is an empty dict `{}` (falsy) but `hist` is a valid DataFrame, execution continues to `bubble_score({}, hist)`, which returns `score=0` and `reasons=["No financial data available"]`. The response is a 200 with zero score rather than a 404 — potentially confusing for users querying tickers with price history but no fundamental data.

**Fix:** Change the condition to `if not info or hist is None` (i.e., treat missing fundamentals as "no data" too), or handle the empty-info case explicitly.

---

### 6. Timeout Mechanism Is Unix-Only (`backend/finance.py:27-34`)

```python
def _setup_alarm(seconds):
    try:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(seconds)
        return True
    except ValueError:
        logger.warning("Signal alarms not available (not in main thread)")
        return False
```

`signal.SIGALRM` is POSIX-only. On Windows, `signal.signal()` raises `ValueError` for `SIGALRM`, which is caught and logged. The function falls through to `_fetch_stock_data()` with no timeout protection. Also fails in threaded environments (e.g., uvicorn with multiple workers).

**Fix:** Use `concurrent.futures.ThreadPoolExecutor` with a timeout, or `asyncio.wait_for`, for cross-platform timeout support.

---

### 7. Cache Stores Mutable DataFrame Objects (`backend/finance.py:93`)

```python
cache[ticker] = result  # result contains hist (pd.DataFrame)
```

`TTLCache` stores the raw `pd.DataFrame` returned by `_fetch_stock_data`. If a caller mutates the returned `hist` (e.g., `hist.drop(...)`), subsequent cache hits receive the mutated object. Pydantic models in `main.py` do not mutate it, but nothing prevents future code from doing so.

**Fix:** Return a copy on cache hit: `return copy.deepcopy(cache[ticker])`, or document that the returned objects must not be mutated.

---

## Summary

| # | Severity | File | Issue |
|---|----------|------|-------|
| 1 | Medium | `tests/test_indicators.py:46` | Flaky assertion due to random noise |
| 2 | Medium | `finance.py:52-53`, `main.py:140` | `Date` column name depends on yfinance version |
| 3 | Low | `main.py:102-103` | Redundant `info or {}` ordering |
| 4 | Low | `tests/test_finance.py:14-17` | `hist` return value not type-checked |
| 5 | Low | `main.py:96` | Empty `info` yields 200/0 instead of 404 |
| 6 | Low | `finance.py:27-34` | `SIGALRM` timeout is Unix-only |
| 7 | Low | `finance.py:93` | Cache stores mutable DataFrames |
