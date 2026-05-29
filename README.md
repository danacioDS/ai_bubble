# AI Bubble Detector

Detect overvaluation signals in AI-related stocks using fundamental and technical indicators. Backend powered by FastAPI + Yahoo Finance, frontend built with Vue 3 + Vite.

## Features

- **Bubble Score** — heuristic risk score (0–9) based on P/E, revenue growth, P/B, volatility, and momentum
- **Live Data** — real-time fundamentals and price history via Yahoo Finance
- **SVG Score Ring** — visual indicator with Stable / Elevated / Speculative / Bubble Risk thresholds
- **Price History Chart** — 6-month normalized SVG polyline
- **Request Cancellation** — AbortController prevents stale responses during rapid searches
- **Server-Side Caching** — 5-minute TTL cache reduces Yahoo Finance API calls
- **Structured Logging** — JSON-formatted logs with request IDs and latency
- **Rate Limiting** — 60 requests/minute per IP
- **Timeout Handling** — configurable timeout for upstream requests
- **Health Checks** — `/health`, `/health/live`, `/health/ready` endpoints
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
│  Logging:    structured JSON (timestamp + level + module) │
│  Rate limit: 60 req/min per IP (in-memory sliding window)│
│  Timeouts:   ThreadPoolExecutor (configurable, fallback)  │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
                 Yahoo Finance (live data)
```

## API Endpoints

### GET /health

```json
{ "status": "ok" }
```

### GET /health/live

```json
{ "status": "alive" }
```

### GET /health/ready

```json
{ "status": "ready" }
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
  "riskLabel": "high",
  "reasons": [
    "P/E very high (75.2)",
    "Strong revenue growth (85.0%)",
    "High P/B (45.3)"
  ]
}
```

### GET /stock/{ticker}/history

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
| 429 | Rate limit exceeded |
| 504 | Upstream finance provider timeout |

Interactive API docs available at `http://localhost:8000/docs`.

## Local Development

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
uvicorn main:app --reload
# http://127.0.0.1:8000
# API docs at http://127.0.0.1:8000/docs
```

### Frontend

```bash
cd frontend
cp .env.example .env
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

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `YAHOO_TIMEOUT` | 10 | Seconds before Yahoo Finance request times out |
| `CACHE_TTL` | 300 | Cache expiry in seconds (5 min) |
| `RATE_LIMIT_MAX` | 60 | Max requests per window |
| `RATE_LIMIT_WINDOW` | 60 | Rate limit window in seconds |

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

**15 tests total** — live Yahoo Finance calls, schema validation, score bounds, and synthetic fixture tests.

### Frontend

```bash
cd frontend
npm run build
```

## Scoring Methodology

### Indicator Thresholds

| Indicator | Threshold | Points |
|-----------|-----------|--------|
| P/E Ratio | > 40 | +2 |
|           | > 30 (≤ 40) | +1 |
| Revenue Growth | > 30% | +2 |
|                | > 15% (≤ 30%) | +1 |
| Price-to-Book | > 10 | +1 |
| Daily Volatility (annualized) | > 50% | +1 |
| 6-Month Momentum | > 50% | +2 |
|                  | > 20% (≤ 50%) | +1 |

Missing data incurs fractional penalties instead of full indicator scores (max penalty: +1.8 across 5 factors).

### Score Interpretation

| Range | Label | Color | Meaning |
|-------|-------|-------|---------|
| 0–2 | Stable | Green | No significant overvaluation signals |
| 3–5 | Elevated | Yellow | Some indicators warrant attention |
| 6–7 | Speculative | Orange | Multiple signals at elevated thresholds |
| 8–9 | Bubble Risk | Red | Strong overvaluation across indicators |

## CI

Every push to `main` (and every PR) runs:

```yaml
backend:
  - pytest (15 tests, Python 3.12)
frontend:
  - npm build (Vite production bundle)
```

See `.github/workflows/ci.yml` for the full pipeline definition.

## Project Status

This project began as a full-stack prototype and has been hardened through iterative improvements covering caching, timeouts, structured logging, rate limiting, CI, and a complete test suite.

## License

MIT
