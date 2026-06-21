"""Uygulama-bazlı ses mikseri (per-app volume).

Windows'ta her ses oturumu (Spotify, Discord, oyun, tarayıcı...) ayrı
kontrol edilebilir: pycaw'ın ISimpleAudioVolume arayüzü. Oturumlar
DİNAMİKTİR - uygulama ses çalınca gelir, kapanınca gider; bu yüzden
liste canlıdır. Aynı isimli süreçler (ör. birden çok tarayıcı penceresi)
tek kaydırakta gruplanır ve ayar gruptaki tüm oturumlara uygulanır.
Sistem sesleri (süreçsiz oturumlar) listede gösterilmez.
"""
import comtypes
from pycaw.pycaw import AudioUtilities

# Süreç adından şık etiket (DisplayName boşsa/teknikse buradan üretilir).
_KNOWN = {
    "opera": "Opera", "chrome": "Chrome", "msedge": "Edge", "firefox": "Firefox",
    "brave": "Brave", "spotify": "Spotify", "discord": "Discord", "steam": "Steam",
    "vlc": "VLC", "obs64": "OBS", "obs": "OBS", "telegram": "Telegram",
    "wmplayer": "Media Player", "music.ui": "Groove",
}

# Windows AudioSessionState: 0=Inactive, 1=Active, 2=Expired (kapanmış).
_EXPIRED = 2


def _sessions():
    comtypes.CoInitialize()
    return AudioUtilities.GetAllSessions()


def _key(session):
    """Gruplama anahtarı = süreç adı (küçük harf). Süreçsiz (sistem) -> None."""
    p = session.Process
    return p.name().lower() if p else None


def _label(session) -> str:
    """İnsana uygun ad: temiz DisplayName varsa o, yoksa süreç adından üret."""
    disp = (session.DisplayName or "").strip()
    if disp and not disp.startswith("@"):   # '@...' = teknik kaynak dizesi
        return disp
    name = session.Process.name()
    base = name[:-4] if name.lower().endswith(".exe") else name
    return _KNOWN.get(base.lower(), base.capitalize())


def list_sessions() -> list[dict]:
    """Ses üreten uygulamalar: her biri için key + ad + seviye(0-100) + sustur.
    Süreç adına göre gruplanır; süreçsiz (sistem) oturumlar atlanır."""
    groups: dict[str, dict] = {}
    for s in _sessions():
        if s.State == _EXPIRED:
            continue
        key = _key(s)
        if key is None:
            continue
        vol = s.SimpleAudioVolume
        level = round(vol.GetMasterVolume() * 100)
        muted = bool(vol.GetMute())
        g = groups.get(key)
        if g is None:
            groups[key] = {"key": key, "label": _label(s),
                           "level": level, "muted": muted}
        else:
            g["level"] = max(g["level"], level)   # grubun en yükseğini göster
            g["muted"] = g["muted"] and muted      # hepsi suskunsa suskun say
    return sorted(groups.values(), key=lambda x: x["label"].lower())


def set_session(key: str, level=None, muted=None) -> bool:
    """Anahtara (süreç adı) uyan TÜM oturumlara ses/sustur ayarını uygula.
    En az bir oturum eşleşirse True."""
    key = (key or "").lower()
    hit = False
    for s in _sessions():
        if _key(s) != key:
            continue
        vol = s.SimpleAudioVolume
        if level is not None:
            vol.SetMasterVolume(max(0, min(100, int(level))) / 100, None)
        if muted is not None:
            vol.SetMute(1 if muted else 0, None)
        hit = True
    return hit
