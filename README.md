# AI Bubble Detector

Detect overvaluation signals in AI-related stocks using fundamental and technical indicators. Backend powered by FastAPI / Yahoo Finance, frontend built with Vue 3 + Vite.

## Features

- **Bubble Score** — heuristic risk score (0–9) based on P/E, revenue growth, P/B, volatility, and momentum
- **Live Data** — fetches real-time fundamentals and price history via Yahoo Finance
- **SVG Score Ring** — visual indicator with Stable / Elevated / Speculative / Bubble Risk thresholds
- **Price History Chart** — 6-month normalized SVG polyline
- **Request Cancellation** — AbortController prevents stale responses during rapid searches
- **Server-Side Caching** — 5-minute TTL cache reduces Yahoo Finance API calls
- **Structured Logging** — timestamped, hierarchical logger output across all modules
- **Timeout Handling** — configurable SIGALRM-based timeout for upstream requests
- **Health Check** — `GET /health` endpoint for monitoring
- **Full Test Suite** — 15 tests covering contracts, scoring, and integration
- **Docker Support** — one-command full-stack deployment
- **GitHub Actions CI** — automated pytest + build on every push
- **Dark Theme** — built-in dark mode UI

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | FastAPI (Python 3.12) |
| ASGI server | Uvicorn |
| Data source | yfinance (Yahoo Finance) |
| Processing | pandas, numpy |
| Response models | Pydantic v2 |
| Caching | cachetools TTLCache |
| Frontend framework | Vue 3 (Composition API, script setup) |
| Build tool | Vite 5 |
| Styling | CSS scoped, dark theme |
| Charts | SVG inline (zero external dependencies) |
| Containerization | Docker, docker-compose |
| CI | GitHub Actions |

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vite)                │
│                                                          │
│  StockAnalyzer.vue                                       │
│    ├── Search input + Analyze button                     │
│    ├── SVG score ring (0–9)                              │
│    ├── Metrics grid (P/E, growth, P/B, market cap)       │
│    ├── Bubble signals list                               │
│    └── Price history SVG chart                           │
│                                                          │
│  State: ref()/computed() (no Pinia/Vuex)                 │
│  HTTP: fetch + AbortController (race-safe)               │
└───────────────────────┬──────────────────────────────────┘
                        │ GET /stock/{ticker}
                        │ GET /stock/{ticker}/history
                        │ GET /health
                        ▼
┌──────────────────────────────────────────────────────────┐
│                    Backend (FastAPI + Uvicorn)             │
│                                                          │
│  main.py        → REST routes + CORS + Pydantic models   │
│  finance.py     → yfinance wrapper + TTLCache + timeout  │
│  indicators.py  → Heuristic scoring engine               │
│                                                          │
│  GET  /health                → Health check              │
│  GET  /stock/{ticker}        → Bubble analysis           │
│  GET  /stock/{ticker}/history → Historical prices        │
│                                                          │
│  Logging:    structured (timestamp + level + module)     │
│  Timeouts:   SIGALRM (configurable, fallback-safe)       │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
                Yahoo Finance (live data)
```

## API Endpoints

### GET /health

Returns service status.

```json
{
  "status": "ok"
}
```

### GET /stock/{ticker}

Analyze a stock for bubble risk.

```json
{
  "ticker": "NVDA",
  "name": "NVIDIA Corporation",
  "price": 880.50,
  "metrics": {
    "pe": 75.2,
    "forwardPe": 65.1,
    "revenueGrowth": 0.85,
    "priceToBook": 45.3,
    "marketCap": 2200000000000
  },
  "score": 8,
  "reasons": [
    "P/E very high (75.2)",
    "Strong revenue growth (85.0%)",
    "High P/B (45.3)"
  ]
}
```

### GET /stock/{ticker}/history

Get 6-month price history.

```json
{
  "prices": [
    { "date": "2024-01-15", "close": 548.22 },
    { "date": "2024-01-16", "close": 563.82 }
  ]
}
```

### Error Responses

| Status | Meaning |
|--------|---------|
| 400 | Invalid ticker format |
| 404 | Ticker not found / no data |
| 504 | Upstream finance provider timeout |

Interactive API docs available at `http://localhost:8000/docs`.

## Local Development

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
cp .env.example .env            # optional: configure YAHOO_TIMEOUT, CACHE_TTL
pip install -r requirements.txt
uvicorn main:app --reload
# http://127.0.0.1:8000
# Interactive docs at http://127.0.0.1:8000/docs
```

### Frontend

```bash
cd frontend
cp .env.example .env            # optional: configure VITE_API_URL
npm install
npm run dev
# http://localhost:5173
```

## Docker Setup

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

## Environment Configuration

Copy the example env files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `YAHOO_TIMEOUT` | 10 | Seconds before Yahoo Finance request times out |
| `CACHE_TTL` | 300 | Cache expiry in seconds (5 min) |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

## Testing

### Backend

```bash
cd backend
python -m pytest tests/ -v
```

| Test file | Type | Tests | Coverage |
|-----------|------|-------|----------|
| `tests/test_api.py` | FastAPI TestClient integration | 5 | Endpoint shape, validation, nullable fields |
| `tests/test_finance.py` | Finance contract tests | 2 | Return count, value types |
| `tests/test_indicators.py` | Deterministic scoring fixtures | 8 | Extreme case, safe case, bounds fuzz (100 iters) |

**15 tests total** — including live Yahoo Finance calls, schema validation, score bounds, and synthetic fixture tests.

### Frontend

```bash
cd frontend
npm run build        # verify production build succeeds
```

## Scoring Methodology

### Indicator Thresholds

| Indicator | Threshold | Points |
|-----------|-----------|--------|
| P/E Ratio | > 40 | +2 |
| | > 30 (≤ 40) | +1 |
| Revenue Growth | > 30% | +2 |
| | > 15% (≤ 30%) | +1 |
| Price-to-Book | > 10 | +1 |
| Daily Volatility (annualized) | > 50% | +1 |
| 6-Month Momentum | > 50% | +2 |
| | > 20% (≤ 50%) | +1 |

Missing data incurs fractional penalties instead of full indicator scores (max penalty: +1.8 across all 5 factors).

### Score Interpretation

| Range | Label | Color | Meaning |
|-------|-------|-------|---------|
| 0–2 | Stable | Green | No significant overvaluation signals |
| 3–5 | Elevated | Yellow | Some indicators warrant attention |
| 6–7 | Speculative | Orange | Multiple signals at elevated thresholds |
| 8–9 | Bubble Risk | Red | Strong overvaluation across indicators |

## CI

Every commit to `main` (and every PR) runs:

```yaml
backend:
  - pytest (15 tests, Python 3.12)

frontend:
  - pnpm build (Vite production bundle)
```

See `.github/workflows/ci.yml` for full pipeline definition.

## Project Status

This project began as a full-stack prototype and has been hardened through three passes:

| Pass | Focus | Output |
|------|-------|--------|
| 1 | Bugfix | Runtime crashes, schema mismatches, Docker networking |
| 2 | Contracts | Pydantic models, integration tests, AbortController |
| 3 | Production | Caching, timeouts, structured logging, CI, README |

See `transcript.md` and `transcript_2.md` for the complete engineering review history.

## Future Improvements

- Add persistent caching (Redis) for Yahoo Finance responses
- Migrate frontend to TypeScript
- Add Vue Router for multiple views / comparison tool
- Integrate professional chart library (Chart.js, D3)
- Add rate limiting and API key authentication
- Deploy frontend to Vercel + backend to Render/Railway
- Add load testing and performance benchmarking
