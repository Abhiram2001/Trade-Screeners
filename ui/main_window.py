"""MainWindow — builds tabs from the screener registry."""

import os
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QLabel

from constants import SETTINGS_FILE
from screeners import get_enabled_screeners
from .screener_tab import ScreenerTab
from .style import STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trade Screener")
        self.setMinimumSize(1200, 720)
        self.resize(1480, 860)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        for screener in get_enabled_screeners():
            tab = ScreenerTab(screener)
            tab.status_msg.connect(self.statusBar().showMessage)
            tabs.addTab(tab, f"{screener.tab_icon}  {screener.label}")

        self.setCentralWidget(tabs)

        sb = self.statusBar()
        sb.showMessage(
            "Ready  ·  Configure parameters on the left, then click Run Both  ·  "
            f"Settings persist in {os.path.basename(SETTINGS_FILE)}"
        )

        ver = QLabel("v2.0  ·  TradingView Data")
        ver.setStyleSheet("color:#4a5070; font-size:11px; margin-right:8px;")
        sb.addPermanentWidget(ver)


def main():
    import warnings
    warnings.filterwarnings("ignore")

    import importlib.util as _iutil
    _DEPS = [("pandas", "pandas"), ("requests", "requests"),
             ("PyQt5", "PyQt5"), ("openpyxl", "openpyxl")]
    _miss = [n for m, n in _DEPS if _iutil.find_spec(m) is None]
    if _miss:
        print(f"Missing packages. Run:\n  pip3 install {' '.join(_miss)}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("Trade Screener")
    app.setOrganizationName("TradeScreener")
    app.setStyle("Fusion")

    font = app.font()
    font.setPointSize(11)
    app.setFont(font)

    app.setStyleSheet(STYLE)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
