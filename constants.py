"""Application-wide constants."""

import os

TV_URL        = "https://scanner.tradingview.com/america/scan"
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "screener_settings.json")
WL1_FILE      = os.path.join(BASE_DIR, "s1_watchlist.json")
WL2_FILE      = os.path.join(BASE_DIR, "s2_watchlist.json")
