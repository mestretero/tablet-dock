"""Yerel LLM - Gemma (ollama üzerinden). Beyin bunu komut ayrıştırma ve
kısa cevaplar için kullanır. Claude CLI yedeği services/assistant.py'de."""
import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:e2b-it-qat"


def gemma(prompt: str, json_mode: bool = False) -> str:
    """Gemma'ya tek seferlik istek. json_mode=True ise geçerli JSON zorlar."""
    body = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0},
    }
    if json_mode:
        body["format"] = "json"

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read())["response"].strip()
