"""ConfigPanel — dynamically built from a BaseScreener's job field definitions."""

from PyQt5.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QFormLayout,
    QCheckBox, QSpinBox, QDoubleSpinBox, QLabel, QFrame,
)
from PyQt5.QtCore import Qt

from screeners.base import BaseScreener, FieldDef


class ConfigPanel(QScrollArea):
    """Scrollable left sidebar that renders itself from screener.jobs[*].fields.

    Adding a field to a job's ``fields`` list is all that's needed to make it
    appear here — no manual widget wiring required.
    """

    def __init__(self, screener: BaseScreener, saved: dict, parent=None):
        super().__init__(parent)
        self._screener = screener
        self.setWidgetResizable(True)
        self.setMinimumWidth(300)
        self.setMaximumWidth(360)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        container.setStyleSheet("background-color: #0d0f1a;")
        lay = QVBoxLayout(container)
        lay.setSpacing(12)
        lay.setContentsMargins(10, 12, 10, 20)

        # ── Universe (always first) ───────────────────────────────────────────
        lay.addWidget(self._section_hdr("Universe"))
        univ_box = self._section_box()
        ul = QVBoxLayout(univ_box)
        ul.setSpacing(8)
        ul.setContentsMargins(10, 10, 10, 10)

        self._universe_widgets: dict = {}
        for attr, label, default in [
            ("include_sp500",  "S&P 500  (≈503 stocks)",   True),
            ("include_ndx100", "Nasdaq 100  (≈101 stocks)", True),
        ]:
            cb = QCheckBox(label)
            cb.setChecked(bool(saved.get(attr, default)))
            cb.toggled.connect(self._update_conditions)
            ul.addWidget(cb)
            self._universe_widgets[attr] = cb
        lay.addWidget(univ_box)

        # ── Per-job sections ──────────────────────────────────────────────────
        self._job_widgets: list = []  # [{attr: widget}, ...] indexed by job index

        for job in screener.jobs:
            lay.addWidget(self._section_hdr(job.label))
            job_box = self._section_box()
            fl = self._form(job_box)
            widgets = {}

            for fdef in job.fields:
                w = self._make_widget(fdef, saved)
                fl.addRow(self._lbl(fdef.label), w)
                widgets[fdef.attr] = w

            self._job_widgets.append(widgets)
            lay.addWidget(job_box)

        # ── Active conditions summary ─────────────────────────────────────────
        lay.addWidget(self._section_hdr("Active Conditions"))
        self.cond_lbl = QLabel()
        self.cond_lbl.setWordWrap(True)
        self.cond_lbl.setStyleSheet(
            "color: #8090b0; font-size: 11px; padding: 10px 8px;"
            "background-color: #111428; border: 1px solid #2e3870; border-radius: 6px;"
        )
        lay.addWidget(self.cond_lbl)
        self._update_conditions()

        lay.addStretch()
        self.setWidget(container)

    # ── Widget factory ────────────────────────────────────────────────────────

    @staticmethod
    def _make_widget(fdef: FieldDef, saved: dict):
        """Create and return the appropriate input widget for *fdef*."""
        val = saved.get(fdef.attr, fdef.default)
        if fdef.kind == "bool":
            w = QCheckBox()
            w.setChecked(bool(val))
            return w
        if fdef.kind == "int":
            w = QSpinBox()
            w.setRange(fdef.min_val if fdef.min_val is not None else 0,
                       fdef.max_val if fdef.max_val is not None else 9999)
            w.setValue(int(val))
            w.setToolTip(fdef.tooltip)
            return w
        # float
        w = QDoubleSpinBox()
        w.setRange(fdef.min_val if fdef.min_val is not None else 0.0,
                   fdef.max_val if fdef.max_val is not None else 9999.0)
        w.setValue(float(val))
        w.setDecimals(fdef.decimals)
        w.setToolTip(fdef.tooltip)
        return w

    # ── Config extraction ─────────────────────────────────────────────────────

    def get_job_config(self, job_index: int):
        """Return a config dataclass instance for job *job_index*."""
        job     = self._screener.jobs[job_index]
        widgets = self._job_widgets[job_index]
        kwargs  = {}
        for fdef in job.fields:
            w = widgets[fdef.attr]
            if isinstance(w, QCheckBox):
                kwargs[fdef.attr] = w.isChecked()
            else:
                kwargs[fdef.attr] = w.value()
        return job.config_class(**kwargs)

    def get_universe_cfg(self) -> dict:
        """Return {'include_sp500': bool, 'include_ndx100': bool}."""
        return {attr: w.isChecked() for attr, w in self._universe_widgets.items()}

    def to_dict(self) -> dict:
        """Flatten all widget values into a single dict for settings persistence."""
        d = self.get_universe_cfg()
        for widgets in self._job_widgets:
            for attr, w in widgets.items():
                d[attr] = w.isChecked() if isinstance(w, QCheckBox) else w.value()
        return d

    # ── Conditions summary ────────────────────────────────────────────────────

    def _update_conditions(self):
        lines = []
        # Universe
        indices = [
            label
            for label, attr in [("S&P 500", "include_sp500"), ("Nasdaq 100", "include_ndx100")]
            if self._universe_widgets.get(attr, QCheckBox()).isChecked()
        ]
        if indices:
            lines.append(f"Universe: {', '.join(indices)}")
        # Per-job conditions
        for i, job in enumerate(self._screener.jobs):
            try:
                cfg = self.get_job_config(i)
                for cond in job.conditions_summary(cfg):
                    lines.append(f"J{i + 1}: {cond}")
            except Exception:
                pass
        self.cond_lbl.setText(
            "Active conditions:\n" + "\n".join(f"  ✓ {l}" for l in lines)
        )

        # Re-connect all widgets on first call (they may not have been connected yet)
        for w in self.findChildren((QSpinBox, QDoubleSpinBox, QCheckBox)):
            try:
                if isinstance(w, QCheckBox):
                    w.toggled.connect(self._update_conditions)
                else:
                    w.valueChanged.connect(self._update_conditions)
            except Exception:
                pass

    # ── Static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _section_hdr(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color: #aabcd8; background-color: transparent;"
            "font-size: 11px; font-weight: 700; padding: 4px 2px 2px 2px;"
        )
        return lbl

    @staticmethod
    def _section_box() -> QFrame:
        f = QFrame()
        f.setStyleSheet(
            "QFrame { background-color: #111428;"
            " border: 1px solid #2e3870; border-radius: 7px; }"
        )
        return f

    @staticmethod
    def _form(parent: QFrame) -> QFormLayout:
        fl = QFormLayout(parent)
        fl.setSpacing(9)
        fl.setContentsMargins(10, 10, 10, 10)
        fl.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        fl.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        return fl

    @staticmethod
    def _lbl(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color: #c8d4ec; background-color: transparent;"
            "font-size: 12px; font-weight: 500;"
        )
        return lbl
