"""Screener 1 — Job 1: Bullish Near Support.

Conditions:
  • Price > EMA(daily_trend)  [Daily]
  • Price > EMA(weekly_trend) [Weekly]
  • EMA(support) ≤ Price ≤ EMA(support) × (1 + gap_max_pct%)
  • Weekly performance ≥ perf_weekly_min%
  • (optional) Market cap ≥ min_mktcap_b $B
"""

from dataclasses import dataclass

from ..base import BaseJob, FieldDef
from api import tv_scan


@dataclass
class S1J1Cfg:
    ema_daily_trend  : int   = 200
    ema_weekly_trend : int   = 200
    ema_support      : int   = 20
    gap_max_pct      : float = 3.0
    perf_weekly_min  : float = 0.0
    min_mktcap_b     : float = 0.0


class Job1(BaseJob):
    label       = "Job 1 — Bullish Near Support"
    result_name = "Potential_Bullish_1"
    needs_watchlist = False

    fields = [
        FieldDef("ema_daily_trend",  "Daily Trend EMA",  "int",   200,  5,      500,
                 tooltip="Daily trend EMA period (Price > EMAn Daily)"),
        FieldDef("ema_weekly_trend", "Weekly Trend EMA", "int",   200,  5,      500,
                 tooltip="Weekly trend EMA period (Price > EMAn Weekly)"),
        FieldDef("ema_support",      "Support EMA",      "int",    20,  3,      200,
                 tooltip="Support EMA — price must be within gap_max_pct% above this"),
        FieldDef("gap_max_pct",      "Gap Max %",        "float",  3.0, 0.1,  50.0, 1,
                 tooltip="Maximum % price can be above the support EMA"),
        FieldDef("perf_weekly_min",  "Perf W ≥ %",       "float",  0.0, -50.0, 50.0, 1,
                 tooltip="Weekly performance floor (%)"),
        FieldDef("min_mktcap_b",     "Min MktCap $B",    "float",  0.0,  0.0, 5000.0, 1,
                 tooltip="Minimum market cap in $B  (0 = no filter)"),
    ]

    @property
    def config_class(self):
        return S1J1Cfg

    def run(self, cfg: S1J1Cfg, universe: set, watchlist=None) -> list:
        dt   = f"EMA{cfg.ema_daily_trend}"
        wt   = f"EMA{cfg.ema_weekly_trend}|1W"
        ds   = f"EMA{cfg.ema_support}"
        cols = [
            "name", "description", "close",
            dt, wt, ds,
            "Perf.W", "RSI", "volume", "market_cap_basic",
            "sector", "change", "high", "low", "high|1W", "low|1W", "exchange",
        ]
        filt = [
            {"left": dt,       "operation": "less",    "right": "close"},
            {"left": wt,       "operation": "less",    "right": "close"},
            {"left": ds,       "operation": "less",    "right": "close"},
            {"left": "Perf.W", "operation": "greater", "right": cfg.perf_weekly_min},
        ]
        raw, out = tv_scan(filt, cols), []
        for item in raw:
            d = item["d"]
            try:
                sym, price, ema_s = d[0], (d[2] or 0), d[5]
                if sym not in universe or not price or not ema_s:
                    continue
                gap = (price - ema_s) / ema_s * 100
                if gap > cfg.gap_max_pct:
                    continue
                mc = d[9]
                if cfg.min_mktcap_b > 0 and (not mc or mc / 1e9 < cfg.min_mktcap_b):
                    continue
                out.append({
                    "Symbol":                              sym,
                    "Exchange":                            d[16] or "",
                    "Company":                             (d[1] or "")[:35],
                    "Price":                               round(price, 2),
                    f"EMA{cfg.ema_support}(1D)":           round(ema_s, 2),
                    "Gap_Supp%":                           round(gap, 2),
                    f"EMA{cfg.ema_daily_trend}(1D)":       round(d[3], 2) if d[3] else None,
                    f"EMA{cfg.ema_weekly_trend}(1W)":      round(d[4], 2) if d[4] else None,
                    "Perf_W%":                             round(d[6], 2) if d[6] is not None else None,
                    "RSI":                                 round(d[7], 1) if d[7] else None,
                    "Volume":                              int(d[8]) if d[8] else None,
                    "MktCap_B":                            round(mc / 1e9, 1) if mc else None,
                    "Sector":                              d[10] or "",
                    "Change%":                             round(d[11], 2) if d[11] is not None else None,
                    "Day_High":                            round(d[12], 2) if d[12] else None,
                    "Day_Low":                             round(d[13], 2) if d[13] else None,
                    "Wk_High":                             round(d[14], 2) if d[14] else None,
                    "Wk_Low":                              round(d[15], 2) if d[15] else None,
                })
            except Exception:
                continue
        return out

    def conditions_summary(self, cfg: S1J1Cfg):
        lines = [
            f"Price > EMA{cfg.ema_daily_trend} (1D)",
            f"Price > EMA{cfg.ema_weekly_trend} (1W)",
            f"EMA{cfg.ema_support} ≤ Price ≤ EMA{cfg.ema_support}×{1 + cfg.gap_max_pct/100:.3f}",
            f"Perf.W ≥ {cfg.perf_weekly_min:.1f}%",
        ]
        if cfg.min_mktcap_b > 0:
            lines.append(f"MktCap ≥ ${cfg.min_mktcap_b:.1f}B")
        return lines
