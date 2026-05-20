# AI Bubble Detector — Data Layer Extraction & Backend-Driven Risk

## Overview

Refactored the company picker from transcript_6.md: extracted hardcoded data to a JSON file, moved risk labeling to the backend, and added search/filtering. Frontend build passes (745ms), 15/15 backend tests pass.

---

## Changes Applied

### 1. Extracted Data to JSON (`frontend/src/data/companies.json`, new)

**Problem:** 59 companies were hardcoded inside `CompanyList.vue`, creating a maintenance bottleneck — duplication risk between frontend and backend, and difficulty updating company metadata without touching component code.

**Fix:** Moved all company data to a standalone JSON file:

```json
[
  {
    "name": "Technology (Growth + High Volatility)",
    "icon": "💻",
    "companies": [
      { "ticker": "AAPL", "name": "Apple" },
      { "ticker": "MSFT", "name": "Microsoft" }
    ]
  }
]
```

Coverage: 59 companies across 9 sectors, matching the original set.

**Benefits:**
- UI is now a rendering client, not a data holder
- JSON can be updated independently of component code
- Data is reusable across the frontend (search, filtering, future features)

---

### 2. Backend-Driven Risk Labels (`backend/main.py`)

**Problem:** Risk labels (`low`, `medium/high`, etc.) were static strings embedded in the frontend — subjective, unversioned, and inconsistent with the backend's bubble scoring logic.

**Fix:** Added `riskLabel` to the `StockResponse` model, computed from the actual bubble score:

```python
def score_to_risk_label(score: int) -> str:
    if score >= 9: return "very high"
    if score >= 7: return "high"
    if score >= 6: return "medium/high"
    if score >= 4: return "medium"
    if score >= 3: return "low/medium"
    return "low"


class StockResponse(BaseModel):
    ticker: str
    name: str | None = None
    price: float | None = None
    metrics: Metrics
    score: int
    riskLabel: str   # ← new, backend-computed
    reasons: list[str]
```

**Frontend:** `StockAnalyzer.vue` now displays a color-coded `riskLabel` badge in the card header, using the same CSS classes as the old static badges — but the source of truth is now the backend.

---

### 3. Search Filtering (`frontend/src/components/CompanyList.vue`)

**Problem:** 59 items in an accordion list is borderline for UX — users must scroll through sectors instead of typing to find a ticker.

**Fix:** Added a search input that filters by ticker or company name:

```vue
<input v-model="searchQuery" placeholder="Search ticker or company..." />
```

**Behavior:**
- Filters in real-time as the user types
- Matches against ticker symbol or company name (case-insensitive)
- Empty sectors are hidden
- "No companies match" message shown when query has no results
- All matching sectors auto-expand when a search is active; accordion behavior restored when search is cleared

---

### 4. Updated Test Assertions (`backend/tests/test_api.py`)

Added `riskLabel` field validation:

```python
assert "riskLabel" in body
assert body["riskLabel"] in ("low", "low/medium", "medium", "medium/high", "high", "very high")
```

---

## Files Changed

| File | Status | Changes |
|------|--------|---------|
| `frontend/src/data/companies.json` | **Created** | 59 companies across 9 sectors (ticker + name only, no risk) |
| `frontend/src/components/CompanyList.vue` | Modified | Replaced hardcoded data with JSON import; added search input with real-time filtering |
| `frontend/src/components/StockAnalyzer.vue` | Modified | Added `riskLabel` badge to card header; added `riskLabelClass()` helper |
| `backend/main.py` | Modified | Added `score_to_risk_label()` function; added `riskLabel` field to `StockResponse` |
| `backend/tests/test_api.py` | Modified | Added `riskLabel` shape assertion |

---

## Verification

```
Frontend build: passed (745ms, 3 assets, ~31KB gzipped)
Backend tests:  15 passed in 6.39s
```
