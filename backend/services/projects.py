"""Proje gezgini: 'project_root' işaretli klasörlerin içindeki proje
klasörlerini canlı listeler. Her istekte taze taranır -> yeni klasör
otomatik gelir, silinen gider. Açma SADECE kök altındaki klasörlerle
sınırlıdır (ağdan rastgele yol açılamaz)."""
import os

from config import load_apps


def _roots() -> list[dict]:
    return [a for a in load_apps() if a.get("project_root")]


def list_projects() -> list[dict]:
    """Köke göre gruplu proje klasörleri; her grup en son değişen üstte."""
    groups = []
    for root in _roots():
        base = root["path"]
        items = []
        try:
            with os.scandir(base) as it:
                for entry in it:
                    if not entry.is_dir():
                        continue
                    try:
                        mtime = entry.stat().st_mtime
                    except OSError:
                        mtime = 0
                    items.append((entry.name, entry.path, mtime))
        except OSError:
            pass  # kök erişilemiyor / yok
        items.sort(key=lambda x: x[2], reverse=True)   # en son değişen üstte
        groups.append({
            "root_id": root["id"],
            "root_name": root["name"],
            "folders": [{"name": n, "path": p} for (n, p, _m) in items],
        })
    return groups


def open_folder(path: str) -> bool:
    """Verilen klasörü Explorer'da aç. Yalnızca bir proje kökünün ALTINDAysa
    ve gerçekten klasörse açar; aksi halde False (güvenlik)."""
    real = os.path.realpath(path)
    target = os.path.normcase(real)
    for root in _roots():
        base = os.path.normcase(os.path.realpath(root["path"]))
        try:
            inside = os.path.commonpath([target, base]) == base
        except ValueError:
            continue  # farklı sürücü
        if inside and os.path.isdir(real):
            os.startfile(real)  # type: ignore[attr-defined]  (Windows'a özel)
            return True
    return False
