"""Asistan - Claude CLI (Haiku 4.5, web aramalı).

Sorular/araştırma buraya gelir. Claude kendi web aramasını kullanabilir
(güncel bilgi). Cevap sesli okunacağı için: kısa + markdown/kaynak/URL yok.
API key gerekmez; PC'deki 'claude' CLI kullanıcının aboneliğiyle çalışır.

NOT: Claude'u açık tutmayı (stream-json kalıcı worker) denedik; ölçümde
kazanç ~0.4 sn çıktı (yavaşlık açılış değil, her soruda yapılan ajan
işlemiymiş). Karmaşıklığa değmedi, sade tek-seferlik kullanıyoruz.
"""
import re
import shutil
import subprocess

_CLAUDE_BIN = shutil.which("claude") or shutil.which("claude.cmd")
_MODEL = "claude-haiku-4-5"
_CREATE_NO_WINDOW = 0x08000000


def _hidden():
    """Windows'ta komut penceresi açılmasını engelleyen subprocess ayarları.
    'claude' bir .cmd sarmalayıcı olduğu için CREATE_NO_WINDOW tek başına bazen
    yetmiyor; STARTUPINFO + SW_HIDE ile kesin gizliyoruz."""
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    return {"startupinfo": si, "creationflags": _CREATE_NO_WINDOW}

_SYSTEM = (
    "ROL: Bu oturumda kodlama asistanı DEĞİLSİN. GENEL bir sesli ev asistanısın; "
    "cevabın yüksek sesle okunacak. Her tür soruyu cevapla: genel "
    "kültür, tavsiye, sohbet, yemek, hava, fiyat, haber. ASLA 'ben kod/yazılım "
    "asistanıyım' deme, ASLA genel bir soruyu reddetme.\n"
    "GÜNCELLİK: Tarih, saat, fiyat, döviz kuru, hava, haber, spor skoru gibi "
    "DEĞİŞEBİLEN ya da 2025 sonrasına dair HER soruda MUTLAKA webde ara; sonuçtaki "
    "ASIL CEVABI (sayı/değer) söyle, sadece link verme. Hafızandan tahmin etme.\n"
    "BİÇİM: Cevap en fazla 1-2 cümle, sade konuşma Türkçesi. Markdown, madde işareti, "
    "başlık, emoji, URL veya kaynak listesi KULLANMA."
)


def available() -> bool:
    return _CLAUDE_BIN is not None


def _clean(text: str) -> str:
    """TTS için temizle: kaynak bloğu, markdown link, yıldız vs. at."""
    text = (text or "").strip()
    text = re.split(r"\n\s*(?:sources?|kaynak(?:lar)?)\s*:", text, flags=re.I)[0]
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)   # [etiket](url) -> etiket
    text = re.sub(r"https?://\S+", "", text)               # çıplak url
    text = text.replace("**", "").replace("*", "").replace("#", "")
    return text.strip()


def ask(prompt: str) -> str:
    if not _CLAUDE_BIN:
        return "Claude bu bilgisayarda bulunamadı."
    prompt = prompt.strip()
    if not prompt:
        return ""

    try:
        result = subprocess.run(
            [_CLAUDE_BIN, "-p", prompt, "--model", _MODEL,
             "--allowedTools", "WebSearch",
             "--append-system-prompt", _SYSTEM],   # bayrak = gömmekten daha güçlü
            capture_output=True,
            text=True,
            timeout=90,
            encoding="utf-8",
            **_hidden(),
        )
    except subprocess.TimeoutExpired:
        return "Cevap çok uzun sürdü."

    return _clean(result.stdout) or "Cevap alamadım."
