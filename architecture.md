# AI Bubble Detector — Arquitectura

## Descripción General

Aplicación full-stack para detectar burbujas financieras en acciones usando datos fundamentales y técnicos. Backend en Python/FastAPI + frontend en Vue 3.

---

## Diagrama del Sistema

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3 + Vite)                             │
│                                                                          │
│  App.vue                                                                 │
│    ├── CompanyList.vue       → Selector de empresas por sector          │
│    └── StockAnalyzer.vue     → UI principal de análisis                 │
│          ├── Input de búsqueda (ticker)                                  │
│          ├── Anillo SVG de puntuación                                    │
│          ├── Grid de métricas (P/E, growth, P/B, market cap)            │
│          ├── Lista de señales de burbuja                                 │
│          └── Gráfico SVG de precio histórico                             │
│                                                                          │
│  API layer: services/api.js (fetch + AbortController)                    │
│  Mappers:  services/mappers.js (API → UI transform)                     │
│  Estado: ref()/computed() local (sin Pinia)                              │
│  Puerto: 5173 (dev) / 80 (producción con nginx)                         │
└──────────────────────┬───────────────────────────────────────────────────┘
                       │ GET http://backend:8000
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI + Uvicorn)                            │
│                                                                          │
│  app/main.py        → Rutas REST + CORS + middleware                    │
│    ├── GET /health              → Health check simple                    │
│    ├── GET /health/live         → Liveness probe                         │
│    ├── GET /health/ready        → Readiness probe                        │
│    ├── GET /stock/{ticker}      → Análisis de burbuja                   │
│    └── GET /stock/{ticker}/history → Precios históricos                 │
│                                                                          │
│  middleware:                                                             │
│    ├── Observability   → request_id + latency_ms (toda request)          │
│    ├── RateLimiter     → 60 req/min por IP (configurable)                │
│    └── JSONFormatter   → Logs estructurados en JSON                      │
│                                                                          │
│  app/finance.py   get_stock_data()                                      │
│    ├── yfinance (yf.Ticker) → Yahoo Finance API                          │
│    ├── TTLCache (128 entries, 5min TTL, schema versioned)                │
│    ├── ThreadPoolExecutor timeout (10s por defecto)                       │
│    └── Pydantic models: StockPoint, StockData                            │
│                                                                          │
│  app/indicators.py   bubble_score() → Facade                             │
│    └── app/domain/                                                       │
│         ├── features.py   → Extrae features limpias de raw data          │
│         │                    (pe, revenue_growth, pb, vol, momentum)     │
│         └── scoring.py    → Evalúa reglas data-driven contra features    │
│                              (INFO_RULES + HIST_RULES, puro, sin IO)     │
│                                                                          │
│  JSON Response: { score, riskLabel, reasons, ticker, ... }              │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Yahoo Finance (datos en vivo)
```

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Frontend framework** | Vue 3 (Composition API, `<script setup>`) |
| **Build tool** | Vite 5 |
| **Backend framework** | FastAPI (Python 3.12) |
| **Servidor ASGI** | Uvicorn |
| **Fuente de datos** | Yahoo Finance via `yfinance` |
| **Procesamiento** | pandas, numpy |
| **Validación** | Pydantic v2 (BaseModel) |
| **Caché** | cachetools TTLCache (128 entradas, 5min TTL, con versionado de schema) |
| **Timeout** | ThreadPoolExecutor (cross-platform, no depende de SIGALRM) |
| **Rate limiting** | In-memory (configurable por env) |
| **Logging** | JSON estructurado con request_id + latencia |
| **Estilos** | CSS scoped, tema oscuro (#0f172a) |
| **Gráficos** | SVG inline (sin librerías externas) |
| **Estado** | `ref()` / `computed()` local (sin Pinia/Vuex) |
| **HTTP client** | `fetch()` nativo con `AbortController` |
| **Mapper UI** | `services/mappers.js` (desacopla API de UI) |
| **Base de datos** | Ninguna (stateless, datos en vivo) |
| **Contenedores** | Docker multi-stage + docker-compose |
| **CI** | GitHub Actions (pytest + pnpm build) |

---

## Estructura del Proyecto

```
ai_bubble/
├── .github/workflows/ci.yml    # CI pipeline
├── docker-compose.yml          # Orquestación backend + frontend
├── architecture.md             # Este documento
├── transcript*.md              # Engineering journal (10 entradas)
│
├── backend/
│   ├── app/                    # ← Paquete principal
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI, rutas, CORS, middleware
│   │   ├── finance.py          # Data access (yfinance + caché)
│   │   ├── indicators.py       # Facade del pipeline domain
│   │   └── domain/
│   │       ├── __init__.py
│   │       ├── features.py     # Extracción de features (datos crudos → limpios)
│   │       └── scoring.py      # Evaluación de reglas (pure, sin IO)
│   ├── tests/
│   │   ├── test_api.py         # 6 tests de API (yfinance mockeado)
│   │   ├── test_finance.py     # 4 tests de data layer (mockeado)
│   │   └── test_indicators.py  # 10 tests: scoring + contract + snapshot
│   ├── requirements.txt
│   ├── Dockerfile              # python:3.12-slim, non-root, healthcheck
│   └── .env.example
│
└── frontend/
    ├── Dockerfile              # Multi-stage: node build → nginx serve
    ├── package.json / pnpm-lock.yaml / vite.config.js
    ├── index.html
    └── src/
        ├── main.js
        ├── App.vue
        ├── services/
        │   ├── api.js          # Capa HTTP centralizada
        │   └── mappers.js      # Transform API → UI model
        ├── components/
        │   ├── StockAnalyzer.vue
        │   └── CompanyList.vue
        └── data/
            └── companies.json  # 59 empresas en 9 sectores
