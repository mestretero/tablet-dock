"""Ajan yapılandırması. Ev içi LAN kullanımı için sade tutuldu."""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
APPS_FILE = BASE_DIR / "apps.json"

# 0.0.0.0 = LAN'daki tabletin erişebilmesi için tüm arayüzleri dinle.
HOST = "0.0.0.0"
PORT = 8000

# HTTPS (mikrofon için şart). deploy/generate_cert.py ile üretilir.
CERT_FILE = BASE_DIR / "certs" / "cert.pem"
KEY_FILE = BASE_DIR / "certs" / "key.pem"


def load_apps() -> list[dict]:
    """apps.json'u oku. Panelde gösterilecek program listesi.

    Dosya her istekte okunur; böylece yeni program eklemek için
    ajanı yeniden başlatmaya gerek kalmaz - sadece apps.json'u kaydet.
    """
    if not APPS_FILE.exists():
        return []
    try:
        return json.loads(APPS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
