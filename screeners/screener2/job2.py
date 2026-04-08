"""Screener 2 — Job 2: Daily EMA Crossover Breakout (from Job 1 watchlist)."""

from dataclasses import dataclass

from ..base import BaseJob, FieldDef
from api import tv_scan


@dataclass
class S2J2Cfg:
    ema_crossover: int = 20


class Job2(BaseJob):
    label           = "Job 2 — EMA Crossover Breakout"
    result_name     = "Bullish2_20ema"
    needs_watchlist = True

    fields = [
        FieldDef("ema_crossover", "Crossover EMA", "int", 20, 3, 200,
                 tooltip="EMA period for the upward daily crossover signal"),
    ]

    @property
    def config_class(self):
        return S2J2Cfg

    def run(self, cfg: S2J2Cfg, universe: set, watchlist=None) -> list:
        ec   = f"EMA{cfg.ema_crossover}"
        cols = [
            "name", "description", "close", "open", ec,
            "EMA200", "EMA200|1W", "EMA8", "RSI", "volume", "market_cap_basic",
            "sector", "change", "high", "low", "high|1W", "low|1W", "exchange",
        ]
        filt = [{"left": "close", "operation": "crosses", "right": ec}]
        raw, out = tv_scan(filt, cols), []
        wl = watchlist or set()
        for item in raw:
            d = item["d"]
            try:
                sym, price, op, ema_c = d[0], (d[2] or 0), (d[3] or 0), d[4]
                if sym not in wl or not ema_c:
                    continue
                if not (price > ema_c and op <= ema_c):
                    continue
                mc = d[10]
                out.append({
                    "Symbol":                      sym,
                    "Exchange":                    d[17] or "",
                    "Company":                     (d[1] or "")[:35],
                    "Price":                       round(price, 2),
                    "Open":                        round(op, 2),
                    f"EMA{cfg.ema_crossover}(1D)": round(ema_c, 2),
                    "Gap_Cross%":                  round((price - ema_c) / ema_c * 100, 2),
                    "EMA200(1D)":                  round(d[5], 2) if d[5] else None,
                    "EMA200(1W)":                  round(d[6], 2) if d[6] else None,
                    "EMA8(1D)":                    round(d[7], 2) if d[7] else None,
                    "RSI":                         round(d[8], 1) if d[8] else None,
                    "Volume":                      int(d[9]) if d[9] else None,
                    "MktCap_B":                    round(mc / 1e9, 1) if mc else None,
                    "Sector":                      d[11] or "",
                    "Change%":                     round(d[12], 2) if d[12] is not None else None,
                    "Day_High":                    round(d[13], 2) if d[13] else None,
                    "Day_Low":                     round(d[14], 2) if d[14] else None,
                    "Wk_High":                     round(d[15], 2) if d[15] else None,
                    "Wk_Low":                      round(d[16], 2) if d[16] else None,
                })
            except Exception:
                continue
        return out

    def conditions_summary(self, cfg: S2J2Cfg):
        return [f"Daily close crosses EMA{cfg.ema_crossover} upward (from Job 1 watchlist)"]
