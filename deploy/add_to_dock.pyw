"""Tek tıkla 'Dock'a Ekle' — apps.json'a program ekler (logo otomatik).

Üç kullanım:
  1) Argümansız     -> dosya seçtirir (tepsi menüsü 'Program Ekle…' bunu çağırır).
  2) <dosya yolu>   -> o dosyayı ekler (Explorer sağ-tık 'Gönder' bunu çağırır).
  3) --install-sendto  -> sağ-tık 'Gönder' kısayolunu kurar (tray açılışta çağırır).

.pyw olduğu için konsol penceresi açılmaz. apps.json her istekte okunduğundan
ekledikten sonra dock'u yeniden başlatmaya gerek yok; tablet kendiliğinden görür.
"""
import json
import os
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
APPS_FILE = BASE / "backend" / "apps.json"
EXAMPLE_FILE = BASE / "backend" / "apps.example.json"
SENDTO_NAME = "Tablet Dock'a Ekle.lnk"


# --- tkinter yardımcıları (pencereyi öne getir) -----------------------------
def _root():
    import tkinter as tk
    r = tk.Tk()
    r.withdraw()
    r.attributes("-topmost", True)
    return r


def _info(msg, title="Tablet Dock"):
    from tkinter import messagebox
    messagebox.showinfo(title, msg)


def _error(msg, title="Tablet Dock"):
    from tkinter import messagebox
    messagebox.showerror(title, msg)


# --- Program bilgisi çıkarma -------------------------------------------------
def _display_name(exe: str):
    """Exe'nin sürüm bilgisinden insana uygun adı al (ör. 'OBS Studio')."""
    try:
        import win32api
        tr = win32api.GetFileVersionInfo(exe, "\\VarFileInfo\\Translation")
        lang, cp = tr[0]
        for field in ("FileDescription", "ProductName"):
            key = "\\StringFileInfo\\%04X%04X\\%s" % (lang, cp, field)
            try:
                val = (win32api.GetFileVersionInfo(exe, key) or "").strip()
                if val:
                    return val
            except Exception:
                continue
    except Exception:
        pass
    return None


def _resolve_lnk(lnk: str):
    """.lnk kısayolunun hedef exe'sini döndür (yoksa '')."""
    try:
        import win32com.client
        sh = win32com.client.Dispatch("WScript.Shell")
        return (sh.CreateShortcut(lnk).TargetPath or "").strip()
    except Exception:
        return ""


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")
    return s or "program"


def _unique_id(base: str, existing: set) -> str:
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"


def _build_entry(path: str, existing_ids: set):
    """Seçilen yoldan apps.json kaydı üret (ad tahmini + ikon/süreç ayarları)."""
    ext = os.path.splitext(path)[1].lower()
    target = _resolve_lnk(path) if ext == ".lnk" else path  # ikon/süreç için gerçek exe
    guess = (_display_name(target) if target.lower().endswith(".exe") else None) \
        or os.path.splitext(os.path.basename(path))[0].replace("_", " ").replace("-", " ").title()

    entry = {
        "id": "",                       # ad onaylandıktan sonra doldurulur
        "name": guess,
        "icon": guess[:1].upper(),
        "path": path,
    }
    if target.lower().endswith(".exe"):
        entry["process"] = os.path.basename(target)        # 'tekrar dokun kapat' + yanma
        if ext == ".lnk":
            entry["icon_from"] = target                    # ikon hedeften çıksın
    return entry


