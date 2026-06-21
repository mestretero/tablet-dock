# 🖥️ Tablet Dock

> Got an old tablet lying in a drawer? Turn it into a **smart wall panel that controls your PC** — open programs, launch games, control music & volume, see your clipboard, and talk to a voice assistant. You just touch the tablet; your PC does the work. **No cloud, no accounts, no API keys.**

**🌐 [English](README.md) · [Türkçe](README.tr.md)**

---

## 📺 Demo

_Add your video link here._

## 🤔 What is this, in plain words?

The tablet on the wall only shows a **web page**. Your **PC** runs a tiny program (the “agent”) that does everything: opens your apps, launches your Steam/Epic games, changes the volume, reads your clipboard, and answers your voice. They talk to each other over your home **Wi‑Fi**. That's it.

This is great for **old/weak tablets** because the tablet does almost nothing — the PC does the heavy lifting.

## ✨ What it can do

- 🚀 **Apps** — tap to open a program (with its real icon). Tap again to close it. Open apps glow.
- 🎮 **Games** — finds your **Steam & Epic** games automatically and shows their cover art. Tap to play. Updates itself when you install/uninstall games.
- 📁 **Projects** — shows the folders inside your project folders; tap to open one in Explorer. Newest on top.
- 🎵 **Media & sound** — play/pause/next, volume, the song that's playing, and a button to switch your speaker/headphones.
- 📋 **Clipboard** — your last few copied texts; tap one to copy it back to the PC. (Passwords from password managers are skipped.)
- 🎙️ **Voice assistant** — tap and talk. *“Ask”* gives a fast answer from a local AI on your PC. *“Search the web”* uses Claude with live internet. It speaks the answer out loud. You can also say commands like “open OBS” or “turn the volume down”.
- 🎨 Clean **Apple‑style dark design** with a floating bottom menu; installs on the tablet like a real app (fullscreen).

---

## 🧰 Before you start

You need:

1. A **Windows PC** (Windows 10 or 11).
2. An old **Android tablet** (or a phone) with **Chrome**.
3. Both connected to the **same Wi‑Fi**.
4. About **20 minutes**.

You do **not** need: any paid service, an API key, or coding knowledge. Just follow the steps. 🙂

---

## 🖥️ Part A — Set up the PC

### Step 1 — Install Python (one time)

Python is the language this runs on.

1. Go to **<https://www.python.org/downloads/>** and click the big **Download** button.
2. Run the file. On the first screen, **tick the box “Add Python to PATH”** ✅ (very important), then click **Install Now**.

### Step 2 — Download this project

- **Easy way:** click the green **`<> Code`** button at the top of this page → **Download ZIP** → unzip it somewhere easy, like your Desktop.
- **Or with git:** `git clone https://github.com/mestretero/tablet-dock.git`

### Step 3 — Install the helper libraries

1. Open the project folder, then go **into the `backend` folder**.
2. Click the **address bar** of that File Explorer window, type **`cmd`** and press **Enter**. A black terminal window opens (already inside the `backend` folder).
3. Type this and press Enter:
   ```
   pip install -r requirements.txt
   ```
   Wait until it finishes. (This downloads the parts the program needs.)

### Step 4 — Choose which programs to show

