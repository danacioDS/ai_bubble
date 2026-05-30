import logging
import json
import os
import re
import time
import uuid
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .finance import get_stock_data
from .indicators import bubble_score


# -----------------------------
# Logging (structured JSON)
# -----------------------------

class JSONFormatter(logging.Formatter):
    def format(self, record):
        obj = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        for key in ("request_id", "latency_ms"):
            val = getattr(record, key, None)
            if val is not None:
                obj[key] = val

        if record.exc_info and record.exc_info[0]:
            obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(obj)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])

logger = logging.getLogger(__name__)


# -----------------------------
# App init
# -----------------------------

app = FastAPI(title="AI Market Risk Intelligence Engine")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Rate limiter
# -----------------------------

class RateLimiter:
    def __init__(self, max_requests: int = 60, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self._requests = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.window

        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        if len(self._requests[key]) >= self.max_requests:
            return False

        self._requests[key].append(now)
        return True


rate_limiter = RateLimiter(
    int(os.getenv("RATE_LIMIT_MAX", "60")),
    int(os.getenv("RATE_LIMIT_WINDOW", "60")),
)


# -----------------------------
# Middleware
# -----------------------------

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.time()

    response = await call_next(request)

    latency_ms = int((time.time() - start) * 1000)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(latency_ms)

    logger.info(
        "Request completed",
        extra={"request_id": request_id, "latency_ms": latency_ms},
    )

    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"

    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    return await call_next(request)


# -----------------------------
# Models
# -----------------------------

class Metrics(BaseModel):
    pe: float | None = None
    forwardPe: float | None = None
    revenueGrowth: float | None = None
    priceToBook: float | None = None
    marketCap: int | None = None


class StockResponse(BaseModel):
    ticker: str
    name: str | None = None
    price: float | None = None
    metrics: Metrics
    score: int
    riskLabel: str
    reasons: list[str]


class PricePoint(BaseModel):
    date: str
    close: float


class HistoryResponse(BaseModel):
    prices: list[PricePoint]


# -----------------------------
# Helpers
# -----------------------------

TICKER_RE = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")


def validate_ticker(ticker: str) -> str:
    if not ticker:
        raise HTTPException(400, "Ticker required")

    ticker = ticker.strip().upper()

    if not TICKER_RE.match(ticker):
        raise HTTPException(400, "Invalid ticker format")

    return ticker


def score_to_risk_label(score: int) -> str:
    if score >= 9:
        return "very high"
    if score >= 7:
        return "high"
    if score >= 6:
        return "medium/high"
    if score >= 4:
        return "medium"
    if score >= 3:
        return "low/medium"
    return "low"


# -----------------------------
# Routes
# -----------------------------

@app.get("/")
def root():
    return {
        "service": "AI Market Risk Intelligence Engine",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stock/{ticker}", response_model=StockResponse)
def get_stock(ticker: str):
    ticker = validate_ticker(ticker)

    info, hist, _ = get_stock_data(ticker)

    if not info or hist is None:
        raise HTTPException(404, "No data found")

    score, reasons = bubble_score(info, hist)

    return StockResponse(
        ticker=ticker,
        name=info.get("shortName") or info.get("longName"),
        price=info.get("currentPrice") or info.get("regularMarketPrice"),
        metrics=Metrics(
            pe=info.get("trailingPE"),
            forwardPe=info.get("forwardPE"),
            revenueGrowth=info.get("revenueGrowth"),
            priceToBook=info.get("priceToBook"),
            marketCap=info.get("marketCap"),
        ),
        score=score,
        riskLabel=score_to_risk_label(score),
        reasons=reasons,
    )


@app.get("/stock/{ticker}/history", response_model=HistoryResponse)
def get_history(ticker: str):
    ticker = validate_ticker(ticker)

    _, hist, _ = get_stock_data(ticker)

    if hist is None or hist.empty:
        return HistoryResponse(prices=[])

    return HistoryResponse(
        prices=[
            PricePoint(
                date=str(row["Date"].date()),
                close=float(row["Close"]),
            )
            for _, row in hist.iterrows()
        ]
    )