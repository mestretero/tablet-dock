"""PC sistem kontrolü: ses, medya tuşları, durum bilgisi, çalan şarkı.

Tüm fonksiyonlar Windows'a özeldir. Hatalar yutulmaz; üst katman
(main.py) anlamlı HTTP cevabına çevirir. Tek istisna: 'çalan şarkı'
opsiyoneldir, winsdk yoksa sessizce None döner.
"""
import asyncio
import ctypes

import psutil

# --- Medya tuşları (bağımlılık yok, ctypes ile sanal tuş) -------------------
# Windows sanal tuş kodları. Bu tuşlar sistem geneli çalışır: hangi oynatıcı
# (Spotify, YouTube, VLC) önde/aktifse onu kontrol eder.
_VK = {
    "next": 0xB0,        # VK_MEDIA_NEXT_TRACK
    "prev": 0xB1,        # VK_MEDIA_PREV_TRACK
    "stop": 0xB2,        # VK_MEDIA_STOP
    "playpause": 0xB3,   # VK_MEDIA_PLAY_PAUSE
}
_KEYEVENTF_KEYUP = 0x0002


async def _smtc_control(action: str) -> bool:
    """Çalan medya oturumunu doğrudan kontrol et (SMTC). Sentetik tuştan
    çok daha güvenilir - özellikle tarayıcı/YouTube/Spotify'da."""
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as SessionManager,
    )

    manager = await SessionManager.request_async()
    session = manager.get_current_session()
    if session is None:
        return False
    if action == "playpause":
        ok = await session.try_toggle_play_pause_async()
    elif action == "next":
        ok = await session.try_skip_next_async()
    elif action == "prev":
        ok = await session.try_skip_previous_async()
    elif action == "stop":
        ok = await session.try_stop_async()
    else:
        return False
    return bool(ok)  # False ise media_key sentetik tuşa düşer


def media_key(action: str) -> None:
    """Medya kontrolü. action: next|prev|stop|playpause.
    Önce SMTC (çalan oturumu doğrudan), olmazsa sentetik medya tuşu."""
    if action not in _VK:
        raise ValueError(f"bilinmeyen medya komutu: {action}")
    try:
        if asyncio.run(_smtc_control(action)):
            return
    except Exception:
        pass  # winsdk yok / oturum yok -> tuşa düş
    user32 = ctypes.windll.user32
    vk = _VK[action]
    user32.keybd_event(vk, 0, 0, 0)                 # bas
    user32.keybd_event(vk, 0, _KEYEVENTF_KEYUP, 0)  # bırak


# --- Ses seviyesi (pycaw / COM) ---------------------------------------------
def _volume_iface():
    """Aktif çıkış cihazının IAudioEndpointVolume arayüzünü döndür.

    comtypes COM gerektirir; FastAPI handler'ları worker thread'de
    çalıştığı için her çağrıda COM'u init ediyoruz (idempotent).
    pycaw'da AudioDevice.EndpointVolume zaten hazır arayüzü verir.
    """
    import comtypes
    from pycaw.pycaw import AudioUtilities

    comtypes.CoInitialize()
    return AudioUtilities.GetSpeakers().EndpointVolume


def get_volume() -> dict:
    """Mevcut ses seviyesi (0-100) ve sustur durumu."""
    vol = _volume_iface()
    level = round(vol.GetMasterVolumeLevelScalar() * 100)
    muted = bool(vol.GetMute())
    return {"level": level, "muted": muted}


def set_volume(level: int) -> dict:
    """Ses seviyesini mutlak değere ayarla (0-100)."""
    level = max(0, min(100, int(level)))
    vol = _volume_iface()
    vol.SetMasterVolumeLevelScalar(level / 100, None)
    return {"level": level, "muted": bool(vol.GetMute())}


def set_mute(muted: bool) -> dict:
    """Sesi sustur / aç."""
    vol = _volume_iface()
    vol.SetMute(1 if muted else 0, None)
    return {"level": round(vol.GetMasterVolumeLevelScalar() * 100), "muted": muted}


# --- Çalan şarkı (winsdk - opsiyonel) ---------------------------------------
async def _now_playing_async():
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as SessionManager,
    )
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    )

    manager = await SessionManager.request_async()
    session = manager.get_current_session()
    if session is None:
        return None
    info = await session.try_get_media_properties_async()
    title = (info.title or "").strip()
    if not title:
        return None
    playing = False
    try:
        playing = session.get_playback_info().playback_status == PlaybackStatus.PLAYING
    except Exception:
        pass
    return {"title": title, "artist": (info.artist or "").strip(), "playing": playing}


def now_playing():
    """Şu an çalan şarkı, ya da None.

    winsdk kurulu değilse veya hiçbir oynatıcı aktif değilse None döner;
    panelde 'çalan şarkı' kartı bu durumda gizlenir.
    """
    try:
        return asyncio.run(_now_playing_async())
    except Exception:
        return None


# --- Sistem durumu ----------------------------------------------------------
def stats() -> dict:
    """CPU %, RAM % ve çalan şarkıyı tek seferde döndür (tek poll)."""
    mem = psutil.virtual_memory()
    return {
        "cpu": round(psutil.cpu_percent(interval=None)),
        "ram": round(mem.percent),
        "ram_used_gb": round(mem.used / 1024**3, 1),
        "ram_total_gb": round(mem.total / 1024**3, 1),
        "now_playing": now_playing(),
    }
