"""TradingView API helpers: universe fetching and scanner calls."""

import io

import pandas as pd
import requests

from constants import TV_URL

_WIKI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_index_tickers() -> tuple:
    """Return (sp500_set, nasdaq100_set).

    Uses requests so SSL certificates bundled via certifi are used correctly
    inside a PyInstaller-frozen app.  The HTML is parsed with lxml (fastest)
    and html5lib as a fallback so the build always finds a working parser.
    """

    def _fetch(url: str, table_idx: int, col: str) -> set:
        resp = requests.get(url, headers=_WIKI_HEADERS, timeout=30, verify=True)
        resp.raise_for_status()
        # io.StringIO keeps lxml / html5lib working in frozen env
        tables = pd.read_html(io.StringIO(resp.text))
        return set(tables[table_idx][col].tolist())

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
