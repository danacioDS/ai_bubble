# AI Bubble Detector

Full-stack app that detects financial bubbles in stocks using fundamental and technical indicators. Backend: Python/FastAPI — Frontend: Vue 3 + Vite.

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# http://127.0.0.1:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

### Docker
```bash
docker compose up --build
```

## Scoring

| Score | Label | Color |
|-------|-------|-------|
| 0–3 | Safe | Green |
| 4–5 | Warning | Yellow |
| 6–9 | Danger | Red |

Evaluates P/E ratio, revenue growth, price-to-book, volatility, and 6-month price change.

## API

- `GET /stock/{ticker}` — bubble analysis
- `GET /stock/{ticker}/history` — historical prices

Data sourced live from Yahoo Finance via `yfinance`.
