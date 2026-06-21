"""Uygulama ikonlarını exe'lerden çıkarıp önbelleğe alır (256px → 128px PNG).

Kaynak: app['icon_from'] varsa o, yoksa .exe path'i. Klasör/.lnk (icon_from'suz)
için None → panel harf monogramına düşer. icoextract + Pillow ile yüksek kalite.
"""
import os
from pathlib import Path

from config import BASE_DIR

CACHE_DIR = BASE_DIR / ".icon-cache"


def icon_source(app: dict):
    """İkonun çıkarılacağı exe yolu, ya da None (klasör/kaynak yok)."""
    src = app.get("icon_from") or (app["path"] if app["path"].lower().endswith(".exe") else None)
    return src if src and os.path.exists(src) else None


def extract_exe_icon(src, cache_id: str):
    """src exe'sinden ikonu çıkar, .icon-cache/{cache_id}.png döndür. Yoksa None.
    (Hem uygulama tile'ları hem Epic oyunları kullanır.)"""
    if not src or not os.path.exists(src):
        return None
    out = CACHE_DIR / (cache_id + ".png")
    if out.exists():
        return out
    try:
        from icoextract import IconExtractor
        from PIL import Image

        data = IconExtractor(src).get_icon()      # en büyük boyutlu .ico (BytesIO)
        img = Image.open(data).convert("RGBA")
        if max(img.size) > 128:                    # tile ~54px; 128 yeterli + küçük dosya
            img = img.resize((128, 128), Image.LANCZOS)
        CACHE_DIR.mkdir(exist_ok=True)
        img.save(out)
        return out
    except Exception:
        return None                                # çıkarılamadı -> harf monogramı


def ensure_icon(app: dict):
    """App için PNG ikon yolunu döndür (önbellekte yoksa çıkarır). Yoksa None."""
    return extract_exe_icon(icon_source(app), app["id"])