```

---

## Flujo de Datos

### Análisis de Burbuja (`GET /stock/{ticker}`)

1. Usuario ingresa un ticker y hace clic en "Analyze"
2. Frontend dispara en paralelo dos fetch a `VITE_API_URL` via `services/api.js`
3. Backend pasa por middleware en orden: observability (request_id) → rate limiter
4. `main.py` valida ticker con regex `^[A-Z]{1,5}$`
5. `finance.get_stock_data()` verifica caché TTLCache; si miss → `yf.Ticker` con timeout 10s
6. Datos se normalizan a `StockData` Pydantic + se cachean con versión de schema
7. `indicators.bubble_score()` orquesta el pipeline domain:
   - `features.extract_features()` → features limpias (pe, growth, pb, vol, momentum)
   - `scoring.evaluate_features()` → score + razones (puro, sin IO)
8. Score (0–9) + riskLabel + razones se devuelven como `StockResponse`
9. Frontent recibe JSON, pasa por `mapStockResponse()` en mappers.js, renderiza

### Historial de Precios (`GET /stock/{ticker}/history`)

1. Frontend solicita histórico en paralelo al análisis
2. Backend obtiene datos (cacheados o fresh) y devuelve `{ date, close }[]`
3. Frontend normaliza precios y dibuja SVG `<polyline>`

---

## Motor de Scoring (`app/domain/scoring.py`)

### Reglas data-driven (INFO_RULES)

| Regla | Feature | Umbral | Puntos |
|---|---|---|---|
| P/E | `pe` | > 40 | +2 |
| P/E | `pe` | > 30 | +1 |
| Revenue Growth | `revenue_growth` | > 30% | +2 |
| Revenue Growth | `revenue_growth` | > 15% | +1 |
| Price-to-Book | `pb` | > 10 | +1 |

### Reglas data-driven (HIST_RULES)

| Regla | Feature | Umbral | Puntos |
|---|---|---|---|
| Volatilidad anualizada | `volatility` | > 50% | +1 |
| Momentum 6 meses | `momentum` | > 50% | +2 |
| Momentum 6 meses | `momentum` | > 20% | +1 |

### Penalizaciones por datos faltantes

| Regla | Penalización |
|---|---|
| P/E | +0.5 |
| Revenue Growth | +0.5 |
| P/B | +0.2 |
| Volatilidad | +0.3 |
| Momentum | +0.3 |
| **Máximo penalización** | **+1.8** |

Score final: suma de puntos + penalizaciones, clamped a rango [0, 9], convertido a `int`.

### Interpretación del Score

| Rango | riskLabel | Color UX |
|---|---|---|
| 0–2 | low | Verde |
| 3 | low/medium | Verde claro |
| 4–5 | medium | Amarillo |
| 6 | medium/high | Naranja |
| 7–8 | high | Rojo |
| 9 | very high | Rojo brillante |

---

## Decisiones de Arquitectura Clave

1. **Stateless** — No hay base de datos ni persistencia. Caché en memoria (TTLCache) como única capa de aceleración.
2. **Síncrono pero con timeout** — Las rutas son síncronas (yfinance es bloqueante). El timeout se maneja con ThreadPoolExecutor (cross-platform, a diferencia de SIGALRM).
3. **Paquete `app/` estándar** — El backend es un paquete Python (`backend/app/`) y se ejecuta con `uvicorn app.main:app`. Esto evita `ModuleNotFoundError` en Docker y es el estándar de producción para FastAPI.
4. **Dominio separado en dos capas** — `features.py` extrae features de datos crudos (contiene todo el `info.get()` y manipulación de DataFrames) mientras `scoring.py` es puro (solo evalúa reglas contra un dict de features). Esto permite cambiar la fuente de datos sin tocar la lógica de scoring, y viceversa.
5. **Scoring data-driven** — Las reglas son estructuras de datos declarativas (`INFO_RULES` / `HIST_RULES`), no if/else hardcodeados. Permite tuning sin tocar código y futura carga desde config/DB.
6. **Pydantic como contrato** — Domain models (`StockPoint`, `StockData`) y response models (`StockResponse`, `Metrics`) definen el schema en ambos lados de la serialización. Cache versionado con `CACHE_VERSION`.
7. **YFinance mockeado en tests** — 20 tests deterministas que no dependen de red (~1s vs ~7s con llamadas reales). Incluye contract test (OpenAPI schema) y snapshot test (output conocido).
8. **Frontend API layer + mappers** — `services/api.js` centraliza el HTTP, `services/mappers.js` desacopla la forma del API del modelo de UI. El frontend ya no depende directamente de `StockResponse`.
9. **Observabilidad** — Middleware que asigna `request_id` a cada request y mide `latency_ms`. Logs JSON estructurados con estos campos para trazabilidad.
10. **SVG inline** — Sin librerías de gráficos. Anillo de score y línea de precio son SVG puro en el template.
11. **Multi-stage Docker** — Frontend: build con node, serve con nginx (~25MB final). Backend: non-root user, Python 3.12-slim, healthcheck configurado.
12. **Rate limiting** — 60 req/min por IP, configurable por variable de entorno.

---

## Cómo Ejecutar

### Local (sin Docker)

Backend:
```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://127.0.0.1:8000
# Documentación: http://127.0.0.1:8000/docs
```

Frontend:
```bash
cd frontend
cp .env.example .env
pnpm install
pnpm dev
# http://localhost:5173
```

Tests:
```bash
cd backend
python -m pytest tests/ -v
```

### Con Docker

```bash
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:80
```

---

## CI/CD (GitHub Actions)

Dos jobs paralelos en cada push/PR a `main`:

- **Backend**: Ubuntu + Python 3.12 → `pip install` → `pytest -v` (20 tests, sin red, ~1s)
- **Frontend**: Ubuntu + Node 18 → pnpm → `install` → `build`

Sin deploy automático — CI es únicamente de validación.

---

## Mejoras Futuras (documentadas)

- Redis como caché distribuida (reemplazar TTLCache local)
- Migración a TypeScript en frontend
- Vue Router para múltiples vistas (comparación, dashboard)
- Rate limiting con backends distribuidos (Redis)
- Autenticación y API keys
- Endpoint de comparación `/compare?tickerA=&tickerB=`
- async yfinance wrapper (httpx)
- Feature store y A/B testing de estrategias de scoring
- Despliegue en Vercel / Render / Fly.io
- Load testing y benchmarks
- Testing de componentes frontend (Vitest + Vue Test Utils)
- Linting y formateo automático (ruff backend, ESLint + Prettier frontend)
- Rate limiter asíncrono para evitar bloqueo del event loop
- Type checking (mypy backend, TypeScript frontend)
- Reportes de cobertura de código (coverage.py, c8)
