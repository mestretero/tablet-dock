"""Beyin: metni (sesli komut ya da yazı) sınıflandırır ve uygular.

Akış:
  metin → Gemma sınıflandırır (komut mu, soru mu?)
    ├─ komut → ajan uygular (program/medya/ses), kısa onay döner
    └─ soru  → Gemma kısa cevap; "claude" denirse Claude CLI yedeği

Dönüş: {"transcript": str, "reply": str, "action": str|None}
  reply = tablette sesli okunacak / gösterilecek metin.
"""
import json

from config import load_apps
from services import assistant, launcher, llm, system


def route(text: str, web: bool = False) -> dict:
    text = (text or "").strip()
    if not text:
        return {"transcript": text, "reply": "Seni net duyamadım, tekrar söyle.", "action": None}

    try:
        intent = _classify(text)
    except Exception:
        intent = {"tip": "soru"}  # sınıflandırma çökerse soru say

    if intent.get("tip") == "komut":
        return _do_command(intent, text)

    # Soru: web=True -> Claude (internet), değilse -> Gemma (yerel, hızlı).
    if web:
        return {"transcript": text, "reply": assistant.ask(text), "action": "soru-web"}
    return {"transcript": text, "reply": _gemma_answer(text), "action": "soru"}


# --- Sınıflandırma (Gemma, JSON) --------------------------------------------
def _classify(text: str) -> dict:
    apps = load_apps()
    app_list = ", ".join(f'{a["id"]} ({a["name"]})' for a in apps) or "(yok)"
    prompt = (
        f'Kullanıcının söylediği: "{text}"\n'
        "Bunu sınıflandır ve SADECE JSON döndür.\n"
        f"Açılabilir programlar: {app_list}\n"
        "Olası JSON cevaplar:\n"
        '- Program aç: {"tip":"komut","eylem":"baslat","hedef":"<program id>"}\n'
        '- Medya:      {"tip":"komut","eylem":"medya","hedef":"playpause|next|prev"}\n'
        '- Ses:        {"tip":"komut","eylem":"ses","hedef":"ac|kis|sustur|<0-100>"}\n'
        '- Soru/sohbet:{"tip":"soru"}\n'
        "Program açma isteği yoksa ve bir kontrol komutu değilse 'soru' döndür."
    )
    return json.loads(llm.gemma(prompt, json_mode=True))


# --- Komut uygulama ---------------------------------------------------------
def _do_command(intent: dict, text: str) -> dict:
    eylem = intent.get("eylem")
    hedef = str(intent.get("hedef", "")).strip()

    try:
        if eylem == "baslat":
            r = launcher.launch(hedef)
            return _ok(text, f"{r['name']} açılıyor.", f"baslat:{hedef}")
        if eylem == "medya":
            system.media_key(hedef)
            ad = {"playpause": "Oynat/duraklat", "next": "Sonraki şarkı",
                  "prev": "Önceki şarkı"}.get(hedef, hedef)
            return _ok(text, ad + ".", f"medya:{hedef}")
        if eylem == "ses":
            return _do_volume(hedef, text)
    except KeyError:
        return {"transcript": text, "reply": "O programı bulamadım.", "action": None}
    except Exception:
        return {"transcript": text, "reply": "Komutu uygulayamadım.", "action": None}

    return {"transcript": text, "reply": "Tam anlayamadım.", "action": None}


def _do_volume(hedef: str, text: str) -> dict:
    cur = system.get_volume()["level"]
    if hedef == "ac":
        yeni = min(100, cur + 15); system.set_volume(yeni); reply = f"Ses {yeni}."
    elif hedef == "kis":
        yeni = max(0, cur - 15); system.set_volume(yeni); reply = f"Ses {yeni}."
    elif hedef == "sustur":
        system.set_mute(True); reply = "Sustruldu."
    elif hedef.isdigit():
        system.set_volume(int(hedef)); reply = f"Ses {int(hedef)}."
    else:
        return {"transcript": text, "reply": "Ses komutunu anlamadım.", "action": None}
    return _ok(text, reply, f"ses:{hedef}")


# --- Soru cevaplama ---------------------------------------------------------
def _gemma_answer(text: str) -> str:
    """Yerel, hızlı cevap (Gemma). İnternet gerektirmeyen genel sorular için."""
    try:
        return llm.gemma(
            "Soruyu kısa, net, sade Türkçeyle cevapla (en fazla 2 cümle). "
            "Emin değilsen kısaca belirt. Soru: " + text
        )
    except Exception:
        return "Şu an cevap veremedim."


def _ok(text: str, reply: str, action: str) -> dict:
    return {"transcript": text, "reply": reply, "action": action}
