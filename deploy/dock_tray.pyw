"""Sistem tepsisi uygulaması - dock ajanını PENCERESIZ çalıştırır.

.pyw uzantısı sayesinde çift tıklayınca konsol penceresi açılmaz, sadece
saat yanında bir tepsi ikonu çıkar. Sağ tık menüsü: Başlat / Durdur /
Paneli aç / Çıkış. Açılışta sunucu otomatik başlar.

Otomatik başlatma: bu dosyaya (veya kısayoluna) Win+R -> shell:startup ile
Başlangıç klasöründen kısayol bırak.
"""
import subprocess
import sys
import webbrowser
from pathlib import Path

import pystray
from PIL import Image, ImageEnhance

BASE = Path(__file__).resolve().parent.parent
BACKEND = BASE / "backend"
ICON_FILE = BASE / "frontend" / "icon-512.png"
LOG_FILE = BASE / "deploy" / "dock.log"
PANEL_URL = "https://localhost:8000"

CREATE_NO_WINDOW = 0x08000000   # alt process'in konsol penceresi açmasını engelle

_proc = None
_icon = None       # tepsi ikonu referansı (durum güncellemek için)
_img_on = None     # çalışıyor görseli (turuncu)
_img_off = None    # durdu görseli (gri + soluk)


def _running() -> bool:
    return _proc is not None and _proc.poll() is None


def _refresh():
    """Tepsi ikonunu, ipucunu ve menüyü mevcut duruma göre güncelle."""
    if _icon is None:
        return
    _icon.icon = _img_on if _running() else _img_off
    _icon.title = "Tablet Dock — Çalışıyor" if _running() else "Tablet Dock — Durdu"
    _icon.update_menu()


def start(icon=None, item=None):
    global _proc
    if _running():
        return
    # ÖNEMLİ: çıktıyı log dosyasına yönlendir. pythonw'da stdout=None olduğu
    # için uvicorn aksi halde açılışta loglarken çöker.
    logf = open(LOG_FILE, "a", encoding="utf-8")
    _proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", "0.0.0.0", "--port", "8000",
         "--ssl-keyfile", "certs/key.pem", "--ssl-certfile", "certs/cert.pem"],
        cwd=str(BACKEND),
        creationflags=CREATE_NO_WINDOW,
        stdout=logf,
        stderr=logf,
    )
    _refresh()


def stop(icon=None, item=None):
    global _proc
    if _running():
        _proc.terminate()
        try:
            _proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _proc.kill()
    _proc = None
    _refresh()


def open_panel(icon=None, item=None):
    webbrowser.open(PANEL_URL)


def quit_app(icon, item):
    stop()
    icon.stop()


def _status(item):
    return "● Çalışıyor" if _running() else "○ Durdu"


def _build_images():
    """Çalışıyor (turuncu) ve durdu (gri + soluk) ikon görsellerini hazırla."""
    base = Image.open(ICON_FILE).convert("RGBA")
    r, g, b, a = base.split()
    rgb = Image.merge("RGB", (r, g, b))
    gray = ImageEnhance.Color(rgb).enhance(0.0)          # renksiz (gri)
    dim = ImageEnhance.Brightness(gray).enhance(0.5)     # soluk
    dr, dg, db = dim.split()
    off = Image.merge("RGBA", (dr, dg, db, a))           # alpha (şeffaflık) korunur
    return base, off


def main():
    global _icon, _img_on, _img_off
    _img_on, _img_off = _build_images()
    menu = pystray.Menu(
        pystray.MenuItem(_status, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Başlat", start, enabled=lambda i: not _running()),
        pystray.MenuItem("Durdur", stop, enabled=lambda i: _running()),
        pystray.MenuItem("Paneli aç", open_panel),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Çıkış", quit_app),
    )
    _icon = pystray.Icon("dock", _img_on, "Tablet Dock", menu)
    start()            # açılışta sunucuyu başlat
    _icon.run()        # tepsi döngüsü (bloklar)


if __name__ == "__main__":
    main()
