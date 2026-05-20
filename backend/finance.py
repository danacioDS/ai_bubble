import yfinance as yf
import pandas as pd
import logging
import signal
import os
from cachetools import TTLCache
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
YAHOO_TIMEOUT = int(os.getenv("YAHOO_TIMEOUT", "10"))

cache = TTLCache(maxsize=128, ttl=CACHE_TTL)


class FinanceTimeoutError(Exception):
    pass


def _timeout_handler(signum, frame):
    raise FinanceTimeoutError("Yahoo Finance request timed out")


def _setup_alarm(seconds):
    try:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(seconds)
        return True
    except ValueError:
        logger.warning("Signal alarms not available (not in main thread)")
        return False


def _cancel_alarm():
    try:
        signal.alarm(0)
    except ValueError:
        pass


def _fetch_stock_data(ticker: str):
    stock = yf.Ticker(ticker)

    hist = stock.history(period="6mo")

    if hist is None or hist.empty:
        return None, None, None

    hist = hist.reset_index()
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


def get_stock_data(ticker: str):
    ticker = ticker.strip().upper()

    if ticker in cache:
        logger.debug("Cache hit for %s", ticker)
        return cache[ticker]

    logger.info("Fetching data for %s", ticker)

    try:
        alarm_set = _setup_alarm(YAHOO_TIMEOUT)

        result = _fetch_stock_data(ticker)

        if alarm_set:
            _cancel_alarm()

        info, hist, price = result
        if info is None and hist is None:
            logger.warning("No data found for %s", ticker)
        else:
            logger.info("Successfully fetched data for %s", ticker)

        cache[ticker] = result
        return result

    except FinanceTimeoutError:
        logger.error("Timeout fetching data for %s after %ds", ticker, YAHOO_TIMEOUT)
        return None, None, None
    except Exception as e:
        logger.exception("Error fetching data for %s: %s", ticker, e)
        return None, None, None
