"""
Automated Watchlist Screener — TradingView
==========================================
Based on: Requirement1_doc_tradingview.docx

JOB 1 — Identify Potential Bullish Stocks
  Universe : S&P 500 + Nasdaq 100
  Conditions:
    • Daily  : Price > EMA 200        (long-term bullish trend)
    • Weekly : Price > EMA 200        (higher timeframe bullish trend)
    • Daily  : Price >= EMA 20        (at or above near-term support)
    • Daily  : Price <= EMA 20 * 1.03 (within 3% above EMA 20 — near support)
    • Weekly : Performance > 0%       (positive higher-timeframe momentum)
  Output : Potential_Bullish_1_<date>.html  +  job1_watchlist.json

JOB 2 — Identify 20 EMA Breakout Stocks
  Input  : Symbols from Job 1 watchlist (job1_watchlist.json)
  Condition : Same-day EMA 20 crossover — open ≤ EMA 20 AND close > EMA 20
  Output : Bullish_1_20ema_<date>.html  (recreated fresh every run)

Usage:
    python3 Screener.py          # Run both jobs
    python3 Screener.py job1     # Run Job 1 only
    python3 Screener.py job2     # Run Job 2 only (requires prior Job 1 run)

Schedule (crontab, weekdays 9 AM):
    0 9 * * 1-5  /path/to/.venv/bin/python /path/to/Screener.py >> screener.log 2>&1
"""

import json
import os
import ssl
import sys
import urllib.request
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=Warning, module="urllib3")

import pandas as pd
import requests
from tabulate import tabulate

# ── Constants ─────────────────────────────────────────────────────────────────

TRADINGVIEW_URL = "https://scanner.tradingview.com/america/scan"
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
WATCHLIST_FILE  = os.path.join(BASE_DIR, "job1_watchlist.json")

# ── Universe ──────────────────────────────────────────────────────────────────

def get_index_tickers() -> tuple[set, int, int]:
    """Fetch S&P 500 and Nasdaq 100 tickers from Wikipedia. Returns (combined_set, sp500_count, ndx_count)."""
    ctx = ssl._create_unverified_context()

    def _fetch(url, table_idx, col):
        req  = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, context=ctx).read()
        return set(pd.read_html(html)[table_idx][col].tolist())

    sp500  = _fetch("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", 0, "Symbol")
    nasdaq = _fetch("https://en.wikipedia.org/wiki/Nasdaq-100", 4, "Ticker")
    combined = sp500 | nasdaq
    print(f"  S&P 500: {len(sp500)}  |  Nasdaq 100: {len(nasdaq)}  |  Combined (unique): {len(combined)}")
    return combined, len(sp500), len(nasdaq)

# ── TradingView API ───────────────────────────────────────────────────────────