# --- apps.json oku/yaz -------------------------------------------------------
def _load_apps():
    src = APPS_FILE if APPS_FILE.exists() else EXAMPLE_FILE
    if not src.exists():
        return []
    try:
        return json.loads(src.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_apps(apps):
    APPS_FILE.write_text(json.dumps(apps, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")


def _norm(p: str) -> str:
    return os.path.normcase(os.path.abspath(p))


# --- Sağ-tık 'Gönder' kısayolu kur ------------------------------------------
def install_sendto(silent=False):
    try:
        import win32com.client
        sh = win32com.client.Dispatch("WScript.Shell")
        sendto = Path(sh.SpecialFolders("SendTo"))
        link = sendto / SENDTO_NAME
        pyw = Path(sys.executable).with_name("pythonw.exe")  # konsolsuz yorumlayıcı
        sc = sh.CreateShortcut(str(link))
        sc.TargetPath = str(pyw) if pyw.exists() else sys.executable
        sc.Arguments = f'"{Path(__file__).resolve()}"'
        sc.WorkingDirectory = str(BASE / "deploy")
        sc.Description = "Seçili programı Tablet Dock'a ekle"
        sc.Save()
        if not silent:
            _info("Sağ-tık menüsü kuruldu.\n\nArtık bir exe/kısayola sağ tıkla →\n"
                  "Gönder → Tablet Dock'a Ekle.")
    except Exception as e:
        if not silent:
            _error(f"Sağ-tık kısayolu kurulamadı:\n{e}")


# --- Bir programı ekle -------------------------------------------------------
def add_path(path: str):
    if not path or not os.path.exists(path):
        _error("Dosya bulunamadı.")
        return
    apps = _load_apps()
    if any(_norm(a.get("path", "")) == _norm(path) for a in apps):
        _info("Bu program zaten ekli.")
        return

    existing_ids = {a.get("id") for a in apps}
    entry = _build_entry(path, existing_ids)

    # Adı kullanıcıya onaylat / düzelttir
    from tkinter import simpledialog
    name = simpledialog.askstring("Tablet Dock", "Program adı:",
                                  initialvalue=entry["name"])
    if not name:                       # iptal
        return
    name = name.strip()
    entry["name"] = name
    entry["icon"] = name[:1].upper()
    entry["id"] = _unique_id(_slug(name), existing_ids)

    apps.append(entry)
    try:
        _save_apps(apps)
    except OSError as e:
        _error(f"Kaydedilemedi:\n{e}")
        return
    _info(f"“{name}” eklendi ✓\n\nTablette Programlar bölümünde görünecek "
          "(birkaç saniye içinde).")


def pick_and_add():
    from tkinter import filedialog
    path = filedialog.askopenfilename(
        title="Dock'a eklenecek programı seç",
        filetypes=[("Program / kısayol", "*.exe;*.lnk"), ("Tüm dosyalar", "*.*")],
    )
    if path:
        add_path(path)


# --- Bir programı panelden kaldır -------------------------------------------
def remove_dialog():
    """Programları listele, seçileni apps.json'dan çıkar (programı SİLMEZ)."""
    apps = _load_apps()
    if not apps:
        _info("Listede program yok.")
        return

    import tkinter as tk
    from tkinter import messagebox

    state = {"removed": []}
    win = tk.Tk()
    win.title("Tablet Dock — Program Kaldır")
    win.attributes("-topmost", True)
    win.geometry("380x440")
    tk.Label(win, justify="left",
             text="Panelden kaldırılacak programı seç:\n"
                  "(Yalnızca panelden kaldırır — programı bilgisayardan SİLMEZ.)"
             ).pack(padx=12, pady=(12, 6), anchor="w")

    lb = tk.Listbox(win, selectmode=tk.EXTENDED)
    for a in apps:
        lb.insert(tk.END, a.get("name", a.get("id", "?")))
    lb.pack(fill="both", expand=True, padx=12)

    def do_remove():
        sel = list(lb.curselection())
        if not sel:
            return
        names = [apps[i].get("name", apps[i].get("id")) for i in sel]
        if not messagebox.askyesno("Onay", "Panelden kaldırılsın mı?\n\n" + "\n".join(names),
                                   parent=win):
            return
        drop = set(sel)
        keep = [a for i, a in enumerate(apps) if i not in drop]
        try:
            _save_apps(keep)
        except OSError as e:
            messagebox.showerror("Tablet Dock", f"Kaydedilemedi:\n{e}", parent=win)
            return
        state["removed"] = names
        win.destroy()

    bar = tk.Frame(win)
    bar.pack(fill="x", padx=12, pady=12)
    tk.Button(bar, text="Kaldır", command=do_remove).pack(side="right")
    tk.Button(bar, text="İptal", command=win.destroy).pack(side="right", padx=8)

    win.mainloop()
    if state["removed"]:
        _info("Kaldırıldı ✓\n\n" + "\n".join(state["removed"]) +
              "\n\nTabletten birkaç saniye içinde kalkacak.")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--remove":
        remove_dialog()                # kendi penceresini açar
        return
    _root()                            # tkinter kökü (gizli, öne getirir)
    if args and args[0] == "--install-sendto":
        install_sendto(silent="--silent" in args)
    elif args:
        add_path(args[0])              # Gönder ile gelen dosya
    else:
        pick_and_add()                 # tepsi menüsü / elle


if __name__ == "__main__":
    main()
