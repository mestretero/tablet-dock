"""Program başlatıcı + toggle (tekrar basınca kapat).

Güvenlik: SADECE apps.json'daki tanımlı programlar açılır/kapanır.
Kapatma NAZİKTİR: görünür pencereye WM_CLOSE gönderir (X'e basmak gibi),
böylece Word/Excel kaydedilmemiş dosyayı sorabilir. Penceresi yoksa
son çare terminate edilir.
"""
import ctypes
import os
import subprocess
from ctypes import wintypes

import psutil

from config import load_apps


def _proc_name(app: dict):
    """Uygulamanın süreç adı (algılama/kapatma için). 'process' alanı varsa o;
    yoksa .exe path'inin dosya adı. Klasör/.lnk için None döner (toggle yok)."""
    if app.get("process"):
        return app["process"]
    path = app["path"]
    if path.lower().endswith(".exe"):
        return os.path.basename(path)
    return None


def running_ids() -> list[str]:
    """Şu an çalışan tanımlı uygulamaların id listesi (tile'ları yakmak için)."""
    names = set()
    for p in psutil.process_iter(["name"]):
        n = p.info.get("name")
        if n:
            names.add(n.lower())
    ids = []
    for app in load_apps():
        pn = _proc_name(app)
        if pn and pn.lower() in names:
            ids.append(app["id"])
    return ids


def _pids_for(name: str) -> list[int]:
    name = name.lower()
    return [p.pid for p in psutil.process_iter(["name"])
            if p.info.get("name") and p.info["name"].lower() == name]


def _graceful_close(pids: list[int]) -> bool:
    """Süreçlerin görünür pencerelerine WM_CLOSE gönder. En az birine
    gönderildiyse True. (Gönderilemezse çağıran terminate'e düşer.)"""
    WM_CLOSE = 0x0010
    user32 = ctypes.windll.user32
    pidset = set(pids)
    posted = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _lparam):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pidset and user32.IsWindowVisible(hwnd):
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            posted.append(pid.value)
        return True

    user32.EnumWindows(cb, 0)
    return bool(posted)


def _close(name: str) -> bool:
    """Adı verilen programı kapat. Çalışmıyorsa False."""
    pids = _pids_for(name)
    if not pids:
        return False
    if not _graceful_close(pids):
        for pid in pids:                       # görünür penceresi yok -> zorla
            try:
                psutil.Process(pid).terminate()
            except psutil.Error:
                pass
    return True


def launch(app_id: str) -> dict:
    """Toggle: kapalıysa başlat, açıksa kapat. Klasörler hep açılır."""
    apps = {a["id"]: a for a in load_apps()}
    app = apps.get(app_id)
    if app is None:
        raise KeyError(app_id)

    path = app["path"]
    name = _proc_name(app)

    # exe (klasör değil) ve çalışıyorsa -> kapat
    if name and not os.path.isdir(path) and _close(name):
        return {"action": "closed", "name": app["name"]}

    args = app.get("args", [])
    if args:
        subprocess.Popen([path, *args], close_fds=True)
    else:
        os.startfile(path)  # type: ignore[attr-defined]  (Windows'a özel)
    return {"action": "launched", "name": app["name"]}
