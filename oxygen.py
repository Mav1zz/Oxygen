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
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
    EXE_DIR  = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR  = BASE_DIR

CFG_PATH  = os.path.join(os.path.expanduser("~"), ".oxygen_cfg.json")
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
        "BG2":     "#050505",
        "INPUT":   "#0a0a0a",
        "BORDER":  "#1c1c1c",
        "FG":      "#ffffff",
        "FG2":     "#aaaaaa",
        "MUTED":   "#404040",
        "LOG_BG":  "#050505",
        "LOG_FG":  "#555555",
        "BTN":     "#0e0e0e",
    },
    "dark": {
        "BG":      "#111111",
        "BG2":     "#0d0d0d",
        "INPUT":   "#1c1c1c",
        "BORDER":  "#2e2e2e",
        "FG":      "#f0f0f0",
        "FG2":     "#bbbbbb",
        "MUTED":   "#555555",
        "LOG_BG":  "#161616",
        "LOG_FG":  "#666666",
        "BTN":     "#1e1e1e",
    },
    "light": {
        "BG":      "#f2f2f2",
        "BG2":     "#e8e8e8",
        "INPUT":   "#ffffff",
        "BORDER":  "#c8c8c8",
        "FG":      "#111111",
        "FG2":     "#444444",
        "MUTED":   "#888888",
        "LOG_BG":  "#f8f8f8",
        "LOG_FG":  "#555555",
        "BTN":     "#dcdcdc",
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
    "theme_color":  "#7c3aed",
    "app_theme":    "oled",
    "language":     "en",
    "download_dir": _default_downloads(),
    "auto_paste":   True,
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
def _pip_install(pkg):
    cmd = [sys.executable, "-m", "pip", "install", pkg, "-q"]
    if platform.system() != "Windows":
        cmd.append("--break-system-packages")
    subprocess.check_call(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

def ensure_deps(log_cb, tr):
    for pkg, import_name, key_ok in [
        ("yt-dlp",  "yt_dlp", "pkg_ytdlp_ok"),
        ("Pillow",  "PIL",    "pkg_pillow_ok"),
    ]:
        try:
            __import__(import_name)
        except ImportError:
            log_cb(f"📦 installing {pkg}…")
            _pip_install(pkg)
            log_cb(tr[key_ok])

    _ffmpeg_name = "ffmpeg.exe" if _SYS == "Windows" else "ffmpeg"

    _local_ffmpeg = os.path.join(EXE_DIR, _ffmpeg_name)
    if os.path.isfile(_local_ffmpeg):
        os.environ["PATH"] = EXE_DIR + os.pathsep + os.environ.get("PATH", "")
        log_cb(tr.get("pkg_ffmpeg_local", "✓ ffmpeg found in app folder"))
        return

    if BASE_DIR != EXE_DIR:
        _meipass_ffmpeg = os.path.join(BASE_DIR, _ffmpeg_name)
        if os.path.isfile(_meipass_ffmpeg):
            os.environ["PATH"] = BASE_DIR + os.pathsep + os.environ.get("PATH", "")
            log_cb(tr.get("pkg_ffmpeg_local", "✓ ffmpeg found (bundled)"))
            return

    if shutil.which("ffmpeg"):
        log_cb(tr.get("pkg_ffmpeg_ok", "✓ ffmpeg ready"))
        return

    log_cb(tr["pkg_ffmpeg"])
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

def acc_bg(acc, alpha=0.18):
    h = acc.lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
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
    def ACC_BG(self): return acc_bg(self.ACC)
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

        # ── log box ───────────────────────────────────────────────────────────
        self._log_frame = tk.Frame(self, bg=P["LOG_BG"],
            highlightbackground=P["BORDER"], highlightthickness=1)
        self._log_frame.pack(padx=50, pady=(10,16), fill="both", expand=True)

        self.log_box = tk.Text(self._log_frame, bg=P["LOG_BG"], fg=P["LOG_FG"],
            font=FM(9), relief="flat", bd=0,
            state="disabled", wrap="word", height=5)
        self._log_sb = tk.Scrollbar(self._log_frame, command=self.log_box.yview,
            bg=P["LOG_BG"], troughcolor=P["LOG_BG"],
            activebackground=P["BORDER"], relief="flat")
        self.log_box.config(yscrollcommand=self._log_sb.set)
        self.log_box.pack(side="left", fill="both", expand=True, padx=8, pady=5)
        self._log_sb.pack(side="right", fill="y")

        self._log(tr["status_ready"])

    # ── combo style ──────────────────────────────────────────────────────────
    def _apply_combo_style(self):
        P = self.P
        style = ttk.Style(self)
        style.configure("Q.TCombobox",
            fieldbackground=P["INPUT"],
            background=P["BTN"],
            foreground=P["FG2"],
            selectbackground=P["INPUT"],
            selectforeground=P["FG"],
            arrowcolor=P["MUTED"])
        style.map("Q.TCombobox",
            fieldbackground=[("readonly", P["INPUT"])],
            foreground=[("readonly", P["FG2"])])

    # ── quality visibility per mode ──────────────────────────────────────────
    def _update_quality_visibility(self, mode):
        """Show/hide format controls based on the active download mode."""
        for f in [self._res_frame, self._vfmt_frame, self._aq_frame, self._afmt_frame]:
            f.pack_forget()

        if mode == "audio":
            self._aq_frame.pack(side="left", padx=(0, 6))
            self._afmt_frame.pack(side="left")
        elif mode == "mute":
            self._res_frame.pack(side="left", padx=(0, 6))
            self._vfmt_frame.pack(side="left")
        else:
            self._res_frame.pack(side="left", padx=(0, 6))
            self._vfmt_frame.pack(side="left")

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
                b.config(bg=self.ACC_BG, fg=P["FG"])
            else:
                b.config(bg=P["BTN"], fg=P["MUTED"])
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
            import yt_dlp
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

            opts = {
                "outtmpl":         os.path.join(out_dir, "%(title)s.%(ext)s"),
                "progress_hooks":  [hook],
                "quiet":           True,
                "no_warnings":     True,
                "ignoreerrors":    True,
            }

            # ── playlist ──────────────────────────────────────────────────
            if self._playlist_on:
                opts["noplaylist"] = False
                opts["outtmpl"] = os.path.join(
                    out_dir,
                    "%(playlist_title|Playlist)s",
                    "%(playlist_index|0)03d - %(title)s.%(ext)s")

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
                # ── audio only ──
                aq_num = aq.rstrip("k") if aq != "best" else "0"  # 0 = VBR best
                opts["format"] = "bestaudio/best"
                opts["postprocessors"] = [{
                    "key":              "FFmpegExtractAudio",
                    "preferredcodec":   afmt,
                    "preferredquality": aq_num,
                }]

            elif mode == "mute":
                # ── video only, no audio ──
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

            else:
                # ── auto: best video + audio ──
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

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            if self._playlist_on and len(saved) > 1:
                self._log(self.tr["playlist_done"].format(count=len(saved)))

            final = saved[-1] if saved else None
            self.after(0, self._on_done, True, final, out_dir)
        except Exception as e:
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
        self._log(self.tr["status_ready"].split("·")[0].strip())
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
        W2, H2 = 440, 490
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

        # ── save / cancel ────────────────────────────────────────────────────
        tk.Frame(d, bg=P["BORDER"], height=1).pack(fill="x", padx=24, pady=(14,0))
        btns = tk.Frame(d, bg=P["BG2"])
        btns.pack(pady=14)

        def apply_save():
            self.cfg["theme_color"]  = sel_color.get()
            self.cfg["app_theme"]    = sel_theme.get()
            self.cfg["language"]     = sel_lang.get()
            self.cfg["download_dir"] = dir_var.get()
            self.cfg["auto_paste"]   = ap_var.get()
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

# ─── entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = Oxygen()
    app.mainloop()
