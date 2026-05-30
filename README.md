# 🔍 AI Bubble Detector

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.4-brightgreen.svg)](https://vuejs.org)
[![Docker](https://img.shields.io/badge/Docker-✓-blue.svg)](https://docker.com)
[![Tests](https://img.shields.io/badge/tests-22-passing-brightgreen.svg)](backend/tests)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **AI Bubble Detector** analyzes potential overvaluation signals in stocks using a heuristic scoring engine driven by fundamentals, growth, and valuation metrics.

Backend built with **FastAPI + Yahoo Finance**, frontend with **Vue 3 + Vite**, fully containerized with Docker.

---

## ⚠️ Disclaimer

The Bubble Score is a heuristic indicator based on fixed thresholds (P/E, momentum, volatility). It has not been backtested or calibrated against historical data. It is not financial advice and should not be used as the sole basis for investment decisions.

---

## 📊 Overview

This project evaluates whether a stock shows **bubble-like behavior** by combining:

- Valuation metrics (P/E, P/B)
- Growth indicators (revenue growth)
- Market data (price, market cap)
- Momentum heuristics
- Simple risk scoring model (0–9)

Each stock receives a **bubble risk score + explanation signals**.

---

## 🧠 Live Examples

| Ticker | Company | Score | Risk Level | Key Signals |
|--------|---------|-------|------------|-------------|
| PLTR | Palantir | 6 | 🔴 High Risk | High P/E, strong growth, elevated P/B |
| NVDA | NVIDIA | 8 | 🔴 Bubble Risk | Extreme valuation + momentum |
| JPM | JPMorgan | 0 | 🟢 Stable | Low valuation, stable fundamentals |
| TSLA | Tesla | 6 | 🟠 Speculative | Volatility + growth premium |

---

## ✨ Features

### 📈 Financial Intelligence
- Heuristic **bubble scoring system (0–9)**
- Multi-factor analysis: P/E, Forward P/E, revenue growth, P/B, market cap
- Risk classification from Stable → Bubble Risk

### ⚡ Real-time Data
- Yahoo Finance integration via `yfinance`
- Live stock fundamentals and pricing
- 6-month historical price data

### 📊 Frontend
- Interactive stock search
- SVG risk score gauge and price history chart (zero chart library dependencies)
- Company presets for fast exploration
- Dark UI optimized for readability

### 🧩 Engineering
- FastAPI backend with Pydantic v2 typed models
- In-memory rate limiting per IP
- Structured JSON logging with request tracing
- CORS configurable via environment variable
- Docker Compose full-stack deployment

---

## 🏗️ Architecture

```
Frontend (Vue 3 + Vite)
│
├── StockAnalyzer UI
├── SVG visualization (score + chart)
└── API client (fetch + AbortController)
│
▼
Backend (FastAPI)
├── /stock/{ticker}
├── /stock/{ticker}/history
├── /health
├── Bubble scoring engine
└── Yahoo Finance wrapper
│
▼
Yahoo Finance (yfinance)
```

---

## 🚀 Quick Start

### 🐳 Docker (Recommended)

```bash
git clone https://github.com/danacio/ai-bubble-detector.git
cd ai-bubble-detector

docker compose up --build

# Frontend:  http://localhost
# Backend:   http://localhost:8000/docs
```

### 💻 Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev

# http://localhost:5173
```

---

## 📡 API

### `GET /stock/{ticker}`

Returns a full stock analysis including metrics, score, and risk signals.

```json
{
  "ticker": "NVDA",
  "price": 880.5,
  "score": 8,
  "riskLabel": "high",
  "metrics": {
    "pe": 75.2,
    "revenueGrowth": 0.85,
    "priceToBook": 45.3
  },
  "reasons": [
    "High P/E ratio",
    "Strong revenue growth",
    "High valuation multiple"
  ]
}
```

### `GET /stock/{ticker}/history`

Returns 6 months of daily closing prices.

```json
{
  "prices": [
    { "date": "2024-01-15", "close": 548.22 },
    { "date": "2024-01-16", "close": 563.82 }
  ]
}
```

---

## 🧮 Scoring System

| Metric | Condition | Score |
|--------|-----------|-------|
| P/E | > 40 | +2 |
| Revenue Growth | > 30% | +2 |
| Price-to-Book | > 10 | +1 |
| Momentum | High | +2 |

### Risk Interpretation

| Score | Label |
|-------|-------|
| 0–2 | Stable |
| 3–5 | Elevated |
| 6–7 | Speculative |
| 8–9 | Bubble Risk |

---

## 🧪 Testing

```bash
cd backend
pytest -v
```

- API contract & integration tests (FastAPI TestClient)
- Scoring engine unit tests
- OpenAPI schema validation

---

## 🐳 Deployment

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## 🛠️ Tech Stack

**Backend:** FastAPI, Pydantic, yfinance, Python 3.12

**Frontend:** Vue 3 (Composition API), Vite, SVG-based charts

**Infra:** Docker, Docker Compose, Nginx

---

## 👤 Author

**Daniel Canedo** — [github.com/danacio](https://github.com/danacio)

---

## 📄 License

MIT
