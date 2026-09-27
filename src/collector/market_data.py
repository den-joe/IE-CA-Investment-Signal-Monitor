import yfinance as yf

EXCHANGE_SUFFIX = {"TSX": ".TO", "TSXV": ".V"}


def fetch_market_data(ticker: str, exchange: str) -> dict:
    suffix = EXCHANGE_SUFFIX.get(exchange)
    if suffix is None:
        raise ValueError(f"Unknown exchange: {exchange}")

    symbol = f"{ticker}{suffix}"
    info = yf.Ticker(symbol).info

    return {
        "symbol": symbol,
        "market_cap": info.get("marketCap"),
        "currency": info.get("currency"),
        "quote_type": info.get("quoteType"),
    }
