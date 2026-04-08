"""ScreenerTab — generic tab driven by any BaseScreener instance."""

import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QPushButton, QLabel, QLineEdit, QFrame, QProgressBar,
    QTextEdit, QFileDialog, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from config import load_settings, save_settings
from constants import BASE_DIR
from exports import export_excel, export_tradingview, export_tws
from screeners.base import BaseScreener
from worker import ScreenerWorker
from .config_panel import ConfigPanel
from .results_table import ResultsTable

_WL_FILE_TPL = os.path.join(BASE_DIR, "s{id}_watchlist.json")


class ScreenerTab(QWidget):
    """Full UI tab for one screener.

    Works with any BaseScreener that declares one or more jobs.
    The toolbar, result tabs, and config panel all adapt to the screener's job list.
    """

    status_msg = pyqtSignal(str)

    def __init__(self, screener: BaseScreener, parent=None):
        super().__init__(parent)
        self.screener      = screener
        self.wl_file       = _WL_FILE_TPL.format(id=screener.id)
        self.worker        = None
        self._job_results  = [[] for _ in screener.jobs]

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        saved = load_settings().get(f"s{screener.id}", {})
        self.cfg_panel = ConfigPanel(screener, saved)
        splitter.addWidget(self.cfg_panel)

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(10, 10, 10, 6)
        rv.setSpacing(8)

        # Search + count bar
        hbar = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search symbol, company, sector…")
        self.search_box.textChanged.connect(self._on_filter)
        self.count_lbl = QLabel("—")
        self.count_lbl.setStyleSheet("color:#7a86a0; font-size:12px; min-width:80px;")
        hbar.addWidget(self.search_box)
        hbar.addWidget(self.count_lbl)
        rv.addLayout(hbar)

        # One result tab per job
        self.res_tabs       = QTabWidget()
        self._result_tables = []
        for job in screener.jobs:
            tbl = ResultsTable()
            self.res_tabs.addTab(tbl, job.label)
            self._result_tables.append(tbl)
        self.res_tabs.currentChanged.connect(self._on_tab_change)
        rv.addWidget(self.res_tabs)

        # Export bar
        ebar = QHBoxLayout()
        ebar.addStretch()

        self.btn_save_cfg = QPushButton("💾  Save Settings")
        self.btn_save_cfg.setToolTip("Save current configuration to disk")
        self.btn_save_cfg.clicked.connect(self._save_config)

        self.btn_xl = QPushButton("📊  Export Excel")
        self.btn_xl.setObjectName("btnSuccess")
        self.btn_xl.setToolTip("Export full results + import sheets to .xlsx")
        self.btn_xl.clicked.connect(self._export_excel)

        self.btn_tv = QPushButton("📋  TradingView (.txt)")
        self.btn_tv.setObjectName("btnTV")
        self.btn_tv.setToolTip(
            "Export TradingView-importable watchlist (.txt)\n"
            "TradingView → Watchlist → ⋮ → Import watchlist"
        )
        self.btn_tv.clicked.connect(self._export_tv)

        self.btn_tws = QPushButton("📋  Trader Workstation (.csv)")
        self.btn_tws.setObjectName("btnTWS")
        self.btn_tws.setToolTip(
            "Export Interactive Brokers TWS-importable watchlist (.csv)\n"
            "TWS → File → Import Watchlist"
        )
        self.btn_tws.clicked.connect(self._export_tws)

        for b in (self.btn_save_cfg, self.btn_xl, self.btn_tv, self.btn_tws):
            ebar.addWidget(b)
        rv.addLayout(ebar)

        splitter.addWidget(right)
        splitter.setSizes([330, 900])
        root.addWidget(splitter)

        # Log panel
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(90)
        self.log_box.setPlaceholderText("Run log will appear here…")
        root.addWidget(self.log_box)

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _build_toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet("background:#141726; border-bottom:1px solid #252a45;")
        bar.setFixedHeight(58)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(10)

        n = len(self.screener.jobs)

        # Individual job buttons
        self._run_btns = []
        for i in range(n):
            btn = QPushButton(f"▶  Run Job {i + 1}")
            btn.setToolTip(self.screener.jobs[i].label)
            btn.clicked.connect(lambda _, idx=i: self._run([idx]))
            self._run_btns.append(btn)

        # "Run All" only when there are multiple jobs
        self.btn_all = None
        if n > 1:
            self.btn_all = QPushButton("▶▶  Run Both" if n == 2 else "▶▶  Run All")
            self.btn_all.setToolTip("Run all jobs sequentially")
            self.btn_all.clicked.connect(lambda: self._run(list(range(n))))

        self.btn_stop = QPushButton("■  Stop")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setMaximumWidth(160)
        self.progress.setMaximumHeight(6)

        title = QLabel(f"Screener {self.screener.id}")
        title.setStyleSheet("color:#7a86a0; font-size:11px; font-weight:600;")

        lay.addWidget(title)
        lay.addSpacing(8)
        for btn in self._run_btns:
            lay.addWidget(btn)
        if self.btn_all:
            lay.addWidget(self.btn_all)
        lay.addWidget(self.btn_stop)
        lay.addStretch()
        lay.addWidget(self.progress)
        return bar

    # ── Run / stop ────────────────────────────────────────────────────────────

    def _run(self, run_indices: list):
        if self.worker and self.worker.isRunning():
            return

        job_configs = {
            i: self.cfg_panel.get_job_config(i)
            for i in range(len(self.screener.jobs))
        }
        universe_cfg = self.cfg_panel.get_universe_cfg()

        self.worker = ScreenerWorker(
            screener     = self.screener,
            run_indices  = run_indices,
            job_configs  = job_configs,
            universe_cfg = universe_cfg,
            wl_file      = self.wl_file,
        )
        self.worker.log.connect(self._log)
        self.worker.job_done.connect(self._on_job_done)
        self.worker.done.connect(self._on_done)
        self.worker.error.connect(self._on_error)

        label = ("BOTH" if len(run_indices) > 1
                 else f"JOB {run_indices[0] + 1}")
        self._set_busy(True)
        self._log(f"Starting {label} …")
        self.worker.start()

    def _stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self._log("Run cancelled.")
            self._set_busy(False)

    def _set_busy(self, busy: bool):
        for btn in self._run_btns:
            btn.setEnabled(not busy)
        if self.btn_all:
            self.btn_all.setEnabled(not busy)
        self.btn_stop.setEnabled(busy)
        self.progress.setVisible(busy)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f'<span style="color:#4a5070">[{ts}]</span> {msg}')
        self.status_msg.emit(msg)

    def _on_job_done(self, job_index: int, results: list):
        self._job_results[job_index] = results
        self._result_tables[job_index].set_data(results)
        self.res_tabs.setCurrentIndex(job_index)
        self._refresh_count()

    def _on_done(self):
        self._set_busy(False)
        self._log("Done.")

    def _on_error(self, msg: str):
        self._log(f'<span style="color:#f87171">ERROR: {msg}</span>')
        self._set_busy(False)

    def _on_filter(self, text: str):
        n = self._active_table().filter_rows(text)
        self.count_lbl.setText(f"{n} stocks")

    def _on_tab_change(self):
        self.search_box.clear()
        self._refresh_count()

    def _refresh_count(self):
        self.count_lbl.setText(f"{self._active_table().visible_count()} stocks")

    def _active_table(self) -> ResultsTable:
        return self._result_tables[self.res_tabs.currentIndex()]

    def _current_job_info(self) -> tuple:
        """Return (results, result_name, job_num) for the active result tab."""
        idx        = self.res_tabs.currentIndex()
        results    = self._job_results[idx]
        job        = self.screener.jobs[idx]
        result_name = job.result_name or f"Screener{self.screener.id}_Job{idx + 1}"
        return results, result_name, idx + 1

    # ── Config persistence ────────────────────────────────────────────────────

    def _save_config(self):
        all_s = load_settings()
        all_s[f"s{self.screener.id}"] = self.cfg_panel.to_dict()
        save_settings(all_s)
        self._log("Settings saved.")
        self.status_msg.emit("Settings saved ✓")

    # ── Exports ───────────────────────────────────────────────────────────────

    def _export_excel(self):
        results, result_name, job_num = self._current_job_info()
        if not results:
            QMessageBox.information(self, "No Data",
                "No results to export.\nRun the screener first.")
            return
        date_str = datetime.now().strftime("%Y-%m-%d")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel Report",
            os.path.join(BASE_DIR, f"{result_name}_{date_str}.xlsx"),
            "Excel Workbook (*.xlsx)",
        )
        if not path:
            return
        try:
            export_excel(results, result_name, self.screener.id, job_num, path)
            self._log(f"Excel saved → {path}")
            QMessageBox.information(self, "Export Successful",
                f"Excel workbook saved:\n{path}\n\n"
                "Sheets included:\n"
                "  • Screener Results — full data table\n"
                "  • TradingView Import — symbols for watchlist import\n"
                "  • Summary — match count and sector breakdown")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _export_tv(self):
        results, result_name, _ = self._current_job_info()
        if not results:
            QMessageBox.information(self, "No Data",
                "No results to export.\nRun the screener first.")
            return
        date_str = datetime.now().strftime("%Y-%m-%d")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export TradingView Watchlist",
            os.path.join(BASE_DIR, f"{result_name}_{date_str}.txt"),
            "TradingView Watchlist (*.txt)",
        )
        if not path:
            return
        try:
            export_tradingview(results, result_name, path)
            self._log(f"TradingView watchlist saved → {path}")
            QMessageBox.information(self, "TradingView Export Successful",
                f"Watchlist saved ({len(results)} symbols):\n{path}\n\n"
                "How to import into TradingView:\n"
                "  1. Open TradingView → Watchlist panel\n"
                "  2. Click ⋮ (More options) → Import watchlist\n"
                "  3. Select this .txt file")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _export_tws(self):
        results, result_name, _ = self._current_job_info()
        if not results:
            QMessageBox.information(self, "No Data",
                "No results to export.\nRun the screener first.")
            return
        date_str = datetime.now().strftime("%Y-%m-%d")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Trader Workstation Watchlist",
            os.path.join(BASE_DIR, f"{result_name}_TWS_{date_str}.csv"),
            "TWS Watchlist CSV (*.csv)",
        )
        if not path:
            return
        try:
            export_tws(results, path)
            self._log(f"Trader Workstation watchlist saved → {path}")
            QMessageBox.information(self, "TWS Export Successful",
                f"Watchlist saved ({len(results)} symbols):\n{path}\n\n"
                "How to import into Interactive Brokers TWS:\n"
                "  1. Open TWS → File → Import Watchlist\n"
                "  2. Select this .csv file")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
