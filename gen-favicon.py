#!/usr/bin/env python3
"""
Generate utxoWallet's favicon.png.

Rendered at 4x (512px) then downscaled to 128 with Lanczos resampling so
the strokes get proper antialiasing — the original ad-hoc 32px draw was
noticeably jagged on Retina displays.

Design: dark Brain-Wallet-palette field with a lime coin ring; inside, a
2×2 grid of small squares (UTXOs) with two filled and two outlined,
suggesting "you pick which coins go in." Distinctive at a glance and
on-brand with the rest of the dapp.
"""
from PIL import Image, ImageDraw

BG     = "#0a0a0f"
LIME   = "#80e600"
SUPER  = 4                  # supersample factor for antialiasing
TARGET = 128                # final icon size (px)
S      = TARGET * SUPER     # render size

img = Image.new("RGBA", (S, S), BG)
d   = ImageDraw.Draw(img)

# Outer ring (the coin)
margin = int(S * 0.07)
stroke = int(S * 0.045)
d.ellipse((margin, margin, S - margin, S - margin),
          outline=LIME, width=stroke)

# 2×2 selection grid inside. Two filled, two outlined — the "explicit UTXO
# selection" idea.
center  = S // 2
chip    = int(S * 0.20)
gap     = int(S * 0.05)
half_w  = chip + gap // 2
chips = [
    # (top-left x, top-left y, filled?)
    (center - chip - gap // 2, center - chip - gap // 2, True),   # ▣
    (center + gap // 2,        center - chip - gap // 2, False),  # ▢
    (center - chip - gap // 2, center + gap // 2,        False),  # ▢
    (center + gap // 2,        center + gap // 2,        True),   # ▣
]
chip_stroke = int(S * 0.028)
for x, y, filled in chips:
    box = (x, y, x + chip, y + chip)
    if filled:
        d.rectangle(box, fill=LIME)
    else:
        d.rectangle(box, outline=LIME, width=chip_stroke)

# Downscale to target size — Lanczos gives smooth edges.
img = img.resize((TARGET, TARGET), Image.LANCZOS)
img.save("favicon.png", "PNG", optimize=True)
print(f"Wrote favicon.png at {TARGET}×{TARGET}")
