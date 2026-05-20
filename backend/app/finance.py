import yfinance as yf
import pandas as pd
import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from cachetools import TTLCache
from dotenv import load_dotenv
from pydantic import BaseModel


CACHE_VERSION = 1

load_dotenv()

logger = logging.getLogger(__name__)

CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
YAHOO_TIMEOUT = int(os.getenv("YAHOO_TIMEOUT", "10"))


class StockPoint(BaseModel):
    date: str
    close: float


class StockData(BaseModel):
    info: dict | None = None
    history: list[StockPoint] | None = None
    price: float | None = None


cache = TTLCache(maxsize=128, ttl=CACHE_TTL)


class FinanceTimeoutError(Exception):
    pass


def run_with_timeout(fn, seconds, *args, **kwargs):
    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=seconds)
        except TimeoutError:
            raise FinanceTimeoutError(f"Request timed out after {seconds}s")


def _fetch_stock_data(ticker: str):
    stock = yf.Ticker(ticker)

    hist = stock.history(period="6mo")

    if hist is None or hist.empty:
        return None, None, None

    hist = hist.reset_index()
    if "Date" not in hist.columns:
        raise ValueError(
            f"Expected 'Date' column after reset_index(), got {list(hist.columns)}"
        )
    hist = hist[["Date", "Close"]].dropna()

    try:
        info = stock.info
        if info is None:
            info = {}
    except Exception:
        info = {}

    price = info.get("currentPrice") or info.get("regularMarketPrice")

    if price is None and not hist.empty:
        price = float(hist["Close"].iloc[-1])

    return info, hist, price


def _normalize(info, hist, price):
    data = StockData(
        info=dict(info) if info else None,
        price=price,
    )

    if hist is not None and not hist.empty:
        data.history = [
            StockPoint(date=str(row["Date"].date()), close=float(row["Close"]))
            for _, row in hist.iterrows()
        ]

    return {"version": CACHE_VERSION, **data.model_dump()}


def _denormalize(data: dict):
    if data.get("version") != CACHE_VERSION:
        raise ValueError(
            f"Cache schema version mismatch: expected {CACHE_VERSION}, got {data.get('version')}"
        )

    parsed = StockData(**{k: v for k, v in data.items() if k != "version"})

    hist = None
    if parsed.history:
        hist = pd.DataFrame(
            {
                "Date": pd.to_datetime([p.date for p in parsed.history]),
                "Close": [p.close for p in parsed.history],
            }
        )

    return parsed.info, hist, parsed.price


def get_stock_data(ticker: str):
    ticker = ticker.strip().upper()

    if ticker in cache:
        logger.debug("Cache hit for %s", ticker)
        return _denormalize(cache[ticker])

    logger.info("Fetching data for %s", ticker)

    try:
        result = run_with_timeout(_fetch_stock_data, YAHOO_TIMEOUT, ticker)

        info, hist, price = result
        if info is None and hist is None:
            logger.warning("No data found for %s", ticker)
        else:
            logger.info("Successfully fetched data for %s", ticker)

        cache[ticker] = _normalize(info, hist, price)
        return result

    except FinanceTimeoutError:
        logger.error("Timeout fetching data for %s after %ds", ticker, YAHOO_TIMEOUT)
        return None, None, None
    except Exception as e:
        logger.exception("Error fetching data for %s: %s", ticker, e)
        return None, None, None
