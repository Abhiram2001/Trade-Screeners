"""Application-wide QSS dark theme stylesheet."""

STYLE = """
QMainWindow, QWidget {
    background-color: #0d0f1a;
    color: #dde4f0;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #2a3060;
    background-color: #141726;
}
QTabWidget > QTabBar { alignment: left; }
QTabBar { font-size: 13px; }
QTabBar::tab {
    background-color: #0d0f1a;
    color: #8090a8;
    padding: 10px 30px;
    min-width: 260px;
    border: 1px solid #2a3060;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    margin-right: 4px;
    font-weight: 600;
    font-size: 13px;
}
QTabBar::tab:selected { background-color: #141726; color: #ffffff; border-color: #6c8ef7; }
QTabBar::tab:hover:!selected { color: #dde4f0; background-color: #141726; }
QLabel { color: #dde4f0; }
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #1a1f3a;
    border: 1px solid #2a3060;
    border-radius: 6px;
    color: #dde4f0;
    padding: 4px 6px;
    min-height: 26px;
    font-size: 12px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #6c8ef7;
    background-color: #1e2548;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 20px;
    background-color: #3a4888;
    border: none;
    border-left: 1px solid #2a3060;
}
QSpinBox::up-button { subcontrol-position: top right; border-radius: 0 4px 0 0; }
QSpinBox::down-button { subcontrol-position: bottom right; border-radius: 0 0 4px 0; }
QDoubleSpinBox::up-button { subcontrol-position: top right; border-radius: 0 4px 0 0; }
QDoubleSpinBox::down-button { subcontrol-position: bottom right; border-radius: 0 0 4px 0; }
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #5568b8;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 7px;
    height: 5px;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 7px;
    height: 5px;
}
QCheckBox { spacing: 8px; color: #c8d4ec; font-size: 13px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 1px solid #3a4070;
    background-color: #1a1f3a;
}
QCheckBox::indicator:checked { background-color: #6c8ef7; border-color: #6c8ef7; }
QPushButton {
    background-color: #1e2545;
    color: #c8d0e2;
    border: 1px solid #3a4870;
    border-radius: 7px;
    padding: 7px 18px;
    font-weight: 600;
    min-height: 30px;
    font-size: 13px;
}
QPushButton:hover { background-color: #2a3570; border-color: #6c8ef7; color: #ffffff; }
QPushButton:pressed { background-color: #141726; }
QPushButton:disabled { color: #3a4060; border-color: #1c2038; background-color: #0f1220; }
QPushButton#btnPrimary {
    background-color: #3a60e8;
    color: #ffffff;
    border: 2px solid #5a80f8;
    font-weight: 700;
    font-size: 13px;
}
QPushButton#btnPrimary:hover { background-color: #4a6eec; border-color: #6a88f8; }
QPushButton#btnPrimary:pressed { background-color: #2a50d0; }
QPushButton#btnPrimary:disabled { background-color: #1e2545; color: #3a4060; border-color: #252a45; }
QPushButton#btnDanger { background-color: #5a1818; color: #ff9090; border: 1px solid #8a2828; }
QPushButton#btnDanger:hover { background-color: #8a2828; color: #ffffff; }
QPushButton#btnSuccess { background-color: #163828; color: #34d399; border: 1px solid #1e5038; }
QPushButton#btnSuccess:hover { background-color: #1e5038; color: #5de8ae; }
QPushButton#btnTV { background-color: #162818; color: #34d399; border: 1px solid #1e4028; }
QPushButton#btnTV:hover { background-color: #1e4028; color: #5de8ae; }
QPushButton#btnTWS { background-color: #1a1a2e; color: #a78bfa; border: 1px solid #2e2a5a; }
QPushButton#btnTWS:hover { background-color: #2a2a4e; color: #c4b5fd; }
QTableWidget {
    background-color: #141726;
    border: none;
    gridline-color: #1c2038;
    color: #dde4f0;
    font-size: 12px;
    selection-background-color: #252a45;
    alternate-background-color: #161929;
}
QTableWidget QHeaderView::section {
    background-color: #1c2038;
    color: #8892aa;
    border: none;
    border-right: 1px solid #252a45;
    border-bottom: 1px solid #252a45;
    padding: 7px 10px;
    font-size: 11px;
    font-weight: 700;
}
QTableWidget QHeaderView::section:hover { color: #dde4f0; background-color: #252a45; }
QTableWidget::item { padding: 5px 8px; border-bottom: 1px solid #1c2038; }
QTableWidget::item:selected { background-color: #252a45; }
QScrollBar:vertical { background-color: #0d0f1a; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background-color: #2a3060; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background-color: #0d0f1a; height: 8px; margin: 0; }
QScrollBar::handle:horizontal { background-color: #2a3060; border-radius: 4px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QStatusBar {
    background-color: #080a12;
    color: #7a86a0;
    border-top: 1px solid #1c2038;
    padding: 4px 12px;
    font-size: 12px;
}
QProgressBar {
    background-color: #141726;
    border: 1px solid #252a45;
    border-radius: 4px;
    color: transparent;
    max-height: 6px;
}
QProgressBar::chunk { background-color: #6c8ef7; border-radius: 4px; }
QSplitter::handle { background-color: #252a45; }
QSplitter::handle:horizontal { width: 1px; }
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QTextEdit {
    background-color: #080a12;
    color: #6a7890;
    border: none;
    border-top: 1px solid #1c2038;
    font-family: 'Menlo', 'Consolas', monospace;
    font-size: 11px;
}
"""
