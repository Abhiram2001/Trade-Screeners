# Trade Screener

A cross-platform desktop application that scans S&P 500 and Nasdaq 100 stocks against configurable technical conditions using live TradingView data.

Built with **PyQt5** · Data from **TradingView Scanner API** · Exports to **Excel**, **TradingView watchlist**, and **Interactive Brokers TWS**.

---

## Table of Contents

- [Features](#features)
- [Screeners](#screeners)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Running the App](#running-the-app)
- [Configuration](#configuration)
- [Exporting Results](#exporting-results)
- [Building a Desktop App Locally](#building-a-desktop-app-locally)
- [Building via GitHub Actions](#building-via-github-actions)
- [Adding a New Screener](#adding-a-new-screener)
- [Troubleshooting](#troubleshooting)

---

## Features

- 📈 Two built-in screeners with fully configurable parameters
- 🔍 Scans S&P 500 and/or Nasdaq 100 (≈600 stocks)
- ⚡ Background worker thread — UI never freezes
- 🎨 Dark theme, sortable/filterable results table
- 💾 Settings persist between sessions (`screener_settings.json`)
- 📊 Export to **Excel** (3 sheets: results, watchlist imports, sector summary)
- 📋 Export **TradingView watchlist** (`.txt`, ready to import)
- 📋 Export **Interactive Brokers TWS watchlist** (`.csv`)
- 🔌 Plugin architecture — add new screeners by dropping in a folder

---

## Screeners

### Screener 1 — Bullish Near Support

**Job 1** scans for stocks trading just above a key EMA support level while in a broader uptrend.

| Parameter | Default | Range | Description |
|---|---|---|---|
| Daily Trend EMA | 200 | 5–500 | Price must be **above** EMA(n) on daily chart |
| Weekly Trend EMA | 200 | 5–500 | Price must be **above** EMA(n) on weekly chart |
| Support EMA | 20 | 3–200 | Price must be within Gap Max % above this EMA |
| Gap Max % | 3.0 | 0.1–50 | Maximum % price can be above the support EMA |
| Perf W ≥ % | 0.0 | −50–50 | Minimum weekly performance floor |
| Min MktCap $B | 0.0 | 0–5000 | Minimum market cap (0 = no filter) |

**Job 2** filters Job 1 results to stocks where the daily close **crosses the EMA upward** today.

| Parameter | Default | Range | Description |
|---|---|---|---|
| Crossover EMA | 20 | 3–200 | EMA period for the upward crossover signal |

---

### Screener 2 — Weekly Bullish / Daily Pullback

**Job 1** finds stocks that are bullish on the weekly timeframe but currently pulling back on the daily — a potential re-entry zone.

| Parameter | Default | Range | Description |
|---|---|---|---|
| Weekly Trend EMA | 200 | 5–500 | Price must be **above** EMA(n) weekly |
| Daily Pullback EMA | 200 | 5–500 | Price must be **below** EMA(n) daily |
| Recovery EMA | 8 | 3–50 | Price must be **above** this short-term EMA |
| Min MktCap $B | 0.0 | 0–5000 | Minimum market cap (0 = no filter) |

**Job 2** is the same EMA crossover signal as Screener 1 Job 2, applied to the Job 1 watchlist.

---

## Project Structure

```
Trade-Screeners/
├── TradeScreener.py          # Entry point — run this to launch the app
├── pyproject.toml            # Project metadata and all dependencies
├── TradeScreener.spec        # PyInstaller build spec (macOS + Windows)
│
├── constants.py              # Paths and API URL
├── config.py                 # Settings load/save helpers
├── api.py                    # TradingView Scanner API wrapper
├── exports.py                # Excel, TradingView .txt, TWS .csv export
├── worker.py                 # Background QThread worker
│
├── screeners/                # Screener plugin packages
│   ├── base.py               # BaseScreener, BaseJob, FieldDef abstractions
│   ├── __init__.py           # Registry: @register + get_enabled_screeners()
│   ├── screener1/            # Screener 1 — Bullish Near Support
│   │   ├── job1.py
│   │   └── job2.py
│   └── screener2/            # Screener 2 — Weekly Bullish / Daily Pullback
│       ├── job1.py
│       └── job2.py
│
├── ui/                       # PyQt5 UI components
│   ├── style.py              # Global dark-theme QSS stylesheet
│   ├── results_table.py      # Sortable/filterable QTableWidget
│   ├── config_panel.py       # Auto-generated config sidebar
│   ├── screener_tab.py       # Per-screener tab (adapts to any screener)
│   └── main_window.py        # MainWindow + app entry point
│
└── .github/workflows/
    ├── build-macos.yml       # Builds macOS .dmg (Apple Silicon + Intel)
    ├── build-windows.yml     # Builds Windows .zip
    └── run-screener.yml      # Runs screener headlessly and uploads reports
```

---

## Prerequisites

- **Python 3.10 or higher**
- **Git**
- macOS 12+ or Windows 10+

Check your Python version:
```bash
python3 --version
```

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/Trade-Screeners.git
cd Trade-Screeners
```

### 2. Create a virtual environment

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install .
```

This installs all runtime dependencies declared in `pyproject.toml`.

---

## Running the App

```bash
python TradeScreener.py
```

Or, if installed as a package:
```bash
trade-screener
```

The app opens with two screener tabs. Configure parameters in the left panel and click **▶ Run Job 1**, **▶ Run Job 2**, or **▶▶ Run Both**.

---

## Configuration

All parameters are editable from the left sidebar:

- **Universe** — toggle S&P 500 and/or Nasdaq 100
- **Job 1 parameters** — EMA periods, gap threshold, market cap filter
- **Job 2 parameters** — crossover EMA period
- The **Active Conditions** panel updates live as you adjust values

Click **💾 Save Settings** to persist your configuration across sessions.  
Settings are stored in `screener_settings.json` in the project root.

---

## Exporting Results

After a run, use the export buttons in the bottom-right of each tab:

| Button | Output | Use |
|---|---|---|
| 📊 Export Excel | `.xlsx` (3 sheets) | Full results + both watchlist formats + sector breakdown |
| 📋 TradingView (.txt) | `.txt` | Import into TradingView → Watchlist → ⋮ → Import watchlist |
| 📋 Trader Workstation (.csv) | `.csv` | Import into IB TWS → File → Import Watchlist |

### TradingView import format
```
###watchlist name=Potential_Bullish_1
###Stocks,NASDAQ:AAPL,NASDAQ:TSLA,NYSE:GS,...
```

### Interactive Brokers TWS import format
```
SYM,AAPL,SMART/AMEX
SYM,TSLA,SMART/AMEX
```

---

## Building a Desktop App Locally

### 1. Install build dependencies

```bash
pip install ".[build]"
```

### 2. Build

```bash
# macOS — produces dist/TradeScreener.app
pyinstaller TradeScreener.spec --noconfirm

# Windows — produces dist/TradeScreener/TradeScreener.exe
pyinstaller TradeScreener.spec --noconfirm
```

### 3. Package for distribution

**macOS — create a DMG:**
```bash
mkdir -p dist/dmg_stage
cp -r dist/TradeScreener.app dist/dmg_stage/
ln -s /Applications dist/dmg_stage/Applications
hdiutil create -volname "TradeScreener" \
  -srcfolder dist/dmg_stage -ov -format UDZO \
  TradeScreener-macOS.dmg
```

**Windows — create a ZIP (PowerShell):**
```powershell
Compress-Archive -Path dist\TradeScreener -DestinationPath TradeScreener-Windows.zip
```

> **macOS Gatekeeper note:** Because the app is unsigned, macOS will warn when opening it the first time.  
> Right-click the `.app` → **Open** → **Open** to bypass the warning.

---

## Building via GitHub Actions

The repository includes two build workflows that can be triggered **manually** from the GitHub UI or **automatically** when you push a version tag.

### Trigger a manual build

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. Select **Build macOS App** or **Build Windows App** from the left sidebar
4. Click **Run workflow** → optionally enter a version label → **Run workflow**
5. Wait for the job to complete (≈ 5–10 minutes)
6. Download the artifact from the **Artifacts** section of the completed run

### Trigger an automatic release build

Push a version tag — both macOS and Windows builds run automatically and the artifacts are attached to a new GitHub Release:

```bash
git tag v2.1.0
git push --tags
```

This triggers:
- `Build macOS App` → produces `TradeScreener-macOS-arm64.dmg` (Apple Silicon) and `TradeScreener-macOS-x86_64.dmg` (Intel)
- `Build Windows App` → produces `TradeScreener-Windows-x64.zip`

All three files are uploaded to a new GitHub Release automatically.

### Workflow files

| File | Trigger | Output |
|---|---|---|
| `.github/workflows/build-macos.yml` | manual / `v*` tag | `.dmg` (arm64 + x86_64) |
| `.github/workflows/build-windows.yml` | manual / `v*` tag | `.zip` (x64) |
| `.github/workflows/run-screener.yml` | manual | HTML reports as artifacts |

---

## Adding a New Screener

The app auto-discovers screeners via a plugin registry. To add one:

### 1. Create the package

```
screeners/
└── screener3/
    ├── __init__.py
    ├── job1.py       ← your job implementation
    └── job2.py       ← optional second job
```

### 2. Define a job

```python
# screeners/screener3/job1.py
from dataclasses import dataclass
from screeners.base import BaseJob, FieldDef
from api import tv_scan

@dataclass
class MyJobCfg:
    my_ema: int = 50

class Job1(BaseJob):
    label       = "Job 1 — My Custom Scan"
    result_name = "My_Scan_Results"
    needs_watchlist = False

    fields = [
        FieldDef("my_ema", "EMA Period", "int", 50, 5, 500,
                 tooltip="EMA period for the scan"),
    ]

    @property
    def config_class(self):
        return MyJobCfg

    def run(self, cfg: MyJobCfg, universe: set, watchlist=None) -> list:
        # ... call tv_scan() and return list of result dicts
        return []

    def conditions_summary(self, cfg) -> list:
        return [f"Price > EMA{cfg.my_ema}"]
```

### 3. Register the screener

```python
# screeners/screener3/__init__.py
from screeners.base import BaseScreener
from screeners import register
from .job1 import Job1

@register
class Screener3(BaseScreener):
    id       = 3
    label    = "Screener 3 — My Custom Screener"
    tab_icon = "🔍"
    enabled  = True          # set False to hide without deleting

    @property
    def jobs(self):
        return [Job1()]
```

### 4. Add to the registry

In `screeners/__init__.py`, add one line at the bottom:

```python
from . import screener1, screener2, screener3  # add screener3
```

Restart the app — the new screener appears as a tab automatically.

> **Disabling a screener** without removing it: set `enabled = False` on the class.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Missing packages` error on launch | Run `pip install .` inside your virtual environment |
| `400 Bad Request` from TradingView | Usually a transient API rate-limit — wait 30 seconds and retry |
| Font warning about "Segoe UI" | Harmless on macOS — the app uses the system font |
| macOS: "app is damaged" | Run `xattr -cr TradeScreener.app` in Terminal to clear quarantine |
| Windows: antivirus flags the exe | Add an exclusion for the `dist\TradeScreener` folder; this is a false positive from PyInstaller |
| Settings not saving | Check write permissions on the project root directory |
