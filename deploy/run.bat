@echo off
REM Tablet dock ajanini HTTPS ile baslatir (mikrofon icin sart).
REM PC acilisina eklemek icin: Win+R -> shell:startup -> bu .bat'a kisayol birak.
cd /d "%~dp0\..\backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 ^
  --ssl-keyfile certs\key.pem --ssl-certfile certs\cert.pem
