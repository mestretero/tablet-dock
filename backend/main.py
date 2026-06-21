"""Tablet dock ajanı - FastAPI.

Tek origin: hem paneli (frontend/) sunar hem /api/* uçlarını sağlar.
Tablet (Fully Kiosk) bu PC'nin LAN IP'sine bağlanır: http://<PC-IP>:8000
"""
from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from services import (appicons, assistant, audio, brain, clipboard, games,
                      launcher, projects, stt, system)

app = FastAPI(title="Tablet Dock Ajanı")


# --- İstek gövdeleri ---------------------------------------------------------
class LaunchBody(BaseModel):
    id: str


class MediaBody(BaseModel):
    action: str  # next | prev | stop | playpause


class VolumeBody(BaseModel):
    level: int | None = None   # 0-100 (mutlak)
    muted: bool | None = None  # sustur / aç


class ChatBody(BaseModel):
    message: str
    web: bool = False   # True -> Claude (internet), False -> Gemma (yerel)


class FolderBody(BaseModel):
    path: str


class AudioBody(BaseModel):
    key: str


class ClipBody(BaseModel):
    index: int


class GameBody(BaseModel):
    id: str


# --- Panel verisi ------------------------------------------------------------
@app.get("/api/apps")
def api_apps():
    """Panelde gösterilecek program listesi (path'ler dahil edilmez)."""
    return [
        {"id": a["id"], "name": a["name"], "icon": a.get("icon", a["name"][:1]),
         "img": appicons.icon_source(a) is not None}
        for a in config.load_apps()
    ]


@app.get("/api/app-icon/{app_id}")
def api_app_icon(app_id: str):
    """Uygulamanın gerçek ikonu (exe'den çıkarılıp önbelleğe alınır)."""
    apps = {a["id"]: a for a in config.load_apps()}
    app = apps.get(app_id)
    if app:
        path = appicons.ensure_icon(app)
        if path:
            return FileResponse(path, media_type="image/png")
    raise HTTPException(404, "ikon yok")


@app.get("/api/games")
def api_games():
    """Yüklü oyunlar (Steam + Epic), kapaklarıyla."""
    return games.list_games()


@app.get("/api/game-cover/{game_id}")
def api_game_cover(game_id: str):
    path = games.cover_path(game_id)
    if path:
        return FileResponse(path)   # jpg/png uzantıdan algılanır
    raise HTTPException(404, "kapak yok")


@app.post("/api/game-launch")
def api_game_launch(body: GameBody):
    if games.launch(body.id):
        return {"ok": True}
    raise HTTPException(404, "oyun başlatılamadı")


@app.get("/api/stats")
def api_stats():
    data = system.stats()
    data["running_apps"] = launcher.running_ids()   # yanan tile'lar için
    return data


@app.get("/api/projects")
def api_projects():
    """Proje köklerinin içindeki klasörler (canlı, en son değişen üstte)."""
    return projects.list_projects()


@app.get("/api/clipboard")
def api_clipboard():
    """Pano geçmişi (en yeni başta, parola-işaretli olanlar hariç)."""
    return clipboard.history()


@app.post("/api/clipboard")
def api_clipboard_copy(body: ClipBody):
    if clipboard.copy_item(body.index):
        return {"ok": True}
    raise HTTPException(404, "pano öğesi yok")


@app.post("/api/open-folder")
def api_open_folder(body: FolderBody):
    if projects.open_folder(body.path):
        return {"ok": True}
    raise HTTPException(403, "izin verilmeyen klasör")


@app.get("/api/health")
def api_health():
    return {"ok": True, "claude": assistant.available()}


@app.get("/cert.crt")
def api_cert():
    """Self-signed sertifikayı indirilebilir yapar (tablete CA olarak kurmak için).
    Sadece sertifika (public) sunulur; özel anahtar asla sunulmaz."""
    return FileResponse(
        config.CERT_FILE,
        media_type="application/x-x509-ca-cert",
        filename="dock-cert.crt",
    )


# --- PC kontrol --------------------------------------------------------------
@app.post("/api/launch")
def api_launch(body: LaunchBody):
    try:
        return launcher.launch(body.id)
    except KeyError:
        raise HTTPException(404, f"tanımsız program: {body.id}")
    except OSError as e:
        raise HTTPException(500, f"başlatılamadı: {e}")


@app.post("/api/media")
def api_media(body: MediaBody):
    try:
        system.media_key(body.action)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "action": body.action}


@app.get("/api/audio")
def api_audio():
    """2 hedef ses çıkışı + hangisi aktif."""
    return audio.list_outputs()


@app.post("/api/audio")
def api_audio_set(body: AudioBody):
    if audio.set_output(body.key):
        return {"ok": True}
    raise HTTPException(404, f"ses cihazı bulunamadı: {body.key}")


@app.post("/api/volume")
def api_volume(body: VolumeBody):
    if body.muted is not None:
        return system.set_mute(body.muted)
    if body.level is not None:
        return system.set_volume(body.level)
    return system.get_volume()


@app.post("/api/chat")
def api_chat(body: ChatBody):
    """Yazılı mesaj → beyin. web=False Gemma (yerel), web=True Claude (internet)."""
    return brain.route(body.message, web=body.web)


@app.post("/api/voice")
def api_voice(audio: bytes = Body(...), web: bool = False):
    """Ham ses → yazıya çevir → beyne ilet.

    web (query param): False -> Gemma (yerel, hızlı), True -> Claude (internet).
    Tablette 'Sor' butonu web=false, 'İnternette ara' butonu web=true gönderir.
    """
    text = stt.transcribe(audio)
    return brain.route(text, web=web)


# --- Statik panel (en sona; /api yollarını gölgelememesi için) --------------
app.mount("/", StaticFiles(directory=config.FRONTEND_DIR, html=True), name="panel")


if __name__ == "__main__":
    import uvicorn

    ssl = {}
    if config.CERT_FILE.exists() and config.KEY_FILE.exists():
        ssl = {"ssl_certfile": str(config.CERT_FILE), "ssl_keyfile": str(config.KEY_FILE)}
    uvicorn.run(app, host=config.HOST, port=config.PORT, **ssl)