1. In the `backend` folder, **copy** `apps.example.json` and **rename the copy to `apps.json`**.
2. Open `apps.json` with **Notepad** and edit it. For each program you want, set its **name** and the **path** to its `.exe`.
   - 💡 **How to find a path:** right‑click the program's shortcut → **Properties** → copy the **Target** line.
   - You can add programs, folders, even your Projects folder. See [Customizing](#️-make-it-yours) below.

### Step 5 — Create the security certificate

The tablet's microphone only works over a secure (`https`) connection. This step makes that possible.

In the same terminal, type:
```
python ..\deploy\generate_cert.py
```

### Step 6 — Start it!

1. Go to the **`deploy`** folder and **double‑click `start-dock.vbs`**.
2. A small icon appears near the clock (bottom‑right of your screen — you may need to click the little **^** arrow to see it). That means it's **running**. Right‑click that icon for **Start / Stop / Open / Quit**.
3. The first time, Windows may ask about the **firewall** → click **Allow** (keep “Private networks” ticked).

### Step 7 — Find your PC's address

1. In the terminal, type **`ipconfig`** and press Enter.
2. Find the line **“IPv4 Address”** — it looks like `192.168.1.42`. **Write it down** — this is your PC's address. (Yours will be different.)

> 💡 Tip: give your PC a fixed IP in your router (a “DHCP reservation”) so the address never changes.

---

## 📱 Part B — Set up the tablet

### Step 1 — Trust the certificate (for the microphone)

1. On the tablet, open **Chrome** and go to:
   `https://YOUR-PC-IP:8000/cert.crt`  (replace `YOUR-PC-IP` with the address from above)
2. It downloads a small file. Now install it:
   **Settings → Security → Encryption & credentials → Install a certificate → CA certificate → pick the downloaded file.**
   (If Android asks you to set a screen lock/PIN first, do it.)

### Step 2 — Install the panel as an app

1. In Chrome, go to **`https://YOUR-PC-IP:8000`**.
2. Open the Chrome menu (**⋮**) → **Install app** (or “Add to Home screen”).
3. Open the new icon from your home screen — it opens **fullscreen**, like a real app.

### Step 3 — Mount it

Put the tablet on the wall (a charging mount is ideal so it stays on). Done! 🎉

> ℹ️ Fully Kiosk Browser also works, but its **free** version blocks the microphone. **Chrome is recommended** if you want the voice assistant.

---

## 🎙️ Voice assistant (optional)

The voice features run mostly **on your PC**. To enable them:

1. **Install [Ollama](https://ollama.com)** (a tool to run AI models locally), then download a small model:
   ```
   ollama pull gemma4:e2b-it-qat
   ```
   (This powers the fast offline answers. You can change the model name in `backend/services/llm.py`.)
2. For the **“Search the web”** button, install the **`claude` CLI** ([Claude Code](https://claude.com/claude-code)) and sign in. It uses your Claude subscription — **no API key needed**.
3. Speech‑to‑text (`faster-whisper`) is already installed in Step 3; it downloads its model the first time you talk.

Then on the tablet, the **Assistant** tab works: tap **Ask** (local & fast) or **Search the web** (Claude), talk, and it answers out loud.

---

## ⚙️ Make it yours

Edit **`backend/apps.json`** any time (it's re‑read automatically — no restart):

```jsonc
{
  "id": "spotify",                   // any unique name
  "name": "Spotify",                 // shown under the icon
  "icon": "S",                       // a letter, used only if no real icon is found
  "path": "C:\\...\\Spotify.exe",    // an .exe, a .lnk shortcut, a folder, or a website
  "args": ["--flag"],                // optional: extra launch options
  "process": "Spotify.exe",          // optional: lets “tap again to close” + the glow work
  "icon_from": "C:\\...\\app.exe",   // optional: which .exe to take the icon from (useful for .lnk)
  "project_root": true               // optional: list this folder's subfolders in the Projects tab
}
```

- Real icons are pulled from the program automatically. Folders show the letter.
- Add `"project_root": true` to a **folder** to make its subfolders appear in the **Projects** tab.

## 🔁 Auto‑start on boot (optional)

So it starts by itself when the PC turns on:

1. Press **Win + R**, type **`shell:startup`**, press Enter.
2. Right‑drag `deploy/start-dock.vbs` into that folder → **Create shortcut here**.

## 🔒 Privacy & safety

- The agent only opens the programs in **your `apps.json`** — nothing else can be run remotely.
- Clipboard history lives only in memory (gone when you restart) and **skips passwords** marked private by password managers.
- No cloud, no tracking, no API keys. Your certificate, `apps.json`, icons and logs are **never uploaded** (git‑ignored).
- Keep it on your **home Wi‑Fi**; don't open it to the internet.

## 🆘 Troubleshooting

- **Tablet says “can't connect”** → Is the agent running (tray icon)? Did you Allow the firewall? Are both on the same Wi‑Fi? Is the IP correct?
- **No microphone / “mic not available”** → Did you install the certificate (Part B, Step 1) and open the site with **https**? Are you using **Chrome** (not free Fully Kiosk)?
- **Old icon after I changed it** → fully **remove** the home‑screen app and **reinstall** it (Chrome caches icons).
- **See server logs** → run `deploy/run.bat` instead of the tray launcher; it opens a console with messages.

## 📄 License

[MIT](LICENSE) — free to use, change, and share.
