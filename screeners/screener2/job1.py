"""Screener 2 — Job 1: Weekly Bullish / Daily Pullback.

Conditions:
  • Price > EMA(weekly_trend)   [Weekly]   — long-term bullish
  • Price < EMA(daily_pullback) [Daily]    — pulling back below daily EMA
  • Price > EMA(recovery)       [Daily]    — short-term recovery in progress
  • (optional) Market cap ≥ min_mktcap_b $B
"""

from dataclasses import dataclass

from ..base import BaseJob, FieldDef
from api import tv_scan


@dataclass
class S2J1Cfg:
    ema_weekly_trend   : int   = 200
    ema_daily_pullback : int   = 200
    ema_recovery       : int   = 8
    min_mktcap_b       : float = 0.0


class Job1(BaseJob):
    label       = "Job 1 — Weekly Bullish / Daily Pullback"
    result_name = "Potential_Bullish2"
    needs_watchlist = False

    fields = [
        FieldDef("ema_weekly_trend",   "Weekly Trend EMA",   "int", 200, 5,    500,
                 tooltip="Price must be ABOVE this EMA on the weekly chart"),
        FieldDef("ema_daily_pullback", "Daily Pullback EMA", "int", 200, 5,    500,
                 tooltip="Price must be BELOW this EMA on the daily chart"),
        FieldDef("ema_recovery",       "Recovery EMA",       "int",   8, 3,     50,
                 tooltip="Price must be ABOVE this short-term EMA (recovery signal)"),
        FieldDef("min_mktcap_b",       "Min MktCap $B",    "float", 0.0, 0.0, 5000.0, 1,
                 tooltip="Minimum market cap in $B  (0 = no filter)"),
    ]

    @property
    def config_class(self):
        return S2J1Cfg

    def run(self, cfg: S2J1Cfg, universe: set, watchlist=None) -> list:
        wt  = f"EMA{cfg.ema_weekly_trend}|1W"
        dpb = f"EMA{cfg.ema_daily_pullback}"
        rec = f"EMA{cfg.ema_recovery}"
        cols = [
            "name", "description", "close",
            wt, dpb, rec,
            "Perf.W", "RSI", "volume", "market_cap_basic",
            "sector", "change", "high", "low", "high|1W", "low|1W", "exchange",
        ]
        filt = [
            {"left": wt,      "operation": "less", "right": "close"},
            {"left": "close", "operation": "less", "right": dpb},
            {"left": rec,     "operation": "less", "right": "close"},
        ]
        raw, out = tv_scan(filt, cols), []
        for item in raw:
            d = item["d"]
            try:
                sym, price = d[0], (d[2] or 0)
                ema_wt, ema_dpb, ema_rec = d[3], d[4], d[5]
                if sym not in universe or not price:
                    continue
                if not ema_wt or not ema_dpb or not ema_rec:
                    continue
                mc = d[9]
                if cfg.min_mktcap_b > 0 and (not mc or mc / 1e9 < cfg.min_mktcap_b):
                    continue
                out.append({
                    "Symbol":                           sym,
                    "Exchange":                         d[16] or "",
                    "Company":                          (d[1] or "")[:35],
                    "Price":                            round(price, 2),
                    f"EMA{cfg.ema_recovery}(1D)":       round(ema_rec, 2),
                    f"EMA{cfg.ema_daily_pullback}(1D)": round(ema_dpb, 2),
                    "Gap_Pull%":                        round((price - ema_dpb) / ema_dpb * 100, 2),
                    f"EMA{cfg.ema_weekly_trend}(1W)":   round(ema_wt, 2),
                    "Perf_W%":                          round(d[6], 2) if d[6] is not None else None,
                    "RSI":                              round(d[7], 1) if d[7] else None,
                    "Volume":                           int(d[8]) if d[8] else None,
                    "MktCap_B":                         round(mc / 1e9, 1) if mc else None,
                    "Sector":                           d[10] or "",
                    "Change%":                          round(d[11], 2) if d[11] is not None else None,
                    "Day_High":                         round(d[12], 2) if d[12] else None,
                    "Day_Low":                          round(d[13], 2) if d[13] else None,
                    "Wk_High":                         round(d[14], 2) if d[14] else None,
                    "Wk_Low":                          round(d[15], 2) if d[15] else None,
                })
            except Exception:
                continue
        return out

    def conditions_summary(self, cfg: S2J1Cfg):
        lines = [
            f"Price > EMA{cfg.ema_weekly_trend} (1W)",
            f"Price < EMA{cfg.ema_daily_pullback} (1D)",
            f"Price > EMA{cfg.ema_recovery} (1D)",
        ]
        if cfg.min_mktcap_b > 0:
            lines.append(f"MktCap ≥ ${cfg.min_mktcap_b:.1f}B")
        return lines
