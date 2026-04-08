"""Generic background worker — runs N jobs for any BaseScreener."""

import json
import os

import requests
from PyQt5.QtCore import QThread, pyqtSignal

from api import get_index_tickers


class ScreenerWorker(QThread):
    """Runs one or more screener jobs off the main UI thread.

    Signals:
        log(str):           Progress / status message.
        job_done(int, list): Emitted after each job completes — (job_index, results).
        done():             Emitted when all requested jobs have finished.
        error(str):         Emitted on a fatal error; no further jobs will run.
    """

    log      = pyqtSignal(str)
    job_done = pyqtSignal(int, list)
    done     = pyqtSignal()
    error    = pyqtSignal(str)

    def __init__(self, screener, run_indices: list,
                 job_configs: dict, universe_cfg: dict, wl_file: str):
        """
        Args:
            screener:     A BaseScreener instance.
            run_indices:  Ordered list of job indices to execute (e.g. [0,1] or [0]).
            job_configs:  {job_index: config_dataclass_instance}
            universe_cfg: {'include_sp500': bool, 'include_ndx100': bool}
            wl_file:      Path to the JSON watchlist file used between jobs.
        """
        super().__init__()
        self.screener     = screener
        self.run_indices  = sorted(run_indices)
        self.job_configs  = job_configs
        self.universe_cfg = universe_cfg
        self.wl_file      = wl_file

    def run(self):
        # ── Build universe ────────────────────────────────────────────────────
        try:
            self.log.emit("Fetching index constituents from Wikipedia…")
            sp500, nasdaq = get_index_tickers()
            self.log.emit(f"S&P 500: {len(sp500)}  |  Nasdaq 100: {len(nasdaq)}")
        except Exception as e:
            self.error.emit(f"Failed to load universe: {e}")
            return

        universe = set()
        if self.universe_cfg.get("include_sp500", True):
            universe |= sp500
        if self.universe_cfg.get("include_ndx100", True):
            universe |= nasdaq
        self.log.emit(f"Universe: {len(universe)} unique tickers")

        jobs         = self.screener.jobs
        last_results = []

        for idx in self.run_indices:
            job = jobs[idx]
            cfg = self.job_configs[idx]

            # Resolve watchlist for jobs that need the previous job's output
            watchlist = None
            if job.needs_watchlist:
                if last_results:
                    watchlist = set(r["Symbol"] for r in last_results)
                    self.log.emit(
                        f"Running Job {idx + 1} — "
                        f"{len(watchlist)} symbols from Job {idx}…"
                    )
                else:
                    # Previous job wasn't in this run — try loading from disk
                    if not os.path.exists(self.wl_file):
                        self.error.emit(
                            f"Job {idx + 1}: watchlist not found — "
                            f"run Job {idx} first."
                        )
                        self.done.emit()
                        return
                    with open(self.wl_file) as f:
                        watchlist = set(json.load(f))
                    if not watchlist:
                        self.log.emit(
                            f"Job {idx + 1}: watchlist is empty — skipping."
                        )
                        self.done.emit()
                        return
                    self.log.emit(
                        f"Running Job {idx + 1} — "
                        f"{len(watchlist)} symbols from saved watchlist…"
                    )
            else:
                self.log.emit(
                    f"Running Job {idx + 1} — fetching from TradingView…"
                )

            try:
                results = job.run(cfg, universe, watchlist)

                # Persist this job's output if any later job needs it as watchlist
                later_jobs_need_wl = any(
                    jobs[j].needs_watchlist
                    for j in range(idx + 1, len(jobs))
                )
                if later_jobs_need_wl:
                    with open(self.wl_file, "w") as f:
                        json.dump([r["Symbol"] for r in results], f, indent=2)

                self.log.emit(
                    f"Job {idx + 1} complete: {len(results)} stocks matched ✓"
                )
                self.job_done.emit(idx, results)
                last_results = results

            except requests.HTTPError as e:
                self.error.emit(f"Job {idx + 1} API error: {e}")
                return
            except Exception as e:
                self.error.emit(f"Job {idx + 1} failed: {e}")
                return

        self.done.emit()
