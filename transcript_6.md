# AI Bubble Detector — Company Picker

## Overview

Added a browsable company list to the frontend so users can select tickers by sector instead of typing them manually. Covers 54 stocks across 9 sectors with color-coded risk badges.

---

## Changes Applied

### 1. Created `frontend/src/components/CompanyList.vue` (new, 262 lines)

A standalone component rendering an accordion-style list of companies organized by sector:

- **9 collapsible sector groups** — Financial Services, Technology, Healthcare & Biotech, Energy & Commodities, Industrials & Manufacturing, Consumer, Auto & Mobility, Communication / Media, High-Risk / Speculative Growth
- Each company row shows: ticker (purple, bold), company name, and a color-coded risk badge
- Risk badge colors: `low`→green, `low/medium`→light green, `medium`→yellow, `medium/high`→orange, `high`→red, `very high`→bright red
- Clicking a company emits a `select` event with the ticker
- Highlights the currently active ticker with a purple border
- Starts all sectors closed; clicking a sector header toggles it open/closed

```vue
<CompanyList @select="onSelect" :selectedTicker="ticker" />
```

### 2. Modified `frontend/src/components/StockAnalyzer.vue` (2 changes)

- Added `import CompanyList from './CompanyList.vue'`
- Added `onSelect(tickerValue)` handler that sets the ticker and immediately triggers `analyze()`
- Rendered `<CompanyList>` above the search box

---

## Files Changed

| File | Status | Changes |
|------|--------|---------|
| `frontend/src/components/CompanyList.vue` | **Created** | 262-line component with sector data + accordion UI |
| `frontend/src/components/StockAnalyzer.vue` | Modified | Added import, template usage, and `onSelect` handler |

---

## Verification

```
frontend build: passed (625ms, 3 assets, ~73KB gzipped)
```

Component data covers all 54 requested tickers across 9 sectors with correct ticker symbols and risk classifications.
