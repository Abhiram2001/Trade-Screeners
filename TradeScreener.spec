# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Trade Screener Desktop Application.

Produces:
  macOS  → dist/TradeScreener.app  (wrap with DMG for distribution)
  Windows → dist/TradeScreener/TradeScreener.exe  (zip for distribution)

Build locally:
  pip install pyinstaller pyinstaller-hooks-contrib
  pyinstaller TradeScreener.spec
"""

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_all

block_cipher = None

# ── Collect all submodules from local packages ────────────────────────────────
# This ensures dynamically-registered screeners are always bundled.
lxml_mods, lxml_bins, lxml_data             = collect_all("lxml")
html5lib_mods, html5lib_bins, html5lib_data = collect_all("html5lib")

hidden = (
    collect_submodules("screeners")
    + collect_submodules("ui")
    + collect_submodules("openpyxl")
    + lxml_mods
    + html5lib_mods
    + [
        # PyQt5 core (hooks usually handle these, but be explicit)
        "PyQt5.sip",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtNetwork",
        "PyQt5.QtPrintSupport",
        # requests / network stack
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "idna",
        # Local app modules (explicit, for safety)
        "constants",
        "config",
        "api",
        "exports",
        "worker",
    ]
)
# Guard against None / non-string entries from hook helpers
hidden = [m for m in hidden if isinstance(m, str)]

# Bundle certifi SSL certs so requests verifies HTTPS in the frozen app
datas = (
    [d for d in lxml_data    if isinstance(d, tuple)]
    + [d for d in html5lib_data if isinstance(d, tuple)]
    + collect_data_files("certifi")
)

_extra_bins = (
    [b for b in lxml_bins    if isinstance(b, tuple)]
    + [b for b in html5lib_bins if isinstance(b, tuple)]
)

a = Analysis(
    ["TradeScreener.py"],
    pathex=["."],          # repo root on sys.path so local packages are found
    binaries=_extra_bins,
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "scipy",
        "notebook",
        "IPython",
        "pytest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── macOS: .app bundle ────────────────────────────────────────────────────────
if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="TradeScreener",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,       # None = current arch; set 'universal2' for fat binary
        codesign_identity=None,
        entitlements_file=None,
        icon="assets/icon.icns",
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="TradeScreener",
    )

    app = BUNDLE(
        coll,
        name="TradeScreener.app",
        icon="assets/icon.icns",
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSAppleScriptEnabled": False,
            "CFBundleDisplayName": "Trade Screener",
            "CFBundleShortVersionString": "2.0.0",
            "NSHighResolutionCapable": True,
            # Allow outbound network connections (required for TradingView API)
            "NSAppTransportSecurity": {
                "NSAllowsArbitraryLoads": True,
            },
        },
    )

# ── Windows / Linux: directory build ─────────────────────────────────────────
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="TradeScreener",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,              # UPX off — avoids antivirus false positives
        console=False,          # no terminal window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon="assets/icon.ico",              # replace with 'assets/icon.ico' if you add one
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="TradeScreener",
    )
