import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from finance import get_stock_data
from indicators import bubble_score

logger = logging.getLogger(__name__)

# -----------------------------
# RESPONSE MODELS
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
    reasons: list[str]

class PricePoint(BaseModel):
    date: str
    close: float

class HistoryResponse(BaseModel):
    prices: list[PricePoint]

# -----------------------------
# APP
# -----------------------------
app = FastAPI(title="AI Bubble Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# HEALTH
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------------
# VALIDATION
# -----------------------------
def validate_ticker(ticker: str):
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker required")

    ticker = ticker.strip().upper()

    if len(ticker) > 10:
        raise HTTPException(status_code=400, detail="Invalid ticker")

    return ticker


# -----------------------------
# ENDPOINT: ANALYSIS
# -----------------------------
@app.get("/stock/{ticker}", response_model=StockResponse)
def get_stock(ticker: str):

    ticker = validate_ticker(ticker)
    logger.info("Analysis request for %s", ticker)

    info, hist, _ = get_stock_data(ticker)

    if not info and hist is None:
        raise HTTPException(
            status_code=404,
            detail="No data found for ticker"
        )

    score, reasons = bubble_score(info or {}, hist)
    info = info or {}

    logger.info("Score for %s: %d/9", ticker, score)

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
        reasons=reasons,
    )


# -----------------------------
# ENDPOINT: HISTORY
# -----------------------------
@app.get("/stock/{ticker}/history", response_model=HistoryResponse)
def get_history(ticker: str):

    ticker = validate_ticker(ticker)
    logger.info("History request for %s", ticker)

    _, hist, _ = get_stock_data(ticker)

    if hist is None or hist.empty:
        return HistoryResponse(prices=[])

    return HistoryResponse(
        prices=[
            PricePoint(
                date=str(row["Date"].date()),
                close=float(row["Close"])
            )
            for _, row in hist.iterrows()
        ]
    )
