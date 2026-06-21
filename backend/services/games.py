"""Yüklü oyunları keşfeder (Steam + Epic), kapak resimleriyle listeler,
steam:// / com.epicgames.launcher:// ile tek tıkla başlatır.

Steam: libraryfolders.vdf -> appmanifest_*.acf (appid+name); kapak
appcache/librarycache/<appid>/library_600x900.jpg. Epic: ProgramData
manifests *.item (JSON); ikon exe'den çıkarılır.
"""
import glob
import json
import os
import re
import urllib.request

from services import appicons

STEAM = r"C:\Program Files (x86)\Steam"
EPIC_MANIFESTS = r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests"
_CDN = "https://cdn.cloudflare.steamstatic.com/steam/apps"
# Oyun olmayan Steam girdileri (redistributable / runtime).
_SKIP = ("steamworks common redistributables", "steam linux runtime", "proton", "steamvr")


# --- Steam ------------------------------------------------------------------
def _steam_libs() -> list[str]:
    lf = os.path.join(STEAM, "steamapps", "libraryfolders.vdf")
    if not os.path.exists(lf):
        return []
    txt = open(lf, encoding="utf-8", errors="ignore").read()
    return [p.replace("\\\\", "\\") for p in re.findall(r'"path"\s+"([^"]+)"', txt)]


def _local(appid: str, fname: str):
    p = os.path.join(STEAM, "appcache", "librarycache", appid, fname)
    return p if os.path.exists(p) else None


def _cdn_cover(appid: str):
    """Steam CDN'den dikey kapağı indir + önbelleğe al (yerelde yoksa)."""
    out = appicons.CACHE_DIR / ("game-" + appid + ".jpg")
    if out.exists():
        return out
    for _ in range(2):   # geçici ağ hatalarına karşı 2 deneme
        try:
            req = urllib.request.Request(f"{_CDN}/{appid}/library_600x900.jpg",
                                         headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=12).read()
            appicons.CACHE_DIR.mkdir(exist_ok=True)
            out.write_bytes(data)
            return out
        except Exception:
            continue
    return None


def _steam_cover(appid: str):
    """Önce YEREL (Steam'in kullanıcıya gösterdiği = doğru), CDN son çare
    (yerelde hiçbir görsel yoksa; ör. Don't Starve). CDN bazı appid'lerde
    alakasız görsel verebildiği için yerel önceliklidir."""
    return (_local(appid, "library_600x900.jpg")
            or _local(appid, "header.jpg")
            or _local(appid, "logo.png")
            or _cdn_cover(appid))


def _steam_games() -> list[dict]:
    out, seen = [], set()
    for lib in _steam_libs():
        for acf in glob.glob(os.path.join(lib, "steamapps", "appmanifest_*.acf")):
            t = open(acf, encoding="utf-8", errors="ignore").read()
            i = re.search(r'"appid"\s+"(\d+)"', t)
            n = re.search(r'"name"\s+"([^"]+)"', t)
            if not (i and n):
                continue
            appid, name = i.group(1), n.group(1)
            if appid in seen or any(s in name.lower() for s in _SKIP):
                continue
            seen.add(appid)
            # fit: dikey/yatay kapak -> cover (doldur); sadece logo -> contain (tam göster).
            has_art = _local(appid, "library_600x900.jpg") or _local(appid, "header.jpg")
            fit = "cover" if has_art else ("contain" if _local(appid, "logo.png") else "cover")
            out.append({"id": "steam-" + appid, "name": name, "source": "Steam",
                        "has_cover": True, "fit": fit})
    return out


# --- Epic -------------------------------------------------------------------
def _epic_manifest(appname: str):
    for it in glob.glob(os.path.join(EPIC_MANIFESTS, "*.item")):
        try:
            d = json.load(open(it, encoding="utf-8"))
        except Exception:
            continue
        if d.get("AppName") == appname:
            return d
    return None


def _epic_games() -> list[dict]:
    out = []
    if not os.path.isdir(EPIC_MANIFESTS):
        return out
    for it in glob.glob(os.path.join(EPIC_MANIFESTS, "*.item")):
        try:
            d = json.load(open(it, encoding="utf-8"))
        except Exception:
            continue
        name, app = d.get("DisplayName"), d.get("AppName")
        if not (name and app):
            continue
        exe = os.path.join(d.get("InstallLocation", ""), d.get("LaunchExecutable", ""))
        out.append({"id": "epic-" + app, "name": name, "source": "Epic",
                    "has_cover": bool(exe and os.path.exists(exe)), "fit": "contain"})
    return out


# --- Genel ------------------------------------------------------------------
def list_games() -> list[dict]:
    games = _steam_games() + _epic_games()
    games.sort(key=lambda g: g["name"].lower())
    return games


def cover_path(game_id: str):
    """Oyunun kapak/ikon dosya yolu (Steam jpg ya da Epic exe ikonu PNG)."""
    if game_id.startswith("steam-"):
        return _steam_cover(game_id[len("steam-"):])
    if game_id.startswith("epic-"):
        d = _epic_manifest(game_id[len("epic-"):])
        if d:
            exe = os.path.join(d.get("InstallLocation", ""), d.get("LaunchExecutable", ""))
            return appicons.extract_exe_icon(exe, game_id)
    return None


def launch(game_id: str) -> bool:
    if game_id.startswith("steam-"):
        os.startfile("steam://rungameid/" + game_id[len("steam-"):])  # type: ignore[attr-defined]
        return True
    if game_id.startswith("epic-"):
        app = game_id[len("epic-"):]
        os.startfile(f"com.epicgames.launcher://apps/{app}?action=launch&silent=true")  # type: ignore[attr-defined]
        return True
    return False
