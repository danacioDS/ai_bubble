import yfinance as yf
import pandas as pd


def get_stock_data(ticker: str):
    """
    Fetch stock fundamentals and historical data from Yahoo Finance.

    Returns:
        info (dict): fundamentals
        hist (pd.DataFrame): price history (6mo)
        price (float): last known price fallback
    """

    ticker = ticker.strip().upper()

    try:
        stock = yf.Ticker(ticker)

        # =========================
        # 1. HISTORICAL DATA (más confiable)
        # =========================
        hist = stock.history(period="6mo")

        if hist is None or hist.empty:
            return None, None, None

        # limpiar columnas mínimas
        hist = hist.reset_index()
        hist = hist[["Date", "Close"]].dropna()

        # =========================
        # 2. INFO (puede venir incompleto)
        # =========================
        try:
            info = stock.info
            if info is None:
                info = {}
        except Exception:
            info = {}

        # =========================
        # 3. FALLBACK PRICE (CRÍTICO)
        # =========================
        price = None

        # 1) intento desde info
        price = info.get("currentPrice") or info.get("regularMarketPrice")

        # 2) fallback desde historial
        if price is None and not hist.empty:
            price = float(hist["Close"].iloc[-1])

        # =========================
        # 4. DEBUG LIGHT (opcional)
        # =========================
        # print(f"[finance] {ticker} keys:", len(info.keys()))

        return info, hist, price

    except Exception as e:
        print(f"[finance error] {ticker}: {e}")
        return None, None, None
