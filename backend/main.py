from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from finance import get_stock_data
from indicators import bubble_score

app = FastAPI(title="AI Bubble Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
# RESPONSE FORMATTER
# -----------------------------
def build_response(ticker, info, hist, score, reasons):
    return {
        "success": True,
        "data": {
            "ticker": ticker,
            "name": info.get("shortName"),
            "price": info.get("currentPrice"),
            "metrics": {
                "pe": info.get("trailingPE"),
                "forwardPe": info.get("forwardPE"),
                "revenueGrowth": info.get("revenueGrowth"),
                "priceToBook": info.get("priceToBook"),
                "marketCap": info.get("marketCap"),
            },
            "score": score,
            "reasons": reasons,
        }
    }


# -----------------------------
# ENDPOINT: ANALYSIS
# -----------------------------
@app.get("/stock/{ticker}")
def get_stock(ticker: str):

    ticker = validate_ticker(ticker)

    info, hist = get_stock_data(ticker)

    if not info and hist is None:
        raise HTTPException(
            status_code=404,
            detail="No data found for ticker"
        )

    score, reasons = bubble_score(info or {}, hist)

    return build_response(ticker, info or {}, hist, score, reasons)


# -----------------------------
# ENDPOINT: HISTORY
# -----------------------------
@app.get("/stock/{ticker}/history")
def get_history(ticker: str):

    ticker = validate_ticker(ticker)

    _, hist = get_stock_data(ticker)

    if hist is None or hist.empty:
        return {"prices": []}

    return {
        "prices": [
            {
                "date": str(idx.date()),
                "close": float(row["Close"])
            }
            for idx, row in hist.iterrows()
        ]
    }