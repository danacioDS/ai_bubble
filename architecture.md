# AI Bubble Detector — Arquitectura

## Descripción General

Aplicación full-stack para detectar burbujas financieras en acciones usando datos fundamentales y técnicos. Backend en Python/FastAPI + frontend en Vue 3.

---

## Diagrama del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (Vue 3 + Vite)                     │
│                                                                 │
│  App.vue                                                        │
│    └── StockAnalyzer.vue (componente único)                     │
│          ├── Input de búsqueda (ticker)                         │
│          ├── Anillo SVG de puntuación                           │
│          ├── Grid de métricas (P/E, growth, P/B, market cap)   │
│          ├── Lista de señales de burbuja                        │
│          └── Gráfico SVG de precio histórico                    │
│                                                                 │
│  Estado: ref()/computed() local en StockAnalyzer                │
│  HTTP: fetch nativo (sin Axios)                                 │
│  Puerto: 5173                                                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │ GET http://localhost:8000
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI + Uvicorn)                   │
│                                                                 │
│  main.py              → Rutas REST + CORS                       │
│    ├── GET /stock/{ticker}        → Análisis de burbuja        │
│    └── GET /stock/{ticker}/history → Precios históricos        │
│         │                             │                         │
│         ▼                             ▼                         │
│  finance.py   get_stock_data()                                   │
│    └── yfinance (yf.Ticker) → Yahoo Finance API                 │
│         │                                                        │
│         ▼                                                        │
│  indicators.py   bubble_score() ← Motor heurístico              │
│    ├── Ratio P/E          (>30 → +1, >40 → +2)                 │
│    ├── Crecimiento ingresos (>15% → +1, >30% → +2)             │
│    ├── Price-to-Book      (>10 → +1)                            │
│    ├── Volatilidad diaria (>3% → +1)                            │
│    └── Retorno 6 meses    (>20% → +1, >50% → +2)               │
│         │                                                        │
│         ▼                                                        │
│  JSON Response: { score, reasons, ticker, name, price, ... }    │
└─────────────────────────────────────────────────────────────────┘
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
| **Procesamiento** | pandas |
| **Estilos** | CSS scoped, tema oscuro |
| **Gráficos** | SVG inline (sin librerías externas) |
| **Estado** | `ref()` / `computed()` local (sin Pinia/Vuex) |
| **Base de datos** | Ninguna (stateless, datos en vivo) |

---

## Estructura del Proyecto

```
ai_bubble/
├── backend/
│   ├── main.py           # App FastAPI, rutas, CORS
│   ├── finance.py        # Obtención de datos (yfinance)
│   ├── indicators.py     # Lógica de scoring heurístico
│   └── requirements.txt  # fastapi, uvicorn, yfinance, pandas
│
├── frontend/
│   ├── index.html        # Entry point HTML
│   ├── package.json      # Dependencias (vue, vite)
│   ├── vite.config.js    # Configuración de Vite
│   └── src/
│       ├── main.js       # createApp + mount
│       ├── App.vue       # Componente raíz (header + layout)
│       └── components/
│           └── StockAnalyzer.vue  # Lógica completa de UI
│
└── architecture.md       # Este documento
```

---

## Flujo de Datos

### Análisis de Burbuja (`GET /stock/{ticker}`)

1. Usuario ingresa un ticker y hace clic en "Analyze"
2. Frontend dispara en paralelo dos fetch a `http://localhost:8000`
3. Backend recibe la solicitud en `main.py` → llama a `finance.get_stock_data()`
4. `finance.py` crea un objeto `yf.Ticker` y obtiene fundamentos (`info`) e histórico (`history`)
5. Ambos se pasan a `indicators.bubble_score()` que evalúa 5 indicadores
6. El score (0–9) más la lista de razones se devuelven como JSON
7. Frontend renderiza: anillo de score, grid de métricas, señales, y gráfico SVG

### Historial de Precios (`GET /stock/{ticker}/history`)

1. Frontend solicita el histórico paralelamente al análisis
2. Backend obtiene datos via `yfinance` y devuelve array `{date, close}`
3. Frontend normaliza los precios y dibuja un SVG `<polyline>`

---

## Motor de Scoring (`indicators.py`)

| Indicador | Condición | Puntos |
|---|---|---|
| Ratio P/E | > 40 | +2 |
| Ratio P/E | > 30 (≤ 40) | +1 |
| Crecimiento ingresos | > 30% | +2 |
| Crecimiento ingresos | > 15% (≤ 30%) | +1 |
| Price-to-Book | > 10 | +1 |
| Volatilidad diaria | > 3% | +1 |
| Cambio precio 6 meses | > 50% | +2 |
| Cambio precio 6 meses | > 20% (≤ 50%) | +1 |

**Score máximo: ~9 puntos**

### Interpretación del Score

| Rango | Etiqueta | Color |
|---|---|---|
| 0–3 | Safe (seguro) | Verde |
| 4–5 | Warning (advertencia) | Amarillo |
| 6–9 | Danger (peligro) | Rojo |

---

## Decisiones de Arquitectura Clave

1. **Stateless** — No hay base de datos ni persistencia. Cada request obtiene datos frescos de Yahoo Finance.
2. **Síncrono** — A pesar de que FastAPI soporta async, las rutas son síncronas porque `yfinance` es bloqueante.
3. **Separación por capas** — `finance.py` (datos), `indicators.py` (lógica de negocio), `main.py` (HTTP) están claramente separados.
4. **Scoring heurístico** — No es ML. Usa umbrales simples con pesos enteros aditivos.
5. **Componente único en frontend** — Toda la lógica vive en `StockAnalyzer.vue` sin enrutamiento ni estado global.
6. **SVG inline** — Los gráficos (anillo de score y línea de precio) se generan como SVG directamente en el template, sin librerías de terceros.
7. **CORS hardcodeado** — Solo permite `http://localhost:5173` (puerto de desarrollo de Vite).

---

## Cómo Ejecutar

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# Disponible en http://127.0.0.1:8000
# Documentación interactiva en http://127.0.0.1:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Disponible en http://localhost:5173
```

---

## Posibles Mejoras Futuras

- Agregar base de datos para cachear respuestas de Yahoo Finance
- Centralizar API client en frontend con variable de entorno para la URL base
- Agregar Vue Router para múltiples vistas
- Migrar a TypeScript
- Integrar librería de gráficos profesional (Chart.js, D3)
- Agregar tests (vitest en frontend, pytest en backend)
- Configurar Docker y docker-compose
- Agregar validación de inputs y manejo de errores robusto en backend
- Externalizar configuración (CORS, puerto) a variables de entorno
