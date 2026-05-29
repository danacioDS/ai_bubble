Te lo mejoré a nivel **portfolio/hiring (más claro, más creíble y más “senior”)**, manteniendo tu contenido pero arreglando narrativa, consistencia y “impacto”.

---

# 🚀 README mejorado

```md
# 🔍 AI Bubble Detector

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.4-brightgreen.svg)](https://vuejs.org)
[![Docker](https://img.shields.io/badge/Docker-✓-blue.svg)](https://docker.com)
[![Tests](https://img.shields.io/badge/tests-15-passing-brightgreen.svg)](backend/tests)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **AI Bubble Detector** analyzes potential overvaluation signals in stocks using a heuristic scoring engine based on fundamentals, growth, and valuation metrics.

Backend built with **FastAPI + Yahoo Finance**, frontend with **Vue 3 + Vite**, fully containerized with Docker.

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

## 🧠 Live Example

| Ticker | Company | Score | Risk Level | Key Signals |
|--------|--------|------|------------|--------------|
| PLTR | Palantir | 6 | 🔴 High Risk | High P/E, strong growth, elevated P/B |
| NVDA | NVIDIA | 8 | 🔴 Bubble Risk | Extreme valuation + momentum |
| JPM | JPMorgan | 0 | 🟢 Stable | Low valuation, stable fundamentals |
| TSLA | Tesla | 6 | 🟠 Speculative | Volatility + growth premium |

---

## ✨ Features

### 📈 Financial Intelligence
- Heuristic **bubble scoring system (0–9)**
- Multi-factor analysis:
  - P/E ratio
  - Forward P/E
  - Revenue growth
  - Price-to-book
  - Market cap
- Risk classification: Stable → Bubble Risk

### ⚡ Real-time Data
- Yahoo Finance integration (`yfinance`)
- Live stock fundamentals
- 6-month historical price data

### 📊 Frontend Experience
- Interactive stock search
- SVG risk score visualization
- Price history chart (no external chart libraries)
- Company presets for fast exploration
- Dark UI optimized for readability

### 🧩 Engineering Features
- FastAPI backend with typed models (Pydantic)
- Request cancellation (AbortController)
- In-memory rate limiting
- Structured JSON logging
- CORS configured for Docker + browser separation
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

````

---

## 🚀 Quick Start

### 🐳 Docker (Recommended)

```bash
git clone https://github.com/danacio/ai-bubble-detector.git
cd ai-bubble-detector

docker compose up --build

# Frontend
http://localhost

# Backend API
http://localhost:8000/docs
````

---

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

http://localhost:5173
```

---

## 📡 API Endpoints

### GET `/stock/{ticker}`

Returns stock analysis:

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

---

### GET `/stock/{ticker}/history`

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

| Metric         | Condition | Score |
| -------------- | --------- | ----- |
| P/E            | > 40      | +2    |
| Revenue Growth | > 30%     | +2    |
| Price-to-Book  | > 10      | +1    |
| Momentum       | High      | +2    |

### Interpretation

| Score | Label       |
| ----- | ----------- |
| 0–2   | Stable      |
| 3–5   | Elevated    |
| 6–7   | Speculative |
| 8–9   | Bubble Risk |

---

## 🧪 Testing

```bash
cd backend
pytest -v
```

* API contract tests
* scoring engine tests
* integration tests (FastAPI TestClient)

---

## 🐳 Deployment

```bash
docker compose up --build
```

Services:

* Frontend → [http://localhost](http://localhost)
* Backend → [http://localhost:8000](http://localhost:8000)
* Docs → [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠️ Tech Stack

**Backend**

* FastAPI
* Pydantic
* yfinance
* Python 3.12

**Frontend**

* Vue 3 (Composition API)
* Vite
* SVG-based charts

**Infra**

* Docker
* Docker Compose
* Nginx (frontend serving)

---

## 👤 Author

**Daniel Canedo**

* GitHub: [https://github.com/danacio](https://github.com/danacio)

---

## ⭐ Notes

This project is a **portfolio-grade financial analytics tool** demonstrating:

* Full-stack architecture
* Real-time data integration
* UI data visualization
* API design + validation
* Production-ready Docker setup

```




