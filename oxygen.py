"""
Oxygen – Multi-platform media downloader  v3.0
Supports: YouTube · SoundCloud · X (Twitter) · Instagram · and 1000+ more via yt-dlp
Features: Playlist · Resolution/Format/Quality selection · Responsive UI · About · Drag & Drop
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, subprocess, sys, os, json, shutil, platform, re, time, webbrowser
import configparser

# ─── cross-platform font ──────────────────────────────────────────────────────
_SYS = platform.system()
if _SYS == "Darwin":
    _FONT   = "SF Pro Display"
    _FONT_M = "Menlo"
elif _SYS == "Windows":
    _FONT   = "Segoe UI"
    _FONT_M = "Consolas"
else:
    _FONT   = "DejaVu Sans"
    _FONT_M = "DejaVu Sans Mono"

def F(size, weight="normal"):
    return (_FONT, size, weight)

def FM(size):
    return (_FONT_M, size)

# ─── paths ────────────────────────────────────────────────────────────────────
# EXE_DIR  = directory of the running exe/script  (for ffmpeg & user assets)
# BASE_DIR = directory of bundled data files       (icons packed by PyInstaller)
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS                          # bundled data (icons, etc.)
    EXE_DIR  = os.path.dirname(sys.executable)       # actual exe location
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR  = BASE_DIR

def _app_data_dir():
    """Return (and create) the Oxygen config folder."""
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif platform.system() == "Darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    folder = os.path.join(base, "Oxygen")
    os.makedirs(folder, exist_ok=True)
    return folder

CFG_PATH = os.path.join(_app_data_dir(), "config.json")
ICON_PATH = os.path.join(BASE_DIR, "oxygen.ico")
LOGO_PNG  = os.path.join(BASE_DIR, "oxygen.png")

# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
BUILTIN_EN = {
    "title":                    "Oxygen",
    "subtitle":                 "media downloader",
    "mode_auto":                "✦  auto",
    "mode_audio":               "♫  audio",
    "mode_mute":                "🔇  mute",
    "btn_paste":                "📋  paste",
    "btn_download":             "↓   download",
    "btn_downloading":          "downloading…",
    "url_placeholder":          "paste the link here",
    "settings_title":           "Settings",
    "settings_theme_color":     "THEME COLOR",
    "settings_download_loc":    "DOWNLOAD LOCATION",
    "settings_browse":          "Browse",
    "settings_clipboard":       "CLIPBOARD",
    "settings_auto_paste_lbl":  "Auto-paste copied links",
    "settings_language":        "LANGUAGE",
    "settings_app_theme":       "APP THEME",
    "settings_save":            "Save",
    "settings_cancel":          "Cancel",
    "theme_dark":               "Dark",
    "theme_light":              "Light",
    "theme_oled":               "OLED",
    "toggle_on":                "ON",
    "toggle_off":               "OFF",
    "done_title":               "✓  download complete",
    "done_open":                "▶  open",
    "done_show_folder":         "📁  show folder",
    "done_close":               "✕  close",
    "status_ready":             "oxygen ready  ·  paste a link and download",
    "status_auto_paste":        "🔗 link auto-detected and pasted",
    "warn_no_link":             "Please paste a link first.",
    "err_title":                "Oxygen – Error",
    "pkg_ytdlp":                "📦 installing yt-dlp…",
    "pkg_ytdlp_ok":             "✓ yt-dlp ready",
    "pkg_pillow":               "📦 installing Pillow…",
    "pkg_pillow_ok":            "✓ Pillow ready",
    "pkg_ffmpeg":               "📦 ffmpeg not found – installing…",
    "pkg_ffmpeg_ok":            "✓ ffmpeg ready",
    "pkg_ffmpeg_fail":          "⚠ ffmpeg auto-install failed – please install manually",
    "pkg_ffmpeg_local":         "✓ ffmpeg found in app folder",
    "settings_saved_log":       "⚙ settings saved",
    # ── playlist ──
    "playlist_toggle":          "📂  playlist",
    "playlist_on":              "playlist mode ON – full list will be downloaded",
    "playlist_off":             "playlist mode OFF – single video only",
    "playlist_progress":        "⬇ item {current}/{total}: {title}",
    "playlist_done":            "✓  playlist complete – {count} items downloaded",
    # ── about ──
    "about_title":              "About",
    "about_version":            "v3.0",
    "about_desc":               "Multi-platform media downloader\npowered by yt-dlp",
    "about_github":             "GitHub",
    "about_youtube":            "YouTube",
    "about_close":              "✕  close",
    "about_made_by":            "made by maviz",
    # ── drag & drop ──
    "drop_hint":                "or drag & drop a link here",
    # ── quality / format controls ──
    "res_label":                "RESOLUTION",
    "vfmt_label":               "VIDEO FORMAT",
    "aq_label":                 "AUDIO QUALITY",
    "afmt_label":               "AUDIO FORMAT",
}

def load_lang(code: str) -> dict:
    result = dict(BUILTIN_EN)
    if code == "en":
        return result
    ini = os.path.join(BASE_DIR, f"{code}.ini")
    if not os.path.exists(ini):
        return result
    try:
        p = configparser.ConfigParser(interpolation=None)
        p.read(ini, encoding="utf-8")
        if p.has_section("oxygen"):
            for k, v in p.items("oxygen"):
                result[k] = v.replace("\\n", "\n")
    except Exception:
        pass
    return result

def get_available_langs() -> list:
    langs = {"en"}
    for f in os.listdir(BASE_DIR):
        if f.lower().endswith(".ini"):
            langs.add(f[:-4].lower())
    return sorted(langs)

# ═══════════════════════════════════════════════════════════════════════════════
# THEME SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
PALETTES = {
    "oled": {
        "BG":      "#000000",
        "BG2":     "#080808",
        "INPUT":   "#111111",
        "BORDER":  "#252525",
        "FG":      "#f5f5f5",
        "FG2":     "#cccccc",
        "MUTED":   "#505050",
        "LOG_BG":  "#080808",
        "LOG_FG":  "#888888",
        "BTN":     "#151515",
        "IS_DARK": True,
    },
    "dark": {
        "BG":      "#1a1a1a",
        "BG2":     "#141414",
        "INPUT":   "#252525",
        "BORDER":  "#383838",
        "FG":      "#f0f0f0",
        "FG2":     "#cccccc",
        "MUTED":   "#777777",
        "LOG_BG":  "#1e1e1e",
        "LOG_FG":  "#aaaaaa",
        "BTN":     "#2a2a2a",
        "IS_DARK": True,
    },
    "light": {
        "BG":      "#f0f0f0",
        "BG2":     "#e4e4e4",
        "INPUT":   "#ffffff",
        "BORDER":  "#bbbbbb",
        "FG":      "#1a1a1a",
        "FG2":     "#444444",
        "MUTED":   "#777777",
        "LOG_BG":  "#f8f8f8",
        "LOG_FG":  "#444444",
        "BTN":     "#d8d8d8",
        "IS_DARK": False,
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
def _default_downloads():
    home = os.path.expanduser("~")
    for candidate in ["Downloads", "Download", "downloads"]:
        p = os.path.join(home, candidate)
        if os.path.isdir(p):
            return p
    return home

DEFAULT_CFG = {
    "theme_color":    "#7c3aed",
    "app_theme":      "oled",
    "language":       "en",
    "download_dir":   _default_downloads(),
    "auto_paste":     True,
    "cookie_browser": "none",
    "cookie_file":    "",
    "log_visible":    False,
}

def load_cfg():
    try:
        with open(CFG_PATH, "r") as f:
            d = json.load(f)
        for k, v in DEFAULT_CFG.items():
            d.setdefault(k, v)
        return d
    except Exception:
        return dict(DEFAULT_CFG)

def save_cfg(cfg):
    with open(CFG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDENCY INSTALLER
# ═══════════════════════════════════════════════════════════════════════════════
_IS_FROZEN = getattr(sys, 'frozen', False)

def _find_python():
    """Find the real Python interpreter (not the frozen exe)."""
    # Never use sys.executable when frozen — it's the EXE itself
    if not _IS_FROZEN:
        return sys.executable
    # Search common locations
    candidates = []
    if _SYS == "Windows":
        import winreg
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for base in [r"SOFTWARE\Python\PythonCore", r"SOFTWARE\WOW6432Node\Python\PythonCore"]:
                try:
                    with winreg.OpenKey(root, base) as k:
                        for i in range(winreg.QueryInfoKey(k)[0]):
                            ver = winreg.EnumKey(k, i)
                            try:
                                with winreg.OpenKey(k, ver + r"\InstallPath") as p:
                                    path = winreg.QueryValue(p, None)
                                    exe = os.path.join(path, "python.exe")
                                    if os.path.isfile(exe):
                                        candidates.append(exe)
                            except Exception:
                                pass
                except Exception:
                    pass
        for name in ["python3.exe", "python.exe"]:
            found = shutil.which(name)
            if found:
                candidates.append(found)
    else:
        for name in ["python3", "python"]:
            found = shutil.which(name)
            if found:
                candidates.append(found)
    # Return first valid one
    for c in candidates:
        try:
            r = subprocess.run([c, "--version"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return c
        except Exception:
            pass
    return None

def _pip_install(pkg, log_cb=None):
    python = _find_python()
    if python is None:
        raise RuntimeError(
            "Python not found on PATH.\n"
            "Please install Python from https://python.org and re-run Oxygen."
        )
    cmd = [python, "-m", "pip", "install", pkg, "-q", "--upgrade"]
    if platform.system() != "Windows":
        cmd.append("--break-system-packages")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pip install {pkg} failed:\n{result.stderr.strip()}")

def ensure_deps(log_cb, tr):
    # When frozen: yt-dlp and Pillow must be bundled via PyInstaller.
    # We still check and report, but never try to pip-install into the frozen exe.
    for pkg, import_name, label in [
        ("yt-dlp",  "yt_dlp", "yt-dlp"),
        ("Pillow",  "PIL",    "Pillow"),
    ]:
        try:
            __import__(import_name)
            log_cb(f"✓ {label} ready")
        except ImportError:
            if _IS_FROZEN:
                log_cb(f"✗ {label} not bundled — rebuild EXE with updated build.bat")
            else:
                log_cb(f"📦 installing {pkg}…")
                try:
                    _pip_install(pkg, log_cb)
                    log_cb(f"✓ {label} ready")
                except Exception as e:
                    log_cb(f"✗ {label} install failed: {e}")

    # ── Check ffmpeg ─────────────────────────────────────────────────────────
    _ffmpeg_name = "ffmpeg.exe" if _SYS == "Windows" else "ffmpeg"

    # 1) next to the exe
    _local_ffmpeg = os.path.join(EXE_DIR, _ffmpeg_name)
    if os.path.isfile(_local_ffmpeg):
        os.environ["PATH"] = EXE_DIR + os.pathsep + os.environ.get("PATH", "")
        log_cb(tr.get("pkg_ffmpeg_local", "✓ ffmpeg found in app folder"))
        return

    # 2) bundled in _MEIPASS
    if BASE_DIR != EXE_DIR:
        _meipass_ffmpeg = os.path.join(BASE_DIR, _ffmpeg_name)
        if os.path.isfile(_meipass_ffmpeg):
            os.environ["PATH"] = BASE_DIR + os.pathsep + os.environ.get("PATH", "")
            log_cb(tr.get("pkg_ffmpeg_local", "✓ ffmpeg found (bundled)"))
            return

    # 3) system PATH
    if shutil.which("ffmpeg"):
        log_cb(tr.get("pkg_ffmpeg_ok", "✓ ffmpeg ready"))
        return

    # 4) warn — don't try to auto-install when frozen
    log_cb("⚠ ffmpeg not found — place ffmpeg.exe next to Oxygen.exe")
    log_cb("  Download: https://ffmpeg.org/download.html")
    if not _IS_FROZEN:
        try:
            _auto_ffmpeg(log_cb)
            log_cb(tr["pkg_ffmpeg_ok"])
        except Exception as e:
            log_cb(f"{tr['pkg_ffmpeg_fail']}: {e}")

def _auto_ffmpeg(log_cb):
    sys_name = platform.system()
    if sys_name == "Windows":
        if shutil.which("winget"):
            subprocess.check_call(
                ["winget", "install", "--id", "Gyan.FFmpeg", "-e", "--silent"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    elif sys_name == "Darwin":
        if shutil.which("brew"):
            subprocess.check_call(["brew", "install", "ffmpeg"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    else:
        for mgr, args in [
            ("apt-get", ["sudo", "apt-get", "install", "-y", "ffmpeg"]),
            ("dnf",     ["sudo", "dnf",     "install", "-y", "ffmpeg"]),
            ("pacman",  ["sudo", "pacman",  "-S", "--noconfirm", "ffmpeg"]),
        ]:
            if shutil.which(mgr):
                subprocess.check_call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
    # fallback: imageio-ffmpeg
    _pip_install("imageio-ffmpeg")
    import imageio_ffmpeg
    src = imageio_ffmpeg.get_ffmpeg_exe()
    ext = ".exe" if sys_name == "Windows" else ""
    dst = os.path.join(EXE_DIR, f"ffmpeg{ext}")
    shutil.copy2(src, dst)
    log_cb(f"  → ffmpeg placed at {dst}")

# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════
def send_notification(title, message):
    """Send OS-level toast/notification. Fire-and-forget."""
    try:
        if _SYS == "Windows":
            ps_script = (
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$ico = [System.Drawing.SystemIcons]::Information;"
                "$n = New-Object System.Windows.Forms.NotifyIcon;"
                "$n.Icon = $ico;"
                "$n.Visible = $True;"
                f'$n.ShowBalloonTip(4000, "{title}", "{message}", '
                "[System.Windows.Forms.ToolTipIcon]::Info);"
                "Start-Sleep -Milliseconds 4500;"
                "$n.Dispose()"
            )
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=0x08000000 if _SYS == "Windows" else 0)
        elif _SYS == "Darwin":
            subprocess.Popen(
                ["osascript", "-e",
                 f'display notification "{message}" with title "{title}"'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(
                ["notify-send", "-i", "emblem-downloads", title, message],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def looks_like_url(t):
    return t.startswith("http") and "." in t

def set_window_icon(window):
    if os.path.exists(ICON_PATH):
        try:
            window.iconbitmap(ICON_PATH)
            return
        except Exception:
            pass
    for path in [LOGO_PNG, ICON_PATH]:
        if os.path.exists(path):
            try:
                from PIL import Image, ImageTk
                img   = Image.open(path).convert("RGBA").resize((64, 64))
                photo = ImageTk.PhotoImage(img)
                window.iconphoto(True, photo)
                window._icon_ref = photo
                return
            except Exception:
                pass

def darken(hx, f=0.7):
    hx = hx.lstrip("#")
    r,g,b = int(hx[0:2],16), int(hx[2:4],16), int(hx[4:6],16)
    return "#{:02x}{:02x}{:02x}".format(int(r*f), int(g*f), int(b*f))

def lighten(hx, f=1.3):
    hx = hx.lstrip("#")
    r,g,b = int(hx[0:2],16), int(hx[2:4],16), int(hx[4:6],16)
    return "#{:02x}{:02x}{:02x}".format(min(255,int(r*f)), min(255,int(g*f)), min(255,int(b*f)))

def blend(c1, c2, t):
    h1,h2 = c1.lstrip("#"), c2.lstrip("#")
    r1,g1,b1 = int(h1[0:2],16), int(h1[2:4],16), int(h1[4:6],16)
    r2,g2,b2 = int(h2[0:2],16), int(h2[2:4],16), int(h2[4:6],16)
    r = int(r1 + (r2-r1)*t)
    g = int(g1 + (g2-g1)*t)
    b = int(b1 + (b2-b1)*t)
    return "#{:02x}{:02x}{:02x}".format(r,g,b)

def acc_fg(acc_color):
    h = acc_color.lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    lum = 0.299*r + 0.587*g + 0.114*b
    return "#000000" if lum > 160 else "#ffffff"

def acc_bg(acc, alpha=0.18, on_light=False):
    """Accent background tint. on_light=True blends toward white instead of black."""
    h = acc.lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    if on_light:
        # blend accent toward white for light theme
        r2 = int(r + (255-r)*(1-alpha*2.5))
        g2 = int(g + (255-g)*(1-alpha*2.5))
        b2 = int(b + (255-b)*(1-alpha*2.5))
        return "#{:02x}{:02x}{:02x}".format(
            max(0,min(255,r2)), max(0,min(255,g2)), max(0,min(255,b2)))
    return "#{:02x}{:02x}{:02x}".format(int(r*alpha), int(g*alpha), int(b*alpha))

def draw_gradient(canvas, w, h, color, bg):
    canvas.delete("all")
    for y in range(h):
        t = y / max(h - 1, 1)
        c = blend(bg, color, t)
        canvas.create_line(0, y, w, y, fill=c)

# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY / FORMAT OPTIONS
# ═══════════════════════════════════════════════════════════════════════════════
RES_OPTS  = ["best", "4K (2160p)", "1440p", "1080p", "720p", "480p", "360p", "240p", "worst"]
VFMT_OPTS = ["mp4", "mkv", "webm", "avi", "mov"]
AQ_OPTS   = ["best", "320k", "256k", "192k", "128k", "96k", "64k"]
AFMT_OPTS = ["mp3", "m4a", "opus", "flac", "wav", "aac"]

# height in pixels for each resolution label
_RES_HEIGHT = {
    "best": None, "4K (2160p)": 2160, "1440p": 1440, "1080p": 1080,
    "720p": 720, "480p": 480, "360p": 360, "240p": 240, "worst": -1,
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
class Oxygen(tk.Tk):

    THEME_PRESETS = [
        ("#7c3aed","Violet"), ("#2563eb","Blue"),  ("#059669","Emerald"),
        ("#dc2626","Red"),    ("#d97706","Amber"),  ("#db2777","Pink"),
        ("#0891b2","Cyan"),   ("#ffffff","White"),
    ]

    SOCIAL_GITHUB  = "https://github.com/Mav1zz"
    SOCIAL_YOUTUBE = "https://youtube.com/@Mav1zz"

    def __init__(self):
        super().__init__()
        self.cfg        = load_cfg()
        self.tr         = load_lang(self.cfg.get("language","en"))
        self._pal       = PALETTES[self.cfg.get("app_theme","oled")]

        self.title(self.tr["title"])
        self.resizable(True, True)

        self._W, self._H = 660, 580
        self._MIN_W, self._MIN_H = 500, 440
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{self._W}x{self._H}+{(sw-self._W)//2}+{(sh-self._H)//2}")
        self.minsize(self._MIN_W, self._MIN_H)
        self.configure(bg=self._pal["BG"])

        set_window_icon(self)

        self.mode         = tk.StringVar(value="auto")
        self.url_var      = tk.StringVar()
        self._dl_thread   = None
        self._last_clip   = ""
        self._last_file   = None
        self._status      = "idle"
        self._logo_img    = None
        self._playlist_on = False
        self._log_visible = self.cfg.get("log_visible", False)

        # ── quality / format selections ──
        self.res_var  = tk.StringVar(value="best")
        self.vfmt_var = tk.StringVar(value="mp4")
        self.aq_var   = tk.StringVar(value="best")
        self.afmt_var = tk.StringVar(value="mp3")

        self._build_ui()
        self._setup_drag_drop()
        self._start_clip_watcher()
        self.after(300, lambda: threading.Thread(
            target=ensure_deps, args=(self._log, self.tr), daemon=True).start())

    # ── theme / palette shorthands ───────────────────────────────────────────
    @property
    def P(self): return self._pal
    @property
    def ACC(self): return self.cfg["theme_color"]
    @property
    def ACC_D(self): return darken(self.ACC)
    @property
    def ACC_BG(self): return acc_bg(self.ACC, on_light=not self.P.get("IS_DARK", True))
    @property
    def ACC_BTN_FG(self):
        """Foreground for active mode buttons — always readable."""
        return self.ACC if not self.P.get("IS_DARK", True) else self.P["FG"]
    @property
    def ACC_FG(self): return acc_fg(self.ACC)

    # ── build UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        P  = self.P
        tr = self.tr

        # ── top bar ──────────────────────────────────────────────────────────
        self._top_frame = tk.Frame(self, bg=P["BG"])
        self._top_frame.pack(fill="x", padx=24, pady=(16,0))

        self._lbl_title = tk.Label(self._top_frame, text=tr["title"],
            font=F(13, "bold"), bg=P["BG"], fg=P["FG"])
        self._lbl_title.pack(side="left")

        self._lbl_sub = tk.Label(self._top_frame, text=tr["subtitle"],
            font=F(10), bg=P["BG"], fg=P["MUTED"])
        self._lbl_sub.pack(side="left", padx=8)

        badge_row = tk.Frame(self._top_frame, bg=P["BG"])
        badge_row.pack(side="left", padx=8)
        for plat, col, tfg in [("YT","#ff0000","#fff"),("SC","#ff5500","#000"),
                                 ("𝕏","#ffffff","#000"),("IG","#e1306c","#fff")]:
            tk.Label(badge_row, text=plat, font=F(8, "bold"),
                     bg=col, fg=tfg, padx=5, pady=1).pack(side="left", padx=2)

        self._gear_btn = tk.Button(
            self._top_frame, text="⚙", font=F(14),
            bg=P["BG"], fg=P["MUTED"],
            activebackground=P["BG"], activeforeground=P["FG"],
            relief="flat", bd=0, cursor="hand2",
            command=self._open_settings)
        self._gear_btn.pack(side="right")

        self._about_btn = tk.Button(
            self._top_frame, text="ℹ", font=F(14),
            bg=P["BG"], fg=P["MUTED"],
            activebackground=P["BG"], activeforeground=P["FG"],
            relief="flat", bd=0, cursor="hand2",
            command=self._open_about)
        self._about_btn.pack(side="right", padx=(0, 4))

        # ── logo ─────────────────────────────────────────────────────────────
        self._logo_frame = tk.Frame(self, bg=P["BG"])
        self._logo_frame.pack(pady=(10, 6))
        self._logo_label = None
        self._load_logo()

        # ── URL input ────────────────────────────────────────────────────────
        self._inp_wrap = tk.Frame(self, bg=P["BG"])
        self._inp_wrap.pack(padx=50, fill="x")

        self._inp_c = tk.Canvas(self._inp_wrap, height=44, bg=P["BG"], highlightthickness=0)
        self._inp_c.pack(fill="x")

        def _draw_inp(e=None):
            self._inp_c.delete("bg")
            w  = self._inp_c.winfo_width() or 540
            PP = self.P
            pts = [8,0, w-8,0, w,0, w,8, w,36, w,44,
                   w-8,44, 8,44, 0,44, 0,36, 0,8, 0,0]
            self._inp_c.create_polygon(pts, smooth=True,
                fill=PP["INPUT"], outline=PP["BORDER"], width=1, tags="bg")
        self._inp_c.bind("<Configure>", _draw_inp)
        self._draw_inp = _draw_inp

        self._inp_c.create_text(22, 22, text="🔗", font=F(12),
                                fill=P["MUTED"], anchor="center", tags="icon")

        self.url_entry = tk.Entry(
            self._inp_c, textvariable=self.url_var,
            bg=P["INPUT"], fg=P["FG"],
            insertbackground=P["FG"],
            relief="flat", font=F(10),
            highlightthickness=0, bd=0)
        self.url_entry.place(x=42, y=12, relwidth=1.0, width=-52, height=20)
        self._set_placeholder()
        self.url_entry.bind("<FocusIn>",  self._on_focus_in)
        self.url_entry.bind("<FocusOut>", self._on_focus_out)

        # ── mode + paste row ─────────────────────────────────────────────────
        self._ctrl_frame = tk.Frame(self, bg=P["BG"])
        self._ctrl_frame.pack(padx=50, pady=(8,0), fill="x")

        self._mode_frame = tk.Frame(self._ctrl_frame, bg=P["BTN"],
            highlightbackground=P["BORDER"], highlightthickness=1)
        self._mode_frame.pack(side="left")

        self._mbtn = {}
        for key, val in [("mode_auto","auto"),("mode_audio","audio"),("mode_mute","mute")]:
            b = tk.Button(self._mode_frame, text=tr[key],
                font=F(9, "bold"),
                bg=P["BTN"], fg=P["FG"],
                activebackground=P["INPUT"], activeforeground=P["FG"],
                relief="flat", bd=0, padx=12, pady=7,
                cursor="hand2", command=lambda v=val: self._set_mode(v))
            b.pack(side="left")
            self._mbtn[val] = b

        # playlist toggle
        self._playlist_btn = tk.Button(self._ctrl_frame, text=tr["playlist_toggle"],
            font=F(9, "bold"),
            bg=P["BTN"], fg=P["MUTED"],
            activebackground=P["INPUT"], activeforeground=P["FG"],
            relief="flat", bd=0, padx=12, pady=7,
            highlightbackground=P["BORDER"], highlightthickness=1,
            cursor="hand2", command=self._toggle_playlist)
        self._playlist_btn.pack(side="left", padx=(8, 0))

        self._paste_btn = tk.Button(self._ctrl_frame, text=tr["btn_paste"],
            font=F(9, "bold"),
            bg=P["BTN"], fg=P["FG"],
            activebackground=P["INPUT"], activeforeground=P["FG"],
            relief="flat", bd=0, padx=14, pady=7,
            highlightbackground=P["BORDER"], highlightthickness=1,
            cursor="hand2", command=self._paste_url)
        self._paste_btn.pack(side="right")

        # ── quality / format row ─────────────────────────────────────────────
        self._qrow = tk.Frame(self, bg=P["BG"])
        self._qrow.pack(padx=50, pady=(8,0), fill="x")

        # ttk combobox style
        self._apply_combo_style()

        def _qlabel(parent, text):
            tk.Label(parent, text=text, font=F(7, "bold"),
                bg=P["BG"], fg=P["MUTED"]).pack(side="left", padx=(0,3))

        def _qcombo(parent, var, values, width=10):
            cb = ttk.Combobox(parent, textvariable=var, values=values,
                state="readonly", font=F(9), width=width, style="Q.TCombobox")
            cb.pack(side="left", padx=(0,4))
            return cb

        # Resolution (video / auto / mute modes)
        self._res_frame = tk.Frame(self._qrow, bg=P["BG"])
        _qlabel(self._res_frame, tr["res_label"])
        self._res_combo = _qcombo(self._res_frame, self.res_var, RES_OPTS, width=11)

        # Video format
        self._vfmt_frame = tk.Frame(self._qrow, bg=P["BG"])
        _qlabel(self._vfmt_frame, tr["vfmt_label"])
        self._vfmt_combo = _qcombo(self._vfmt_frame, self.vfmt_var, VFMT_OPTS, width=6)

        # Audio quality (audio mode)
        self._aq_frame = tk.Frame(self._qrow, bg=P["BG"])
        _qlabel(self._aq_frame, tr["aq_label"])
        self._aq_combo = _qcombo(self._aq_frame, self.aq_var, AQ_OPTS, width=8)

        # Audio format (audio mode)
        self._afmt_frame = tk.Frame(self._qrow, bg=P["BG"])
        _qlabel(self._afmt_frame, tr["afmt_label"])
        self._afmt_combo = _qcombo(self._afmt_frame, self.afmt_var, AFMT_OPTS, width=6)

        # Initial mode (auto)
        self._set_mode("auto")

        # ── download button ───────────────────────────────────────────────────
        self.dl_btn = tk.Button(self, text=tr["btn_download"],
            font=F(11, "bold"),
            bg=self.ACC, fg=self.ACC_FG,
            activebackground=self.ACC_D, activeforeground=self.ACC_FG,
            relief="flat", bd=0, pady=10, cursor="hand2",
            command=self._start_download)
        self.dl_btn.pack(padx=50, pady=(10,0), fill="x")

        # ── progress bar ─────────────────────────────────────────────────────
        s = ttk.Style(self)
        s.theme_use("default")
        s.configure("O.Horizontal.TProgressbar",
            troughcolor=P["INPUT"], background=self.ACC,
            thickness=3, borderwidth=0)
        self.pb = ttk.Progressbar(self, style="O.Horizontal.TProgressbar",
                                   mode="indeterminate", length=400)
        self.pb.pack(padx=50, pady=(4,0), fill="x")

        # ── log toggle bar ────────────────────────────────────────────────────
        self._log_toggle_bar = tk.Frame(self, bg=P["BG"])
        self._log_toggle_bar.pack(padx=50, pady=(8, 0), fill="x")

        self._log_toggle_btn = tk.Button(
            self._log_toggle_bar, text="▼  log",
            font=F(8), bg=P["BG"], fg=P["MUTED"],
            activebackground=P["BG"], activeforeground=P["FG"],
            relief="flat", bd=0, cursor="hand2",
            command=self._toggle_log)
        self._log_toggle_btn.pack(side="left")

        # ── log box (hidden by default) ───────────────────────────────────────
        self._log_frame = tk.Frame(self, bg=P["LOG_BG"],
            highlightbackground=P["BORDER"], highlightthickness=1)

        self.log_box = tk.Text(self._log_frame, bg=P["LOG_BG"], fg=P["LOG_FG"],
            font=FM(9), relief="flat", bd=0,
            state="disabled", wrap="word", height=5)
        self._log_sb = tk.Scrollbar(self._log_frame, command=self.log_box.yview,
            bg=P["LOG_BG"], troughcolor=P["LOG_BG"],
            activebackground=P["BORDER"], relief="flat")
        self.log_box.config(yscrollcommand=self._log_sb.set)
        self.log_box.pack(side="left", fill="both", expand=True, padx=8, pady=5)
        self._log_sb.pack(side="right", fill="y")

        # ── bottom spacer (visible when log is hidden, centers content) ───────
        self._bottom_spacer = tk.Frame(self, bg=P["BG"], height=1)

        # Apply initial log visibility
        self._log_visible = self.cfg.get("log_visible", False)
        self._apply_log_visibility()

        self._log(tr["status_ready"])

    # ── combo style ──────────────────────────────────────────────────────────
    def _apply_combo_style(self):
        P = self.P
        style = ttk.Style(self)
        style.configure("Q.TCombobox",
            fieldbackground=P["INPUT"],
            background=P["BTN"],
            foreground=P["FG"],
            selectbackground=self.ACC,
            selectforeground=acc_fg(self.ACC),
            arrowcolor=P["FG2"],
            insertcolor=P["FG"],
            padding=(4, 2))
        style.map("Q.TCombobox",
            fieldbackground=[("readonly", P["INPUT"]), ("focus", P["INPUT"])],
            foreground=[("readonly", P["FG"]), ("focus", P["FG"])],
            selectbackground=[("readonly", self.ACC)],
            selectforeground=[("readonly", acc_fg(self.ACC))],
            arrowcolor=[("disabled", P["MUTED"]), ("pressed", P["FG"])])
        # Also style the Listbox that pops up (option_add)
        self.option_add("*TCombobox*Listbox.background",   P["INPUT"])
        self.option_add("*TCombobox*Listbox.foreground",   P["FG"])
        self.option_add("*TCombobox*Listbox.selectBackground", self.ACC)
        self.option_add("*TCombobox*Listbox.selectForeground", acc_fg(self.ACC))
        self.option_add("*TCombobox*Listbox.font",         FM(9))

    # ── quality visibility per mode ──────────────────────────────────────────
    def _update_quality_visibility(self, mode):
        """Show/hide format controls based on the active download mode."""
        for f in [self._res_frame, self._vfmt_frame, self._aq_frame, self._afmt_frame]:
            f.pack_forget()

        if mode == "audio":
            # Audio-only: show audio quality + audio format
            self._aq_frame.pack(side="left", padx=(0, 6))
            self._afmt_frame.pack(side="left")
        elif mode == "mute":
            # Video, no audio: show resolution + video format
            self._res_frame.pack(side="left", padx=(0, 6))
            self._vfmt_frame.pack(side="left")
        else:  # auto
            # Video + audio: show resolution + video format
            self._res_frame.pack(side="left", padx=(0, 6))
            self._vfmt_frame.pack(side="left")

    # ── log toggle ───────────────────────────────────────────────────────────
    def _toggle_log(self):
        self._log_visible = not self._log_visible
        self.cfg["log_visible"] = self._log_visible
        save_cfg(self.cfg)
        self._apply_log_visibility()

    def _apply_log_visibility(self):
        P = self.P
        if self._log_visible:
            self._bottom_spacer.pack_forget()
            self._log_frame.pack(padx=50, pady=(4, 16), fill="both", expand=True)
            self._log_toggle_btn.config(text="▲  log", fg=P["FG2"])
            # Restore window to taller size if it was collapsed
            if self.winfo_height() < 480:
                self.geometry(f"{self.winfo_width()}x580")
        else:
            self._log_frame.pack_forget()
            self._bottom_spacer.pack(pady=(4, 16), fill="both", expand=True)
            self._log_toggle_btn.config(text="▼  log", fg=P["MUTED"])
            # Shrink window
            self.after(10, lambda: self.geometry(
                f"{self.winfo_width()}x{self._compact_height()}"))

    def _compact_height(self):
        """Calculate the height needed when log is hidden."""
        self.update_idletasks()
        h = 0
        for w in [self._top_frame, self._logo_frame, self._inp_wrap,
                  self._ctrl_frame, self._qrow, self.dl_btn, self.pb,
                  self._log_toggle_bar]:
            try:
                h += w.winfo_reqheight() + 8
            except Exception:
                pass
        return max(380, min(h + 50, 480))

    # ── logo loader ──────────────────────────────────────────────────────────
    def _load_logo(self):
        if self._logo_label:
            self._logo_label.destroy()
            self._logo_label = None

        P = self.P
        self._logo_frame.config(bg=P["BG"])

        for path in [LOGO_PNG, ICON_PATH]:
            if os.path.exists(path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(path).convert("RGBA").resize((88, 88), Image.LANCZOS)
                    self._logo_img = ImageTk.PhotoImage(img)
                    self._logo_label = tk.Label(self._logo_frame, image=self._logo_img,
                        bg=P["BG"], bd=0, highlightthickness=0)
                    self._logo_label.pack()
                    return
                except Exception:
                    pass

        self._logo_label = tk.Label(self._logo_frame, text="⊙",
            font=F(52), bg=P["BG"], fg=self.ACC, bd=0)
        self._logo_label.pack()

    # ── status bar ───────────────────────────────────────────────────────────
    def _update_status_bar(self, status=None):
        if status:
            self._status = status

    # ── placeholder ──────────────────────────────────────────────────────────
    def _set_placeholder(self):
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, self.tr["url_placeholder"])
        self.url_entry.config(fg=self.P["MUTED"])
        self._placeholder_active = True

    def _on_focus_in(self, _=None):
        if getattr(self, "_placeholder_active", False):
            self.url_entry.delete(0, "end")
            self.url_entry.config(fg=self.P["FG"])
            self._placeholder_active = False

    def _on_focus_out(self, _=None):
        if not self.url_entry.get().strip():
            self._set_placeholder()

    # ── mode buttons ─────────────────────────────────────────────────────────
    def _set_mode(self, val):
        self.mode.set(val)
        P = self.P
        for v, b in self._mbtn.items():
            if v == val:
                b.config(bg=self.ACC_BG, fg=self.ACC_BTN_FG,
                         activeforeground=self.ACC_BTN_FG)
            else:
                b.config(bg=P["BTN"], fg=P["MUTED"],
                         activeforeground=P["FG"])
        self._update_quality_visibility(val)

    # ── playlist toggle ──────────────────────────────────────────────────────
    def _toggle_playlist(self):
        self._playlist_on = not self._playlist_on
        P = self.P
        if self._playlist_on:
            self._playlist_btn.config(bg=self.ACC_BG, fg=P["FG"])
            self._log(self.tr["playlist_on"])
        else:
            self._playlist_btn.config(bg=P["BTN"], fg=P["MUTED"])
            self._log(self.tr["playlist_off"])

    # ── drag & drop support ──────────────────────────────────────────────────
    def _setup_drag_drop(self):
        try:
            self.bind("<Button-2>", self._handle_middle_click_paste)
            self.url_entry.bind("<Control-v>", self._handle_keyboard_paste)
        except Exception:
            pass

    def _handle_middle_click_paste(self, event=None):
        self._paste_url()

    def _handle_keyboard_paste(self, event=None):
        if getattr(self, "_placeholder_active", False):
            self._on_focus_in()
        return None

    # ── clipboard watcher ────────────────────────────────────────────────────
    def _start_clip_watcher(self):
        def watch():
            while True:
                try:
                    if self.cfg.get("auto_paste", True):
                        clip = self.clipboard_get().strip()
                        if clip != self._last_clip and looks_like_url(clip):
                            self._last_clip = clip
                            self.after(0, self._auto_paste, clip)
                except Exception:
                    pass
                time.sleep(1)
        threading.Thread(target=watch, daemon=True).start()

    def _auto_paste(self, txt):
        cur = self.url_entry.get()
        if cur == self.tr["url_placeholder"] or not cur.strip():
            self._on_focus_in()
            self.url_entry.delete(0,"end")
            self.url_entry.insert(0, txt)
            self.url_entry.config(fg=self.P["FG"])
            self._log(self.tr["status_auto_paste"])

    def _paste_url(self):
        try:
            txt = self.clipboard_get().strip()
            self._on_focus_in()
            self.url_entry.delete(0,"end")
            self.url_entry.insert(0, txt)
            self.url_entry.config(fg=self.P["FG"])
        except Exception:
            pass

    # ── log ──────────────────────────────────────────────────────────────────
    def _log(self, msg):
        def _do():
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg+"\n")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        try: self.after(0, _do)
        except Exception: pass

    # ── download ─────────────────────────────────────────────────────────────
    def _start_download(self):
        url = self.url_entry.get().strip()
        if not url or url == self.tr["url_placeholder"]:
            messagebox.showwarning("Oxygen", self.tr["warn_no_link"])
            return
        if self._dl_thread and self._dl_thread.is_alive():
            return

        out_dir = self.cfg["download_dir"]
        os.makedirs(out_dir, exist_ok=True)

        self.dl_btn.config(state="disabled",
            text=self.tr["btn_downloading"],
            bg=darken(self.ACC, 0.6))
        self.pb.start(12)
        self._update_status_bar("downloading")

        res   = self.res_var.get()
        vfmt  = self.vfmt_var.get()
        aq    = self.aq_var.get()
        afmt  = self.afmt_var.get()
        mode  = self.mode.get()

        self._log(f"▶ [{mode.upper()}] {url}")
        if mode == "audio":
            self._log(f"  ♫ {afmt.upper()}  ·  quality {aq}")
        else:
            self._log(f"  🎬 {res}  ·  {vfmt.upper()}")

        self._dl_thread = threading.Thread(
            target=self._do_download,
            args=(url, out_dir, mode, res, vfmt, aq, afmt), daemon=True)
        self._dl_thread.start()

    def _do_download(self, url, out_dir, mode, res, vfmt, aq, afmt):
        try:
            try:
                import yt_dlp
            except ImportError:
                raise RuntimeError(
                    "yt-dlp is not available.\n\n"
                    "EXE kullanıyorsanız: build.bat ile yeniden derleyin.\n"
                    "Python ile çalıştırıyorsanız: pip install yt-dlp"
                )

            saved = []

            def hook(d):
                if d.get("status") == "downloading":
                    pct = d.get("_percent_str","").strip()
                    spd = d.get("_speed_str","").strip()
                    eta = d.get("_eta_str","").strip()
                    self._log(f"  {pct}  {spd}  eta {eta}")
                elif d.get("status") == "finished":
                    fn = d.get("filename","")
                    saved.append(fn)
                    self._log(f"  ✓ {os.path.basename(fn)}")
                elif d.get("status") == "error":
                    err = d.get("error", "")
                    if err:
                        self._log(f"  ✗ hata: {err}")

            opts = {
                "outtmpl":           os.path.join(out_dir, "%(title)s.%(ext)s"),
                "progress_hooks":    [hook],
                "quiet":             True,
                "no_warnings":       True,
                "ignoreerrors":      False,
                "retries":           5,
                "fragment_retries":  5,
                "http_headers": {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                },
            }

            # ── cookie bypass (fixes YouTube 403) ─────────────────────────
            # Priority: cookies.txt file > browser cookies
            cookie_file = self.cfg.get("cookie_file", "").strip()
            browser = self.cfg.get("cookie_browser", "none")
            if cookie_file and os.path.isfile(cookie_file):
                opts["cookiefile"] = cookie_file
                self._log(f"  🍪 cookies.txt: {os.path.basename(cookie_file)}")
            elif browser and browser != "none":
                opts["cookiesfrombrowser"] = (browser,)
                self._log(f"  🍪 cookies from {browser}")

            # ── playlist ──────────────────────────────────────────────────
            if self._playlist_on:
                opts["noplaylist"] = False
                opts["outtmpl"] = os.path.join(
                    out_dir,
                    "%(playlist_title|Playlist)s",
                    "%(playlist_index|0)03d - %(title)s.%(ext)s")
                opts["ignoreerrors"] = True  # skip unavailable items in playlist

                _orig_hook = hook
                def playlist_hook(d):
                    _orig_hook(d)
                    if d.get("status") == "downloading":
                        info = d.get("info_dict", {})
                        idx   = d.get("playlist_index") or info.get("playlist_index")
                        total = d.get("playlist_count") or info.get("playlist_count")
                        title = info.get("title","")
                        if idx and total:
                            self._log(self.tr["playlist_progress"].format(
                                current=idx, total=total, title=title))
                opts["progress_hooks"] = [playlist_hook]
            else:
                opts["noplaylist"] = True

            # ── format / quality selection ────────────────────────────────
            height = _RES_HEIGHT.get(res, None)

            if mode == "audio":
                aq_num = aq.rstrip("k") if aq != "best" else "0"
                opts["format"] = "bestaudio/best"
                opts["postprocessors"] = [{
                    "key":              "FFmpegExtractAudio",
                    "preferredcodec":   afmt,
                    "preferredquality": aq_num,
                }]

            elif mode == "mute":
                if height == -1:
                    opts["format"] = "worstvideo"
                elif height:
                    opts["format"] = (
                        f"bestvideo[height<={height}][ext={vfmt}]/"
                        f"bestvideo[height<={height}]/bestvideo"
                    )
                else:
                    opts["format"] = f"bestvideo[ext={vfmt}]/bestvideo"
                opts["merge_output_format"] = vfmt

            else:  # auto
                if height == -1:
                    opts["format"] = "worstvideo+worstaudio/worst"
                elif height:
                    opts["format"] = (
                        f"bestvideo[height<={height}][ext={vfmt}]+bestaudio[ext=m4a]/"
                        f"bestvideo[height<={height}][ext={vfmt}]+bestaudio/"
                        f"bestvideo[height<={height}]+bestaudio/"
                        f"best[height<={height}]/best"
                    )
                else:
                    opts["format"] = (
                        f"bestvideo[ext={vfmt}]+bestaudio[ext=m4a]/"
                        f"bestvideo[ext={vfmt}]+bestaudio/"
                        f"bestvideo+bestaudio/best"
                    )
                opts["merge_output_format"] = vfmt

            self._log(f"  format: {opts['format']}")

            def _run_download(download_opts):
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    retcode = ydl.download([url])
                    if retcode != 0:
                        self._log(f"  ⚠ yt-dlp returned code {retcode}")

            try:
                _run_download(opts)
            except Exception as dl_err:
                err_str = str(dl_err)
                # Cookie errors (browser locked, permission denied, etc.)
                if "cookie" in err_str.lower() or "CookieLoad" in err_str:
                    self._log("  ⚠ Cookie okuma hatasi — tarayici acik olabilir.")
                    self._log("  ↻ Cookie olmadan tekrar deneniyor...")
                    opts_no_cookie = dict(opts)
                    opts_no_cookie.pop("cookiesfrombrowser", None)
                    opts_no_cookie.pop("cookiefile", None)
                    _run_download(opts_no_cookie)
                else:
                    raise

            if self._playlist_on and len(saved) > 1:
                self._log(self.tr["playlist_done"].format(count=len(saved)))

            final = saved[-1] if saved else None
            self.after(0, self._on_done, True, final, out_dir)

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self._log(f"  ✗ HATA: {e}")
            # Log full traceback to help debug
            for line in tb.splitlines():
                self._log(f"    {line}")
            self.after(0, self._on_done, False, None, out_dir, str(e))

    def _on_done(self, ok, filepath, out_dir, err=""):
        self.pb.stop()
        self.dl_btn.config(state="normal",
            text=self.tr["btn_download"],
            bg=self.ACC, fg=self.ACC_FG)
        self._update_status_bar("success" if ok else "error")

        if not ok:
            self._log(f"✗ {err}")
            messagebox.showerror(self.tr["err_title"], err)
            self.after(4000, lambda: self._update_status_bar("idle"))
            return

        self._last_file = filepath
        fname = os.path.basename(filepath) if filepath else "file"
        self._log(self.tr["status_ready"].split("·")[0].strip())
        # OS notification
        threading.Thread(
            target=send_notification,
            args=("Oxygen — Download Complete", fname),
            daemon=True).start()
        self._show_done_dialog(filepath, out_dir)
        self.after(5000, lambda: self._update_status_bar("idle"))

    # ── done dialog ──────────────────────────────────────────────────────────
    def _show_done_dialog(self, filepath, folder):
        P  = self.P
        tr = self.tr
        d  = tk.Toplevel(self)
        d.title(self.tr["title"] + " – done")
        d.configure(bg=P["BG2"])
        d.resizable(False, False)
        W2, H2 = 420, 210
        cx = self.winfo_x() + (self.winfo_width()  - W2) // 2
        cy = self.winfo_y() + (self.winfo_height() - H2) // 2
        d.geometry(f"{W2}x{H2}+{cx}+{cy}")
        d.grab_set()
        set_window_icon(d)

        tk.Label(d, text=tr["done_title"],
            font=F(12, "bold"), bg=P["BG2"], fg=P["FG"]
            ).pack(pady=(22,4))

        fname = os.path.basename(filepath) if filepath else "file"
        tk.Label(d, text=(fname[:44]+"…") if len(fname)>47 else fname,
            font=FM(9), bg=P["BG2"], fg=P["MUTED"], wraplength=380
            ).pack(pady=(0,2))
        tk.Label(d, text=f"📁  {folder}",
            font=F(9), bg=P["BG2"], fg=P["MUTED"]
            ).pack(pady=(0,16))

        br = tk.Frame(d, bg=P["BG2"])
        br.pack()

        def _open():
            if filepath and os.path.exists(filepath):
                if _SYS == "Windows":
                    os.startfile(filepath)
                elif _SYS == "Darwin":
                    subprocess.Popen(["open", filepath])
                else:
                    subprocess.Popen(["xdg-open", filepath])
            d.destroy()

        def _show():
            if _SYS == "Windows":
                if filepath and os.path.exists(filepath):
                    subprocess.Popen(["explorer", "/select,", filepath])
                else:
                    subprocess.Popen(["explorer", folder])
            elif _SYS == "Darwin":
                subprocess.Popen(["open", "-R", filepath] if filepath and os.path.exists(filepath) else ["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            d.destroy()

        for txt, cmd, bg in [
            (tr["done_open"],        _open,     self.ACC),
            (tr["done_show_folder"], _show,     P["BTN"]),
            (tr["done_close"],       d.destroy, P["BTN"]),
        ]:
            fg = acc_fg(bg) if bg == self.ACC else P["FG"]
            tk.Button(br, text=txt, font=F(9, "bold"),
                bg=bg, fg=fg,
                activebackground=darken(bg,0.85), activeforeground=fg,
                relief="flat", bd=0, padx=14, pady=7,
                cursor="hand2", command=cmd).pack(side="left", padx=5)

    # ── about window ─────────────────────────────────────────────────────────
    def _open_about(self):
        P  = self.P
        tr = self.tr
        d  = tk.Toplevel(self)
        d.title(f"{tr['title']} – {tr['about_title']}")
        d.configure(bg=P["BG2"])
        d.resizable(False, False)
        W2, H2 = 380, 340
        cx = self.winfo_x() + (self.winfo_width()  - W2) // 2
        cy = self.winfo_y() + (self.winfo_height() - H2) // 2
        d.geometry(f"{W2}x{H2}+{cx}+{cy}")
        d.grab_set()
        set_window_icon(d)

        about_logo_frame = tk.Frame(d, bg=P["BG2"])
        about_logo_frame.pack(pady=(24, 8))
        _about_logo = None
        for path in [LOGO_PNG, ICON_PATH]:
            if os.path.exists(path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(path).convert("RGBA").resize((64, 64), Image.LANCZOS)
                    _about_logo = ImageTk.PhotoImage(img)
                    lbl = tk.Label(about_logo_frame, image=_about_logo,
                        bg=P["BG2"], bd=0, highlightthickness=0)
                    lbl.image = _about_logo
                    lbl.pack()
                    break
                except Exception:
                    pass
        if _about_logo is None:
            tk.Label(about_logo_frame, text="⊙", font=F(40),
                bg=P["BG2"], fg=self.ACC, bd=0).pack()

        tk.Label(d, text=tr["title"],
            font=F(16, "bold"), bg=P["BG2"], fg=P["FG"]).pack(pady=(4,0))
        tk.Label(d, text=tr["about_version"],
            font=F(10), bg=P["BG2"], fg=self.ACC).pack(pady=(0,4))
        tk.Label(d, text=tr["about_desc"],
            font=F(9), bg=P["BG2"], fg=P["MUTED"],
            justify="center").pack(pady=(0,16))

        tk.Label(d, text=tr["about_made_by"],
            font=F(10, "bold"), bg=P["BG2"], fg=P["FG2"]).pack(pady=(0,12))

        tk.Frame(d, bg=P["BORDER"], height=1).pack(fill="x", padx=40, pady=(0,16))

        link_frame = tk.Frame(d, bg=P["BG2"])
        link_frame.pack()
        for label, icon, url, bg_color, fg_color in [
            (tr["about_github"],  "⚡", self.SOCIAL_GITHUB,  "#333333", "#ffffff"),
            (tr["about_youtube"], "▶",  self.SOCIAL_YOUTUBE, "#ff0000", "#ffffff"),
        ]:
            btn = tk.Button(link_frame, text=f"{icon}  {label}",
                font=F(10, "bold"),
                bg=bg_color, fg=fg_color,
                activebackground=darken(bg_color, 0.8), activeforeground=fg_color,
                relief="flat", bd=0, padx=20, pady=8,
                cursor="hand2",
                command=lambda u=url: webbrowser.open(u))
            btn.pack(side="left", padx=6)

        tk.Frame(d, bg=P["BORDER"], height=1).pack(fill="x", padx=40, pady=(16,0))
        tk.Button(d, text=tr["about_close"],
            font=F(10), bg=P["BTN"], fg=P["FG2"],
            activebackground=P["INPUT"], relief="flat", bd=0,
            padx=18, pady=8, cursor="hand2",
            command=d.destroy).pack(pady=14)

    # ── settings window ──────────────────────────────────────────────────────
    def _open_settings(self):
        P  = self.P
        tr = self.tr
        d  = tk.Toplevel(self)
        d.title(f"{tr['title']} – {tr['settings_title']}")
        d.configure(bg=P["BG2"])
        d.resizable(False, False)
        W2, H2 = 460, 660
        cx = self.winfo_x() + (self.winfo_width()  - W2) // 2
        cy = self.winfo_y() + (self.winfo_height() - H2) // 2
        d.geometry(f"{W2}x{H2}+{cx}+{cy}")
        d.grab_set()
        set_window_icon(d)

        tk.Label(d, text=tr["settings_title"],
            font=F(13, "bold"), bg=P["BG2"], fg=P["FG"]
            ).pack(anchor="w", padx=24, pady=(20,14))

        def sep():
            tk.Frame(d, bg=P["BORDER"], height=1).pack(fill="x", padx=24, pady=8)

        def section(text):
            tk.Label(d, text=text,
                font=F(8, "bold"), bg=P["BG2"], fg=P["MUTED"]
                ).pack(anchor="w", padx=24, pady=(4,4))

        # ── theme color ─────────────────────────────────────────────────────
        section(tr["settings_theme_color"])
        color_row = tk.Frame(d, bg=P["BG2"])
        color_row.pack(padx=24, fill="x")
        sel_color = tk.StringVar(value=self.cfg["theme_color"])

        swatches = {}
        def pick_color(hx):
            sel_color.set(hx)
            for h, b in swatches.items():
                active = (h == hx)
                b.config(relief="solid" if active else "flat",
                         bd=2 if active else 0,
                         highlightbackground=P["FG"] if active else P["BG2"])
        for hx, name in self.THEME_PRESETS:
            b = tk.Button(color_row, bg=hx, width=3, height=1,
                relief="solid" if hx==sel_color.get() else "flat",
                bd=2 if hx==sel_color.get() else 0,
                highlightbackground=P["FG"] if hx==sel_color.get() else P["BG2"],
                highlightthickness=1, cursor="hand2",
                command=lambda h=hx: pick_color(h))
            b.pack(side="left", padx=3)
            swatches[hx] = b

        sep()

        # ── app theme ────────────────────────────────────────────────────────
        section(tr["settings_app_theme"])
        theme_row = tk.Frame(d, bg=P["BG2"])
        theme_row.pack(padx=24, fill="x")
        sel_theme = tk.StringVar(value=self.cfg.get("app_theme","oled"))

        theme_btns = {}
        def pick_theme(t):
            sel_theme.set(t)
            for tv, tb in theme_btns.items():
                active = (tv == t)
                tb.config(bg=self.ACC_BG if active else P["BTN"],
                          fg=P["FG"] if active else P["MUTED"],
                          relief="flat")
        for t_key, t_val in [("theme_oled","oled"),("theme_dark","dark"),("theme_light","light")]:
            tb = tk.Button(theme_row, text=tr[t_key],
                font=F(9, "bold"),
                bg=self.ACC_BG if t_val==sel_theme.get() else P["BTN"],
                fg=P["FG"] if t_val==sel_theme.get() else P["MUTED"],
                activebackground=P["INPUT"], activeforeground=P["FG"],
                relief="flat", bd=0, padx=18, pady=7,
                cursor="hand2", command=lambda t=t_val: pick_theme(t))
            tb.pack(side="left", padx=(0,4))
            theme_btns[t_val] = tb

        sep()

        # ── language ─────────────────────────────────────────────────────────
        section(tr["settings_language"])
        lang_row = tk.Frame(d, bg=P["BG2"])
        lang_row.pack(padx=24, fill="x")
        langs = get_available_langs()
        sel_lang = tk.StringVar(value=self.cfg.get("language","en"))
        lang_combo = ttk.Combobox(lang_row, textvariable=sel_lang,
            values=langs, state="readonly", font=F(10), width=10)
        lang_combo.pack(side="left")
        tk.Label(lang_row, text="  ← put tr.ini / fr.ini etc. next to oxygen.py",
            font=F(8), bg=P["BG2"], fg=P["MUTED"]).pack(side="left")

        sep()

        # ── download location ────────────────────────────────────────────────
        section(tr["settings_download_loc"])
        dir_row = tk.Frame(d, bg=P["BG2"])
        dir_row.pack(padx=24, fill="x")
        dir_var = tk.StringVar(value=self.cfg["download_dir"])
        tk.Entry(dir_row, textvariable=dir_var,
            bg=P["INPUT"], fg=P["FG2"],
            relief="flat", font=F(9),
            highlightthickness=1, highlightbackground=P["BORDER"],
            insertbackground=P["FG"], bd=0
            ).pack(side="left", fill="x", expand=True, ipady=5, padx=(0,8))

        def browse():
            p = filedialog.askdirectory(initialdir=dir_var.get())
            if p: dir_var.set(p)

        tk.Button(dir_row, text=tr["settings_browse"],
            font=F(9), bg=P["BTN"], fg=P["FG2"],
            activebackground=P["INPUT"], relief="flat", bd=0,
            padx=10, pady=5, cursor="hand2",
            command=browse).pack(side="left")

        sep()

        # ── auto-paste toggle ────────────────────────────────────────────────
        section(tr["settings_clipboard"])
        ap_row = tk.Frame(d, bg=P["BG2"])
        ap_row.pack(padx=24, fill="x")
        tk.Label(ap_row, text=tr["settings_auto_paste_lbl"],
            font=F(10), bg=P["BG2"], fg=P["FG2"]).pack(side="left")

        ap_var = tk.BooleanVar(value=self.cfg.get("auto_paste",True))
        def toggle_ap():
            ap_var.set(not ap_var.get())
            v = ap_var.get()
            ap_cb.config(bg=self.ACC if v else P["BTN"],
                         fg=acc_fg(self.ACC) if v else P["MUTED"],
                         text=tr["toggle_on"] if v else tr["toggle_off"])
        ap_cb = tk.Button(ap_row,
            text=tr["toggle_on"] if ap_var.get() else tr["toggle_off"],
            font=F(8, "bold"),
            bg=self.ACC if ap_var.get() else P["BTN"],
            fg=acc_fg(self.ACC) if ap_var.get() else P["MUTED"],
            activebackground=P["INPUT"],
            relief="flat", bd=0, padx=12, pady=4,
            cursor="hand2", command=toggle_ap)
        ap_cb.pack(side="right")

        sep()

        # ── cookie browser (fixes YouTube 403) ──────────────────────────────
        section("YOUTUBE / COOKIE BYPASS")
        ck_row = tk.Frame(d, bg=P["BG2"])
        ck_row.pack(padx=24, fill="x")
        tk.Label(ck_row, text="Browser cookies (fixes 403 errors):",
            font=F(9), bg=P["BG2"], fg=P["FG2"]).pack(side="left", padx=(0,8))

        BROWSERS = ["none", "chrome", "firefox", "edge", "brave", "opera", "chromium", "vivaldi"]
        sel_browser = tk.StringVar(value=self.cfg.get("cookie_browser", "none"))
        ck_combo = ttk.Combobox(ck_row, textvariable=sel_browser,
            values=BROWSERS, state="readonly", font=F(9), width=10, style="Q.TCombobox")
        ck_combo.pack(side="left")

        tk.Label(ck_row, text="  ← pick your browser",
            font=F(8), bg=P["BG2"], fg=P["MUTED"]).pack(side="left")

        # cookies.txt (most reliable, works even when browser is open)
        cf_frame = tk.Frame(d, bg=P["BG2"])
        cf_frame.pack(padx=24, pady=(6,0), fill="x")
        tk.Label(cf_frame, text="Or use cookies.txt file (most reliable):",
            font=F(9), bg=P["BG2"], fg=P["FG2"]).pack(anchor="w")

        cf_row2 = tk.Frame(d, bg=P["BG2"])
        cf_row2.pack(padx=24, pady=(2,0), fill="x")
        cookie_file_var = tk.StringVar(value=self.cfg.get("cookie_file", ""))
        tk.Entry(cf_row2, textvariable=cookie_file_var,
            bg=P["INPUT"], fg=P["FG2"], relief="flat", font=F(8),
            highlightthickness=1, highlightbackground=P["BORDER"],
            insertbackground=P["FG"], bd=0
            ).pack(side="left", fill="x", expand=True, ipady=4, padx=(0,6))

        def browse_cookie():
            p = filedialog.askopenfilename(
                title="Select cookies.txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if p:
                cookie_file_var.set(p)
                sel_browser.set("none")

        tk.Button(cf_row2, text="Browse", font=F(8),
            bg=P["BTN"], fg=P["FG2"],
            activebackground=P["INPUT"], relief="flat", bd=0,
            padx=8, pady=4, cursor="hand2",
            command=browse_cookie).pack(side="left")

        tk.Label(d, text="  Tip: chrome://net-export or EditThisCookie ext → export Netscape format",
            font=F(7), bg=P["BG2"], fg=P["MUTED"], anchor="w"
            ).pack(padx=24, anchor="w")

        # ── save / cancel ────────────────────────────────────────────────────
        tk.Frame(d, bg=P["BORDER"], height=1).pack(fill="x", padx=24, pady=(14,0))
        btns = tk.Frame(d, bg=P["BG2"])
        btns.pack(pady=14)

        def apply_save():
            self.cfg["theme_color"]    = sel_color.get()
            self.cfg["app_theme"]      = sel_theme.get()
            self.cfg["language"]       = sel_lang.get()
            self.cfg["download_dir"]   = dir_var.get()
            self.cfg["auto_paste"]     = ap_var.get()
            self.cfg["cookie_browser"] = sel_browser.get()
            self.cfg["cookie_file"]    = cookie_file_var.get().strip()
            save_cfg(self.cfg)
            self.tr   = load_lang(self.cfg["language"])
            self._pal = PALETTES[self.cfg["app_theme"]]
            self._apply_theme()
            d.destroy()
            self._log(f"{self.tr['settings_saved_log']}  ·  {sel_color.get()}")

        tk.Button(btns, text=tr["settings_cancel"],
            font=F(10), bg=P["BTN"], fg=P["FG2"],
            activebackground=P["INPUT"], relief="flat", bd=0,
            padx=18, pady=8, cursor="hand2",
            command=d.destroy).pack(side="left", padx=6)

        tk.Button(btns, text=tr["settings_save"],
            font=F(10, "bold"),
            bg=self.ACC, fg=self.ACC_FG,
            activebackground=self.ACC_D, activeforeground=self.ACC_FG,
            relief="flat", bd=0, padx=22, pady=8,
            cursor="hand2", command=apply_save).pack(side="left", padx=6)

    # ── apply theme after settings save ──────────────────────────────────────
    def _apply_theme(self):
        P  = self.P
        tr = self.tr
        self.configure(bg=P["BG"])

        self._top_frame.config(bg=P["BG"])
        self._lbl_title.config(bg=P["BG"], fg=P["FG"])
        self._lbl_sub.config(bg=P["BG"], fg=P["MUTED"])
        self._gear_btn.config(bg=P["BG"], fg=P["MUTED"],
                               activebackground=P["BG"], activeforeground=P["FG"])
        self._about_btn.config(bg=P["BG"], fg=P["MUTED"],
                                activebackground=P["BG"], activeforeground=P["FG"])
        for child in self._top_frame.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(bg=P["BG"])

        self._load_logo()

        self._inp_wrap.config(bg=P["BG"])
        self._inp_c.config(bg=P["BG"])
        self._draw_inp()
        self._inp_c.itemconfig("icon", fill=P["MUTED"])
        self.url_entry.config(bg=P["INPUT"], fg=P["FG"], insertbackground=P["FG"])
        self._set_placeholder()

        self._ctrl_frame.config(bg=P["BG"])
        self._mode_frame.config(bg=P["BTN"], highlightbackground=P["BORDER"])
        for v, b in self._mbtn.items():
            lbl = tr[{"auto":"mode_auto","audio":"mode_audio","mute":"mode_mute"}[v]]
            b.config(text=lbl, bg=P["BTN"], fg=P["MUTED"],
                     activebackground=P["INPUT"], activeforeground=P["FG"])
        self._mode_frame.config(bg=P["BTN"], highlightbackground=P["BORDER"])
        self._set_mode(self.mode.get())

        if self._playlist_on:
            self._playlist_btn.config(text=tr["playlist_toggle"],
                bg=self.ACC_BG, fg=P["FG"], activebackground=P["INPUT"],
                highlightbackground=P["BORDER"])
        else:
            self._playlist_btn.config(text=tr["playlist_toggle"],
                bg=P["BTN"], fg=P["MUTED"], activebackground=P["INPUT"],
                highlightbackground=P["BORDER"])

        self._paste_btn.config(text=tr["btn_paste"],
            bg=P["BTN"], fg=P["FG"], activebackground=P["INPUT"],
            highlightbackground=P["BORDER"])

        # quality row background
        self._qrow.config(bg=P["BG"])
        for frame in [self._res_frame, self._vfmt_frame, self._aq_frame, self._afmt_frame]:
            frame.config(bg=P["BG"])
            for child in frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=P["BG"], fg=P["MUTED"])
        self._apply_combo_style()

        self.dl_btn.config(text=tr["btn_download"],
            bg=self.ACC, fg=self.ACC_FG,
            activebackground=self.ACC_D, activeforeground=self.ACC_FG)

        s = ttk.Style(self)
        s.configure("O.Horizontal.TProgressbar",
            troughcolor=P["INPUT"], background=self.ACC)

        self._log_frame.config(bg=P["LOG_BG"], highlightbackground=P["BORDER"])
        self.log_box.config(bg=P["LOG_BG"], fg=P["LOG_FG"])
        self._log_sb.config(bg=P["LOG_BG"], troughcolor=P["LOG_BG"],
                             activebackground=P["BORDER"])
        self._log_toggle_bar.config(bg=P["BG"])
        self._bottom_spacer.config(bg=P["BG"])
        vis_fg = P["FG2"] if self._log_visible else P["MUTED"]
        self._log_toggle_btn.config(
            bg=P["BG"], fg=vis_fg,
            activebackground=P["BG"], activeforeground=P["FG"])

# ─── entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = Oxygen()
    app.mainloop()
