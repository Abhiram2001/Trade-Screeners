"""TradingView API helpers: universe fetching and scanner calls."""

import ssl
import urllib.request

import pandas as pd
import requests

from constants import TV_URL


def get_index_tickers() -> tuple:
    """Return (sp500_set, nasdaq100_set)."""
    ctx = ssl._create_unverified_context()

    def _fetch(url, idx, col):
        req  = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, context=ctx).read()
        return set(pd.read_html(html)[idx][col].tolist())

    sp500  = _fetch("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", 0, "Symbol")
    nasdaq = _fetch("https://en.wikipedia.org/wiki/Nasdaq-100", 4, "Ticker")
    return sp500, nasdaq


def tv_scan(filters: list, columns: list, limit: int = 3000) -> list:
    """Execute a TradingView scanner POST and return raw data rows."""
    # Sanitize filter values: ensure numeric "right" values are JSON-safe
    clean_filters = []
    for f in filters:
        cf = dict(f)
        if isinstance(cf.get("right"), float) and cf["right"] == int(cf["right"]):
            cf["right"] = int(cf["right"])
        clean_filters.append(cf)

    payload = {
        "filter":   clean_filters,
        "options":  {"lang": "en"},
        "markets":  ["america"],
        "screener": "america",
        "symbols":  {"query": {"types": []}, "tickers": []},
        "columns":  columns,
        "sort":     {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range":    [0, limit],
    }
    r = requests.post(TV_URL, json=payload, timeout=30)
    if not r.ok:
        raise requests.HTTPError(
            f"{r.status_code} {r.reason} — TradingView response: {r.text[:300]}",
            response=r,
        )
    return r.json().get("data", [])
