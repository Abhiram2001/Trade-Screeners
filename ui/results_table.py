"""ResultsTable — sortable, filterable QTableWidget for screener results."""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont


class ResultsTable(QTableWidget):

    _RIGHT_ALIGN = {
        "Price", "Open", "Gap_Supp%", "Gap_Cross%", "Gap_Pull%",
        "Perf_W%", "RSI", "MktCap_B", "Change%",
        "Day_High", "Day_Low", "Wk_High", "Wk_Low", "Volume",
    }
    _PCT_POS  = {"Gap_Supp%", "Gap_Cross%"}   # always green
    _PCT_SIGN = {"Change%", "Perf_W%"}         # green/red by sign
    _PCT_NEG  = {"Gap_Pull%"}                  # negative expected (amber)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSortingEnabled(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSortIndicatorShown(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self._all_data: list = []
        self._cols: list = []

    def set_data(self, rows: list):
        self._all_data = rows
        if not rows:
            self.setRowCount(0)
            self.setColumnCount(0)
            self._cols = []
            return
        self._cols = list(rows[0].keys())
        self._populate(rows)

    def _populate(self, rows: list):
        self.setSortingEnabled(False)
        self.clearContents()
        self.setColumnCount(len(self._cols))
        self.setHorizontalHeaderLabels(self._cols)
        self.setRowCount(len(rows))

        for r, row in enumerate(rows):
            self.setRowHeight(r, 28)
            for c, col in enumerate(self._cols):
                val = row.get(col)
                item = QTableWidgetItem()

                if isinstance(val, (int, float)) and val is not None:
                    item.setData(Qt.DisplayRole, val)
                else:
                    item.setText("—" if val is None else str(val))

                if col in self._RIGHT_ALIGN:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                else:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

                if col == "Symbol":
                    item.setForeground(QColor("#6c8ef7"))
                    f = QFont()
                    f.setBold(True)
                    item.setFont(f)
                elif col in ("Sector", "Exchange", "MktCap_B"):
                    item.setForeground(QColor("#7a86a0"))
                elif col in self._PCT_POS and isinstance(val, float):
                    item.setForeground(QColor("#34d399"))
                elif col in self._PCT_SIGN and isinstance(val, float):
                    item.setForeground(QColor("#34d399") if val > 0 else QColor("#f87171"))
                elif col in self._PCT_NEG and isinstance(val, float):
                    item.setForeground(QColor("#fbbf24") if val < 0 else QColor("#34d399"))
                elif col == "RSI" and isinstance(val, float):
                    if val > 70:
                        item.setForeground(QColor("#f87171"))
                    elif val < 30:
                        item.setForeground(QColor("#fbbf24"))

                self.setItem(r, c, item)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)

    def filter_rows(self, text: str) -> int:
        text = text.lower()
        visible = 0
        for r in range(self.rowCount()):
            match = any(
                text in (self.item(r, c).text().lower() if self.item(r, c) else "")
                for c in range(self.columnCount())
            )
            self.setRowHidden(r, not match)
            if match:
                visible += 1
        return visible

    def visible_count(self) -> int:
        return sum(1 for r in range(self.rowCount()) if not self.isRowHidden(r))
