#!/usr/bin/env python3
"""
Generate app icons for Trade Screener.

Outputs
-------
  assets/icon.ico    — Windows multi-size icon (16-256 px)
  assets/icon.icns   — macOS icon bundle (requires macOS with iconutil)

Usage
-----
  pip install pillow
  python create_icon.py

Run this once before building with PyInstaller.
The spec file (TradeScreener.spec) references assets/icon.ico and assets/icon.icns.
"""

import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# ── App colour palette (matches the dark UI theme) ────────────────────────────
BG       = (13,  15,  26, 255)    # #0d0f1a  dark navy background
GREEN    = (52, 211, 153, 255)    # #34d399  bullish candle / uptrend
RED      = (248, 113, 113, 255)   # #f87171  bearish candle
BLUE     = (108, 142, 247, 255)   # #6c8ef7  trend-line accent
BLUE_DIM = (58,  96, 232, 180)    # semi-transparent glow


def draw_icon(size: int) -> Image.Image:
    """Draw an upward-trending candlestick chart at *size* × *size* pixels."""
    img  = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)

    # All coordinates are designed in a 64-unit grid then scaled
    def p(v: float) -> float:
        return v * size / 64.0

    line_w = max(1, round(p(1.8)))

    # ── Three bullish candles in an uptrend (left=low, right=high) ────────────
    # (center_x, body_top, body_bottom, wick_top, wick_bottom)  — y=0 is top
    candles = [
        (13, 45, 55, 42, 58),   # left — lowest
        (32, 28, 40, 25, 44),   # centre
        (51, 13, 25, 10, 29),   # right — highest
    ]

    half_body = p(5.5)

    for xc, bt, bb, wt, wb in candles:
        cx = p(xc)
        # Shadow glow beneath the body (give depth)
        glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        gd   = ImageDraw.Draw(glow)
        gd.rectangle(
            [cx - half_body - p(2), p(bt) - p(2),
             cx + half_body + p(2), p(bb) + p(2)],
            fill=(*GREEN[:3], 50),
        )
        img = Image.alpha_composite(img, glow)
        draw = ImageDraw.Draw(img)

        # Wick
        draw.line([(cx, p(wt)), (cx, p(wb))], fill=GREEN, width=line_w)
        # Body
        draw.rectangle(
            [cx - half_body, p(bt), cx + half_body, p(bb)],
            fill=GREEN,
        )

    # ── Rising trend line in blue ─────────────────────────────────────────────
    trend_pts = [
        (p(4),  p(60)),
        (p(13), p(50)),
        (p(32), p(34)),
        (p(51), p(18)),
        (p(60), p(9)),
    ]
    for i in range(len(trend_pts) - 1):
        draw.line([trend_pts[i], trend_pts[i + 1]],
                  fill=BLUE, width=max(1, round(p(2.2))))

    # ── Subtle rounded-rect frame ─────────────────────────────────────────────
    margin = max(1, round(p(1.5)))
    draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=max(2, round(p(6))),
        outline=(*BLUE[:3], 80),
        width=max(1, round(p(1))),
    )

    return img


# ── Windows .ico ──────────────────────────────────────────────────────────────

def create_ico():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [draw_icon(s) for s in sizes]
    out = os.path.join(ASSETS_DIR, "icon.ico")
    images[0].save(
        out,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"✓  {out}")


# ── macOS .icns (requires macOS + iconutil) ───────────────────────────────────

def create_icns():
    if sys.platform != "darwin":
        print("⚠  Skipping .icns — iconutil is only available on macOS")
        return

    iconset = os.path.join(ASSETS_DIR, "icon.iconset")
    os.makedirs(iconset, exist_ok=True)

    # Required sizes per Apple HIG
    for size in [16, 32, 64, 128, 256, 512, 1024]:
        draw_icon(size).save(
            os.path.join(iconset, f"icon_{size}x{size}.png")
        )
        if size <= 512:
            draw_icon(size * 2).save(
                os.path.join(iconset, f"icon_{size}x{size}@2x.png")
            )

    out = os.path.join(ASSETS_DIR, "icon.icns")
    subprocess.run(
        ["iconutil", "-c", "icns", iconset, "-o", out],
        check=True,
    )
    shutil.rmtree(iconset)
    print(f"✓  {out}")


if __name__ == "__main__":
    print("Generating icons…")
    create_ico()
    create_icns()
    print("Done.")
