"""Ses → yazı (faster-whisper, yerel, GPU).

Model tembel yüklenir (ilk istekte) ve bellekte kalır. GPU yoksa CPU'ya
düşer. Tablet ses kaydını (webm/opus veya wav) ham bayt olarak gönderir;
PyAV/ffmpeg çözer.
"""
import io

_model = None

# Whisper'ın sessizlik/gürültüde uydurduğu bilinen kalıplar (TR YouTube kaynaklı).
_HALLUCINATIONS = {
    "izlediğiniz için teşekkür ederim",
    "abone olmayı unutmayın",
    "altyazı m.k.",
    "teşekkürler",
    "teşekkür ederim",
}


def _get_model():
    # faster_whisper ağır; açılışı yavaşlatmamak için tembel import.
    from faster_whisper import WhisperModel

    global _model
    if _model is None:
        try:
            _model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
        except Exception:
            # GPU/cuDNN yoksa CPU'ya düş (yavaş ama çalışır).
            _model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    return _model


def transcribe(audio_bytes: bytes) -> str:
    """Ham ses baytlarını Türkçe metne çevir.

    VAD (ses aktivite algılama) sessizliği eler -> Whisper'ın sessizlikte
    uydurma yapması engellenir. Bilinen uydurma kalıpları da filtrelenir.
    """
    segments, _info = _get_model().transcribe(
        io.BytesIO(audio_bytes),
        language="tr",
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False,
    )
    text = " ".join(seg.text for seg in segments).strip()

    # Tanı logu (tray'de dock.log'a, run.bat'te konsola düşer).
    print(f"[stt] ses={len(audio_bytes)}B  ham_metin={text!r}", flush=True)

    norm = text.lower().strip(" .,!?")
    if norm in _HALLUCINATIONS or "izlediğiniz için teşekkür" in norm:
        return ""
    return text
