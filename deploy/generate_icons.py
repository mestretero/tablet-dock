"""PWA + tepsi ikonlarını üretir (frontend/icon-192.png, icon-512.png).

Yeni tarz: Apple-vari koyu zemin + sistem mavisi bento tile düzeni
(dock/dashboard kimliği). Tam kare zemin (maskable-uyumlu).
Çalıştır: python deploy/generate_icons.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "frontend"
BG_TOP = (30, 30, 34)        # üst (açık)
BG_BOT = (10, 10, 11)        # alt (koyu)
BLUE = (10, 132, 255)        # sistem mavisi
BLUE_HI = (74, 163, 255)     # parlak mavi (derinlik)


def make(size: int):
    img = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(img)

    # Koyu dikey gradient zemin (tam kare -> maskable uyumlu)
    for y in range(size):
        t = y / size
        d.line([(0, y), (size, y)], fill=(
            int(BG_TOP[0] * (1 - t) + BG_BOT[0] * t),
            int(BG_TOP[1] * (1 - t) + BG_BOT[1] * t),
            int(BG_TOP[2] * (1 - t) + BG_BOT[2] * t), 255))

    # Bento tile düzeni: solda büyük, sağda iki küçük (ortada, güvenli alan)
    m = size * 0.54
    mx = (size - m) / 2
    my = (size - m) / 2
    gap = m * 0.09
    rad = int(m * 0.17)
    big_w = m * 0.55
    right_x = mx + big_w + gap
    right_w = m - big_w - gap
    small_h = (m - gap) / 2

    def tile(x0, y0, x1, y1, col):
        d.rounded_rectangle([x0, y0, x1, y1], radius=rad, fill=col)

    tile(mx, my, mx + big_w, my + m, BLUE_HI)                       # büyük
    tile(right_x, my, right_x + right_w, my + small_h, BLUE)        # sağ üst
    tile(right_x, my + small_h + gap, right_x + right_w, my + m, BLUE)  # sağ alt

    path = OUT / f"icon-{size}.png"
    img.save(path)
    print(f"yazıldı: {path}")


for s in (192, 512):
    make(s)
