"""Pano geçmişi: PC panosunu izler, son kopyalananları tutar, dokununca
PC'ye geri kopyalar.

Gizlilik: Parola yöneticileri panoya "ExcludeClipboardContentFromMonitor-
Processing" işareti koyar; o işaretli kopyalar ATLANIR (duvarda parola
görünmesin). Geçmiş yalnızca bellekte (yeniden başlatınca silinir).
"""
import ctypes
import threading
import time

import pyperclip

_user32 = ctypes.windll.user32
# Parola yöneticilerinin "beni geçmişe alma" işareti.
_EXCLUDE_FMT = _user32.RegisterClipboardFormatW("ExcludeClipboardContentFromMonitorProcessing")

_MAX = 5         # tutulacak öğe sayısı (son 5; yeni gelince en eski düşer)
_MAXLEN = 5000   # öğe başına metin sınırı
_history: list[str] = []   # en yeni başta
_lock = threading.Lock()
_last = None


def _excluded() -> bool:
    """Pano içeriği parola yöneticisi tarafından 'gizli' işaretlenmiş mi."""
    return bool(_EXCLUDE_FMT) and bool(_user32.IsClipboardFormatAvailable(_EXCLUDE_FMT))


def _add(text: str):
    global _history
    with _lock:
        _history = [t for t in _history if t != text]   # aynısını çıkar (başa taşı)
        _history.insert(0, text)
        del _history[_MAX:]


def _monitor():
    global _last
    while True:
        try:
            if not _excluded():
                txt = pyperclip.paste()
                if txt and txt.strip() and txt != _last:
                    _last = txt
                    _add(txt[:_MAXLEN])
        except Exception:
            pass   # pano başkası tarafından açıksa bu turu atla
        time.sleep(1.5)


def _preview(text: str) -> str:
    one = " ".join(text.split())   # tek satıra indir
    return one[:80] + ("…" if len(one) > 80 else "")


def history() -> list[dict]:
    with _lock:
        return [{"index": i, "preview": _preview(t)} for i, t in enumerate(_history)]


def copy_item(index: int) -> bool:
    global _last
    with _lock:
        if not (0 <= index < len(_history)):
            return False
        txt = _history[index]
    pyperclip.copy(txt)
    _last = txt    # kendi yazdığımızı tekrar eklemeyelim
    _add(txt)      # kullanılanı başa taşı
    return True


def start():
    threading.Thread(target=_monitor, daemon=True).start()


# Dock başlarken pano izleyiciyi başlat.
start()