def fetch_screener(filters: list, columns: list, limit: int = 3000) -> dict:
    payload = {
        "filter":   filters,
        "options":  {"lang": "en"},
        "markets":  ["america"],
        "screener": "america",
        "symbols":  {"query": {"types": []}, "tickers": []},
        "columns":  columns,
        "sort":     {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range":    [0, limit],
    }
    resp = requests.post(TRADINGVIEW_URL, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

# ── JOB 1 ─────────────────────────────────────────────────────────────────────

_JOB1_COLUMNS = [
    "name",             # 0  Ticker
    "description",      # 1  Company name
    "close",            # 2  Price
    "EMA200",           # 3  EMA 200 Daily
    "EMA200|1W",        # 4  EMA 200 Weekly
    "EMA20",            # 5  EMA 20 Daily
    "Perf.W",           # 6  Weekly % performance
    "RSI",              # 7  RSI 14 Daily
    "volume",           # 8  Volume
    "market_cap_basic", # 9  Market cap
    "sector",           # 10 Sector
    "change",           # 11 Daily % change
]

_JOB1_FILTERS = [
    # Price above EMA 200 Daily → long-term daily bullish
    {"left": "EMA200",    "operation": "less",    "right": "close"},
    # Price above EMA 200 Weekly → higher-timeframe bullish
    {"left": "EMA200|1W", "operation": "less",    "right": "close"},
    # Price at or above EMA 20 Daily (client-side ≤3% cap applied below)
    {"left": "EMA20",     "operation": "less",    "right": "close"},
    # Weekly performance > 0% → positive momentum
    {"left": "Perf.W",    "operation": "greater", "right": 0},
]

def run_job1(universe: set, sp500_n: int, ndx_n: int) -> list[dict]:
    print("\n" + "─" * 60)
    print("  JOB 1 — Potential Bullish Stocks")
    print("─" * 60)
    print("  Conditions:")
    print("    ✓ Price > EMA 200 (Daily)")
    print("    ✓ Price > EMA 200 (Weekly)")
    print("    ✓ EMA 20 ≤ Price ≤ EMA 20 × 1.03  (within 3% above)")
    print("    ✓ Weekly Performance > 0%")

    data     = fetch_screener(_JOB1_FILTERS, _JOB1_COLUMNS)
    raw_rows = data.get("data", [])
    results  = []

    for item in raw_rows:
        d = item["d"]
        try:
            symbol  = d[0]
            price   = d[2] or 0
            ema20   = d[5]

            # Restrict to S&P 500 + Nasdaq 100 universe
            if symbol not in universe:
                continue
            if not ema20 or not price:
                continue

            # Client-side: price must be within 3% above EMA 20
            gap_pct = (price - ema20) / ema20 * 100
            if gap_pct > 3.0:
                continue

            ema200d = d[3]
            ema200w = d[4]
            perf_w  = d[6]
            mktcap  = d[9]

            results.append({
                "Symbol":      symbol,
                "Company":     (d[1] or "")[:30],
                "Price":       round(price, 2),
                "EMA20_1D":    round(ema20, 2),
                "Gap_EMA20%":  round(gap_pct, 2),
                "EMA200_1D":   round(ema200d, 2) if ema200d else None,
                "EMA200_1W":   round(ema200w, 2) if ema200w else None,
                "Perf_W%":     round(perf_w, 2) if perf_w is not None else None,
                "RSI_1D":      round(d[7], 1) if d[7] else None,
                "Volume":      int(d[8]) if d[8] else None,
                "MarketCap_B": round(mktcap / 1e9, 1) if mktcap else None,
                "Sector":      d[10] or "",
                "Change%":     round(d[11], 2) if d[11] is not None else None,
            })
        except Exception:
            continue

    print(f"\n  Screened {len(raw_rows)} US stocks  →  {len(results)} match in S&P500+NDX100 ✓")

    # Save watchlist for Job 2
    with open(WATCHLIST_FILE, "w") as f:
        json.dump([r["Symbol"] for r in results], f, indent=2)
    print(f"  Watchlist saved  → {WATCHLIST_FILE}")

    _print_console(results, "JOB 1 — Potential_Bullish_1",
                   ["Symbol","Company","Price","EMA20_1D","Gap_EMA20%","EMA200_1D","EMA200_1W","Perf_W%","RSI_1D","Change%","Sector"])
    _save_html(results, job_name="Potential_Bullish_1", job_num=1,
               universe_label=f"S&P 500 ({sp500_n}) + Nasdaq 100 ({ndx_n})",
               conditions=[
                   "Price > EMA 200 Daily",
                   "Price > EMA 200 Weekly",
                   "EMA 20 Daily ≤ Price ≤ EMA 20 Daily × 1.03",
                   "Weekly Performance > 0%",
               ])
    return results

# ── JOB 2 ─────────────────────────────────────────────────────────────────────

_JOB2_COLUMNS = [
    "name",             # 0
    "description",      # 1
    "close",            # 2
    "open",             # 3  Daily open — for crossover detection
    "EMA20",            # 4  EMA 20 Daily
    "EMA200",           # 5
    "EMA200|1W",        # 6
    "RSI",              # 7
    "volume",           # 8
    "market_cap_basic", # 9
    "sector",           # 10
    "change",           # 11
]

# Crossover: close crossed EMA20 today (both directions) → filter to upward cross client-side
_JOB2_FILTERS = [
    {"left": "close", "operation": "crosses", "right": "EMA20"},
]

def run_job2(universe: set, sp500_n: int, ndx_n: int) -> list[dict]:
    print("\n" + "─" * 60)
    print("  JOB 2 — 20 EMA Breakout Stocks")
    print("─" * 60)

    if not os.path.exists(WATCHLIST_FILE):
        print("  [error] job1_watchlist.json not found. Run Job 1 first.")
        return []

    with open(WATCHLIST_FILE) as f:
        job1_symbols = set(json.load(f))

    if not job1_symbols:
        print("  [warn] Job 1 watchlist is empty.")
        return []

    print(f"  Job 1 watchlist  : {len(job1_symbols)} symbols")
    print("  Crossover logic  : close crossed EMA 20 upward (close > EMA20, open ≤ EMA20)")

    data     = fetch_screener(_JOB2_FILTERS, _JOB2_COLUMNS)
    raw_rows = data.get("data", [])
    results  = []

    for item in raw_rows:
        d = item["d"]
        try:
            symbol = d[0]
            # Must be in the Job 1 watchlist
            if symbol not in job1_symbols:
                continue

            price   = d[2] or 0
            open_p  = d[3] or 0
            ema20   = d[4]
            ema200d = d[5]
            ema200w = d[6]
            mktcap  = d[9]

            if not ema20:
                continue

            # Keep only upward crosses (close > EMA20, open at/below EMA20)
            if not (price > ema20 and open_p <= ema20):
                continue

            results.append({
                "Symbol":      symbol,
                "Company":     (d[1] or "")[:30],
                "Price":       round(price, 2),
                "Open":        round(open_p, 2),
                "EMA20_1D":    round(ema20, 2),
                "Gap_EMA20%":  round((price - ema20) / ema20 * 100, 2),
                "EMA200_1D":   round(ema200d, 2) if ema200d else None,
                "EMA200_1W":   round(ema200w, 2) if ema200w else None,
                "RSI_1D":      round(d[7], 1) if d[7] else None,
                "Volume":      int(d[8]) if d[8] else None,
                "MarketCap_B": round(mktcap / 1e9, 1) if mktcap else None,
                "Sector":      d[10] or "",
                "Change%":     round(d[11], 2) if d[11] is not None else None,
            })
        except Exception:
            continue

    print(f"\n  EMA 20 crossovers found : {len(results)} stocks ✓")

    _print_console(results, "JOB 2 — Bullish_1_20ema",
                   ["Symbol","Company","Price","Open","EMA20_1D","Gap_EMA20%","EMA200_1D","RSI_1D","Change%","Sector"])
    _save_html(results, job_name="Bullish_1_20ema", job_num=2,
               universe_label=f"Job 1 watchlist ({len(job1_symbols)} symbols)",
               conditions=[
                   "Stock was in Job 1 Potential_Bullish_1 watchlist",
                   "Daily Close crossed above EMA 20 today (upward crossover)",
                   "Open ≤ EMA 20  AND  Close > EMA 20",
               ])
    return results

# ── Console output ────────────────────────────────────────────────────────────

def _print_console(rows: list[dict], title: str, display_keys: list) -> None:
    now = datetime.now().strftime("%Y-%m-%d  %H:%M")
    print()
    print("═" * 90)
    print(f"  {title}  ·  {now}  ·  {len(rows)} stocks")
    print("═" * 90)
    if not rows:
        print("  No stocks matched today.")
        print()
        return
    table_data = [[r.get(k, "") for k in display_keys] for r in rows]
    print(tabulate(table_data, headers=display_keys, tablefmt="simple", floatfmt=".2f"))
    print()

# ── HTML report ───────────────────────────────────────────────────────────────

def _save_html(rows: list[dict], job_name: str, job_num: int,
               universe_label: str, conditions: list[str]) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%B %d, %Y  %H:%M")
    filename = f"{job_name}_{date_str}.html"
    filepath = os.path.join(BASE_DIR, filename)

    job_color   = "#6c8ef7" if job_num == 1 else "#34d399"
    job_label   = "Potential Bullish" if job_num == 1 else "20 EMA Breakout"
    condition_html = "".join(f'<li>{c}</li>' for c in conditions)

    # Determine columns to display based on available keys
    if not rows:
        cols = []
    elif job_num == 1:
        cols = ["Symbol","Company","Price","EMA20_1D","Gap_EMA20%","EMA200_1D","EMA200_1W","Perf_W%","RSI_1D","Change%","MarketCap_B","Sector"]
    else:
        cols = ["Symbol","Company","Price","Open","EMA20_1D","Gap_EMA20%","EMA200_1D","EMA200_1W","RSI_1D","Change%","MarketCap_B","Sector"]

    col_headers = {
        "Symbol": "Symbol", "Company": "Company", "Price": "Price",
        "Open": "Open", "EMA20_1D": "EMA 20 (1D)", "Gap_EMA20%": "Gap EMA20%",
        "EMA200_1D": "EMA 200 (1D)", "EMA200_1W": "EMA 200 (1W)",
        "Perf_W%": "Perf W%", "RSI_1D": "RSI (1D)", "Change%": "Change%",
        "MarketCap_B": "Mkt Cap", "Sector": "Sector",
    }

    right_align = {"Price","Open","EMA20_1D","Gap_EMA20%","EMA200_1D","EMA200_1W","Perf_W%","RSI_1D","Change%","MarketCap_B"}

    thead = "".join(
        f'<th class="{"r" if c in right_align else "l"}" onclick="sortTable({i})">{col_headers.get(c,c)}</th>'
        for i, c in enumerate(cols)
    )

    tbody = ""
    for r in rows:
        cells = ""
        for c in cols:
            val = r.get(c, "")
            cls = "r" if c in right_align else "l"
            extra = ""
            if c == "Symbol":
                cls = "sym"
                display = val
            elif c == "Company":
                cls = "co"
                display = val
            elif c == "Sector":
                cls = "sector"
                display = val
            elif c == "MarketCap_B":
                cls = "r muted"
                display = f"${val}B" if val else "—"
            elif c == "Change%":
                try:
                    v = float(val)
                    extra = "pos" if v > 0 else ("neg" if v < 0 else "")
                    display = f"+{v:.2f}%" if v > 0 else f"{v:.2f}%"
                    cls = f"r {extra}".strip()
                except (TypeError, ValueError):
                    display = "—"
            elif c == "Gap_EMA20%":
                try:
                    v = float(val)
                    display = f"+{v:.2f}%"
                    cls = "r gap"
                except (TypeError, ValueError):
                    display = "—"
            elif c == "Perf_W%":
                try:
                    v = float(val)
                    extra = "pos" if v > 0 else ("neg" if v < 0 else "")
                    display = f"+{v:.2f}%" if v > 0 else f"{v:.2f}%"
                    cls = f"r {extra}".strip()
                except (TypeError, ValueError):
                    display = "—"
            elif c == "RSI_1D":
                try:
                    v = float(val)
                    extra = "rsi-high" if v > 70 else ("rsi-low" if v < 30 else "")
                    display = f"{v:.1f}"
                    cls = f"r {extra}".strip()
                except (TypeError, ValueError):
                    display = "—"
            elif c in ("Price","Open","EMA20_1D","EMA200_1D","EMA200_1W"):
                try:
                    display = f"${float(val):,.2f}"
                except (TypeError, ValueError):
                    display = "—"
            else:
                display = str(val) if val is not None else "—"
            cells += f'<td class="{cls}">{display}</td>'
        tbody += f"<tr>{cells}</tr>\n"

    empty_msg = "" if rows else '<tr><td colspan="20" style="text-align:center;padding:2rem;color:var(--muted)">No stocks matched today.</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{job_name} — {date_str}</title>
<style>
  :root {{
    --bg:       #0d0f1a; --surface: #141726; --surface2: #1c2038;
    --border:   #252a45; --text:    #dde4f0; --muted:    #7a86a0;
    --accent:   {job_color}; --green: #34d399; --red: #f87171; --yellow: #fbbf24;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Inter','Segoe UI',system-ui,sans-serif; padding:2rem; min-height:100vh; }}

  /* Header */
  .header {{ display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem; margin-bottom:1.8rem; }}
  .header h1 {{ font-size:1.6rem; font-weight:700; letter-spacing:-0.5px; }}
  .header h1 .accent {{ color:var(--accent); }}
  .job-badge {{ display:inline-block; background:var(--accent); color:#0d0f1a; font-size:0.72rem; font-weight:700;
                text-transform:uppercase; letter-spacing:1px; border-radius:20px; padding:0.2rem 0.75rem; margin-left:0.6rem; vertical-align:middle; }}
  .sub {{ color:var(--muted); font-size:0.83rem; margin-top:0.35rem; }}
  .timestamp {{ font-size:0.8rem; color:var(--muted); text-align:right; line-height:1.6; }}

  /* Stats */
  .stats {{ display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.6rem; }}
  .card {{ background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:0.85rem 1.3rem; min-width:130px; }}
  .card .lbl {{ font-size:0.7rem; text-transform:uppercase; letter-spacing:0.6px; color:var(--muted); }}
  .card .val {{ font-size:1.45rem; font-weight:700; color:var(--accent); margin-top:0.15rem; }}

  /* Conditions */
  .conditions {{ background:var(--surface); border:1px solid var(--border); border-radius:10px;
                 padding:1rem 1.4rem; margin-bottom:1.6rem; }}
  .conditions h3 {{ font-size:0.7rem; text-transform:uppercase; letter-spacing:0.6px; color:var(--muted); margin-bottom:0.6rem; }}
  .conditions ul {{ list-style:none; display:flex; flex-wrap:wrap; gap:0.4rem 1.2rem; }}
  .conditions li {{ font-size:0.82rem; color:var(--text); }}
  .conditions li::before {{ content:"✓ "; color:var(--accent); font-weight:700; }}

  /* Toolbar */
  .toolbar {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem; flex-wrap:wrap; gap:0.6rem; }}
  .search {{ background:var(--surface); border:1px solid var(--border); border-radius:8px;
             padding:0.5rem 1rem; color:var(--text); font-size:0.84rem; width:280px; outline:none; }}
  .search:focus {{ border-color:var(--accent); }}
  .search::placeholder {{ color:var(--muted); }}
  .count {{ font-size:0.82rem; color:var(--muted); }}

  /* Table */
  .wrap {{ overflow-x:auto; border-radius:12px; border:1px solid var(--border); }}
  table {{ width:100%; border-collapse:collapse; white-space:nowrap; }}
  thead th {{
    background:var(--surface2); color:var(--muted); font-size:0.7rem;
    text-transform:uppercase; letter-spacing:0.5px; padding:0.7rem 0.9rem;
    border-bottom:1px solid var(--border); cursor:pointer; user-select:none;
    position:sticky; top:0;
  }}
  thead th.r {{ text-align:right; }} thead th.l {{ text-align:left; }}
  thead th:hover {{ color:var(--text); }}
  thead th.asc::after  {{ content:" ▲"; color:var(--accent); font-size:0.6rem; }}
  thead th.desc::after {{ content:" ▼"; color:var(--accent); font-size:0.6rem; }}

  tbody tr {{ border-bottom:1px solid var(--border); transition:background 0.12s; }}
  tbody tr:last-child {{ border-bottom:none; }}
  tbody tr:hover {{ background:var(--surface2); }}
  td {{ padding:0.6rem 0.9rem; font-size:0.82rem; }}

  td.sym    {{ font-weight:700; color:var(--accent); font-family:'Fira Code','Consolas',monospace; letter-spacing:0.4px; }}
  td.co     {{ color:var(--text); max-width:180px; overflow:hidden; text-overflow:ellipsis; }}
  td.sector {{ font-size:0.75rem; color:var(--muted); }}
  td.r      {{ text-align:right; font-variant-numeric:tabular-nums; font-family:'Fira Code','Consolas',monospace; }}
  td.muted  {{ color:var(--muted); font-size:0.78rem; }}
  td.gap    {{ color:var(--green) !important; }}
  .pos      {{ color:var(--green) !important; }}
  .neg      {{ color:var(--red)   !important; }}
  .rsi-high {{ color:var(--red)   !important; }}
  .rsi-low  {{ color:var(--yellow)!important; }}

  /* Footer */
  .footer {{ margin-top:2rem; font-size:0.74rem; color:var(--muted); text-align:center; }}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1><span class="accent">Job {job_num}</span> — {job_label}<span class="job-badge">{job_name}</span></h1>
    <div class="sub">Universe: {universe_label} &nbsp;·&nbsp; Source: TradingView</div>
  </div>
  <div class="timestamp">Generated<br>{time_str}</div>
</div>

<div class="stats">
  <div class="card"><div class="lbl">Matched</div><div class="val">{len(rows)}</div></div>
  <div class="card"><div class="lbl">Job</div><div class="val" style="font-size:1rem;margin-top:0.3rem">{job_name}</div></div>
  <div class="card"><div class="lbl">Report Date</div><div class="val" style="font-size:0.95rem;margin-top:0.3rem">{date_str}</div></div>
</div>

<div class="conditions">
  <h3>Screening Conditions</h3>
  <ul>{condition_html}</ul>
</div>

<div class="toolbar">
  <input class="search" id="sb" type="text" placeholder="Search symbol, company, sector…" oninput="filterTable()">
  <span class="count" id="cnt">{len(rows)} stocks</span>
</div>

<div class="wrap">
  <table id="tbl">
    <thead><tr>{thead}</tr></thead>
    <tbody id="tb">{empty_msg}{tbody}</tbody>
  </table>
</div>

<div class="footer">
  Data: TradingView &nbsp;·&nbsp; Constituents: Wikipedia &nbsp;·&nbsp; <strong>Not financial advice.</strong>
</div>

<script>
let sc=-1, sd=1;
function sortTable(c){{
  const tb=document.getElementById('tb');
  const rows=[...tb.querySelectorAll('tr')];
  const ths=[...document.querySelectorAll('thead th')];
  ths.forEach(t=>t.classList.remove('asc','desc'));
  if(sc===c) sd*=-1; else {{sc=c;sd=1;}}
  ths[c].classList.add(sd===1?'asc':'desc');
  rows.sort((a,b)=>{{
    const av=a.cells[c]?.innerText.replace(/[$%+,B]/g,'')||'';
    const bv=b.cells[c]?.innerText.replace(/[$%+,B]/g,'')||'';
    const an=parseFloat(av), bn=parseFloat(bv);
    return(!isNaN(an)&&!isNaN(bn))?(an-bn)*sd:av.localeCompare(bv)*sd;
  }});
  rows.forEach(r=>tb.appendChild(r));
}}
function filterTable(){{
  const q=document.getElementById('sb').value.toLowerCase();
  const rows=document.querySelectorAll('#tb tr');
  let v=0;
  rows.forEach(r=>{{const m=r.innerText.toLowerCase().includes(q);r.style.display=m?'':'none';if(m)v++;}});
  document.getElementById('cnt').textContent=v+' stocks';
}}
</script>
</body></html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  HTML saved  → {filepath}")
    return filepath

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "both"
    if mode not in ("job1", "job2", "both"):
        print(f"Usage: python3 Screener.py [job1|job2|both]")
        sys.exit(1)

    print("=" * 60)
    print("  TradingView Automated Watchlist Screener")
    print(f"  Mode: {mode.upper()}  ·  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Load universe (needed for both jobs)
    print("\nFetching index constituents from Wikipedia …")
    try:
        universe, sp500_n, ndx_n = get_index_tickers()
    except Exception as e:
        print(f"  [error] Could not load universe: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if mode in ("job1", "both"):
            run_job1(universe, sp500_n, ndx_n)

        if mode in ("job2", "both"):
            run_job2(universe, sp500_n, ndx_n)

    except requests.HTTPError as e:
        print(f"\n[error] TradingView API error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.ConnectionError:
        print("\n[error] Connection failed – check internet connection.", file=sys.stderr)
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()

