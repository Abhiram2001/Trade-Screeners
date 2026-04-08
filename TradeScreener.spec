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
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ── Collect all submodules from local packages ────────────────────────────────
# This ensures dynamically-registered screeners are always bundled.
hidden = (
    collect_submodules("screeners")
    + collect_submodules("ui")
    + collect_submodules("openpyxl")
    + collect_submodules("lxml")
    + [
        # PyQt5 core (hooks usually handle these, but be explicit)
        "PyQt5.sip",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtNetwork",
        "PyQt5.QtPrintSupport",
        # pandas HTML parser backends
        "lxml.etree",
        "lxml.html",
        "html5lib",
        # requests / network stack
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "idna",
        "ssl",
        # Local app modules (explicit, for safety)
        "constants",
        "config",
        "api",
        "exports",
        "worker",
    ]
)

a = Analysis(
    ["TradeScreener.py"],
    pathex=["."],          # repo root on sys.path so local packages are found
    binaries=[],
    datas=[],
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
