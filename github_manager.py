"""
Oxygen GitHub Manager  –  v3.0
Pure Python TUI: push files, browse repo, delete files, manage settings.
Run with:  python github_manager.py
"""

import sys, os, json, subprocess, urllib.request, urllib.error
import urllib.parse, shutil, threading, time, textwrap

# ═══════════════════════════════════════════════════════════════════════════════
# WINDOWS ANSI + INPUT
# ═══════════════════════════════════════════════════════════════════════════════
if sys.platform == "win32":
    import ctypes, msvcrt
    ctypes.windll.kernel32.SetConsoleMode(
        ctypes.windll.kernel32.GetStdHandle(-11), 7)
    import winreg as _winreg
else:
    import tty, termios, select

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS / ANSI
# ═══════════════════════════════════════════════════════════════════════════════
R  = "\033[0m"
B  = "\033[1m"
DM = "\033[2m"

def fg(r,g,b): return f"\033[38;2;{r};{g};{b}m"
def bg(r,g,b): return f"\033[48;2;{r};{g};{b}m"

C = {
    "bg":       bg(10, 10, 12),
    "bg2":      bg(18, 16, 28),
    "bgsel":    bg(45, 25, 85),
    "title":    fg(160, 90, 255),
    "accent":   fg(130, 70, 220),
    "fg":       fg(230, 230, 235),
    "muted":    fg(100, 100, 115),
    "border":   fg(55, 45, 75),
    "green":    fg(60, 210, 110),
    "yellow":   fg(240, 175, 50),
    "red":      fg(220, 65, 65),
    "blue":     fg(90, 165, 255),
    "white":    fg(255, 255, 255),
    "check":    fg(75, 220, 130),
    "uncheck":  fg(65, 65, 80),
    "file":     fg(195, 190, 220),
    "dir":      fg(100, 165, 255),
    "size":     fg(90, 90, 105),
}

def clr():  print("\033[2J\033[H", end="", flush=True)
def mv(r,c): print(f"\033[{r};{c}H", end="", flush=True)
def hide(): print("\033[?25l", end="", flush=True)
def show(): print("\033[?25h", end="", flush=True)

def tsz():
    try:
        s = shutil.get_terminal_size()
        return s.lines, s.columns
    except Exception:
        return 30, 80

# ═══════════════════════════════════════════════════════════════════════════════
# KEY INPUT
# ═══════════════════════════════════════════════════════════════════════════════
UP    = "UP"
DOWN  = "DOWN"
LEFT  = "LEFT"
RIGHT = "RIGHT"
ENTER = "ENTER"
SPACE = "SPACE"
ESC   = "ESC"
TAB   = "TAB"
BKSP  = "BKSP"
DEL   = "DEL"
PGUP  = "PGUP"
PGDN  = "PGDN"
HOME  = "HOME"
END   = "END"

def getch():
    if sys.platform == "win32":
        ch = msvcrt.getwch()
        if ch in ('\x00', '\xe0'):
            ch2 = msvcrt.getwch()
            return {
                'H': UP, 'P': DOWN, 'K': LEFT, 'M': RIGHT,
                'S': DEL, 'I': PGUP, 'Q': PGDN,
                'G': HOME, 'O': END,
            }.get(ch2, ch2)
        if ch == '\r':   return ENTER
        if ch == ' ':    return SPACE
        if ch == '\x1b': return ESC
        if ch == '\t':   return TAB
        if ch in ('\x08', '\x7f'): return BKSP
        return ch
    else:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if r:
                    seq = sys.stdin.read(2)
                    return {
                        '[A': UP, '[B': DOWN, '[C': RIGHT, '[D': LEFT,
                        '[3': DEL, '[5': PGUP, '[6': PGDN,
                        '[H': HOME, '[F': END,
                        'OH': HOME, 'OF': END,
                    }.get(seq.rstrip('~'), ESC)
                return ESC
            if ch in ('\r','\n'): return ENTER
            if ch == ' ':        return SPACE
            if ch == '\t':       return TAB
            if ch in ('\x08','\x7f'): return BKSP
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ═══════════════════════════════════════════════════════════════════════════════
# DRAW PRIMITIVES
# ═══════════════════════════════════════════════════════════════════════════════
def cut(s, n):
    """Truncate string to n chars with ellipsis."""
    return s if len(s) <= n else s[:n-1] + "…"

def pad(s, n, align="left"):
    s = cut(s, n)
    if align == "center": return s.center(n)
    if align == "right":  return s.rjust(n)
    return s.ljust(n)

def hline(row, col, w, ch="─"):
    mv(row, col)
    print(C["border"] + ch * w + R, end="", flush=True)

def box(row, col, w, h, title=""):
    """Draw a box. Returns inner (row, col, w, h)."""
    tl,tr,bl,br,hz,vt = "┌","┐","└","┘","─","│"
    top = tl + hz*(w-2) + tr
    if title:
        t = f" {title} "
        pos = (w - len(t)) // 2
        top = tl + hz*pos + t + hz*(w-2-pos-len(t)) + tr
    mv(row, col);   print(C["border"] + top + R, end="", flush=True)
    for r in range(1, h-1):
        mv(row+r, col)
        print(C["border"] + vt + " "*(w-2) + vt + R, end="", flush=True)
    mv(row+h-1, col)
    print(C["border"] + bl + hz*(w-2) + br + R, end="", flush=True)
    return row+1, col+1, w-2, h-2

def box_line(row, col, w, text, color="", align="left"):
    """Write a line inside a box (handles the border chars)."""
    mv(row, col)
    inner = w - 2
    content = color + pad(text, inner, align) + R
    print(C["border"] + "│" + R + " " + content + " " + C["border"] + "│" + R,
          end="", flush=True)

def print_at(row, col, text, color=""):
    mv(row, col)
    print(color + text + R, end="", flush=True)

def human_size(b):
    if not b: return ""
    for u in ("B","KB","MB","GB"):
        if b < 1024: return f"{b:.0f}{u}"
        b /= 1024
    return f"{b:.1f}GB"

def loading_spin(msg, fn, args=()):
    """Run fn(*args) in background, show spinner. Returns result."""
    result = [None]; error = [None]; done = [False]
    def worker():
        try:    result[0] = fn(*args)
        except Exception as e: error[0] = e
        finally: done[0] = True

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    i = 0
    hide()
    rows, cols = tsz()
    r, c = rows//2, (cols - len(msg) - 3) // 2
    while not done[0]:
        mv(r, c)
        print(C["accent"] + frames[i % len(frames)] + " " + C["muted"] + msg + R + "   ",
              end="", flush=True)
        time.sleep(0.08)
        i += 1
    mv(r, c); print(" " * (len(msg) + 5), end="", flush=True)
    show()
    if error[0]: raise error[0]
    return result[0]

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
def app_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME",
                              os.path.join(os.path.expanduser("~"), ".config"))
    d = os.path.join(base, "Oxygen")
    os.makedirs(d, exist_ok=True)
    return d

CFG = os.path.join(app_dir(), "github_manager.json")

def load_cfg():
    try:
        with open(CFG) as f: return json.load(f)
    except Exception: return {}

def save_cfg(d):
    try:
        with open(CFG, "w") as f: json.dump(d, f, indent=2)
    except Exception: pass

# ═══════════════════════════════════════════════════════════════════════════════
# GITHUB API
# ═══════════════════════════════════════════════════════════════════════════════
def _req(token, path, method="GET", body=None):
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"token {token}",
        "Accept":        "application/vnd.github.v3+json",
        "User-Agent":    "Oxygen-Manager/3.0",
        "Content-Type":  "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode(errors="ignore")
        try:
            msg = json.loads(body_txt).get("message", body_txt)
        except Exception:
            msg = body_txt[:120]
        raise RuntimeError(f"HTTP {e.code}: {msg}")

def gh_repo(token, owner, repo):
    return _req(token, f"/repos/{owner}/{repo}")

def gh_branches(token, owner, repo):
    data = _req(token, f"/repos/{owner}/{repo}/branches")
    return [b["name"] for b in data]

def gh_tree(token, owner, repo, branch):
    data = _req(token, f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
    return [
        {"path": i["path"], "sha": i["sha"],
         "type": i["type"], "size": i.get("size", 0)}
        for i in data.get("tree", [])
        if i["type"] in ("blob", "tree")
    ]

def gh_contents_sha(token, owner, repo, path):
    """Fetch the current blob SHA for a file via Contents API (required for delete)."""
    data = _req(token, f"/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}")
    if isinstance(data, list):
        # It's a directory — shouldn't happen for blobs
        raise RuntimeError(f"Path is a directory, not a file: {path}")
    return data["sha"]

def gh_delete(token, owner, repo, path, sha, msg="Remove via Oxygen Manager"):
    """Delete a file. sha must be the blob SHA from Contents API."""
    encoded = urllib.parse.quote(path, safe="")
    return _req(token, f"/repos/{owner}/{repo}/contents/{encoded}",
                method="DELETE", body={"message": msg, "sha": sha})

def _403_hint(err_str):
    """Return a helpful hint for 403 errors."""
    if "403" in err_str or "accessible by personal access token" in err_str:
        return (
            "Token permission error. Fix:",
            "  Classic PAT → needs 'repo' scope (full)",
            "  Fine-grained PAT → needs 'Contents: Read & Write'",
            "  Go to: github.com/settings/tokens",
        )
    return None

def parse_url(url):
    url = url.strip().rstrip("/").removesuffix(".git")
    parts = url.split("/")
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    return "", ""

def git_remote():
    try:
        return subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""

# ═══════════════════════════════════════════════════════════════════════════════
# INPUT WIDGET
# ═══════════════════════════════════════════════════════════════════════════════
def input_field(row, col, width, default="", password=False, label=""):
    """Inline text input. Returns entered string."""
    if label:
        mv(row, col)
        print(C["muted"] + label + R, end="", flush=True)
        col += len(label)
        width -= len(label)

    buf = list(default)

    def redraw():
        mv(row, col)
        disp = "".join("*" if password else c for c in buf)
        disp = disp[-(width-1):]  # scroll right
        print(C["fg"] + disp.ljust(width-1) + C["accent"] + "█" + R,
              end="", flush=True)

    show()
    redraw()
    while True:
        k = getch()
        if k == ENTER:
            break
        elif k == ESC:
            buf = list(default)
            break
        elif k == BKSP and buf:
            buf.pop()
            redraw()
        elif k in (LEFT, RIGHT, UP, DOWN, TAB):
            break
        elif isinstance(k, str) and len(k) == 1 and k.isprintable():
            buf.append(k)
            redraw()
    hide()
    # Clear cursor
    mv(row, col)
    val = "".join(buf)
    disp = "".join("*" if password else c for c in buf)
    disp = disp[-(width-1):]
    print(C["fg"] + disp.ljust(width) + R, end="", flush=True)
    return val, k  # return value AND the key that ended input

def dialog_input(row, col, w, h, title, fields):
    """
    Multi-field dialog.
    fields = list of {"label": str, "key": str, "default": str, "password": bool}
    Returns dict of values, or None if ESCed.
    """
    box(row, col, w, h, title)
    values = {f["key"]: f.get("default", "") for f in fields}
    idx = 0

    while True:
        # Draw all fields
        for i, f in enumerate(fields):
            r = row + 2 + i * 2
            active = (i == idx)
            lbl = f["label"].ljust(14)
            mv(r, col + 2)
            bcol = C["accent"] if active else C["muted"]
            print(bcol + ("▶ " if active else "  ") + C["muted"] + lbl + R, end="", flush=True)
            mv(r, col + 18)
            val = values[f["key"]]
            disp = "*" * len(val) if f.get("password") else val
            disp = cut(disp, w - 20)
            bkg = C["bgsel"] if active else ""
            print(bkg + C["fg"] + disp.ljust(w - 20) + R, end="", flush=True)

        # Hint line
        mv(row + h - 2, col + 2)
        print(C["muted"] + "Tab/↑↓ navigate   Enter confirm   Esc cancel" + R,
              end="", flush=True)

        # Edit active field
        r = row + 2 + idx * 2
        mv(r, col + 18)
        val, last_key = input_field(r, col + 18, w - 19,
                                    default=values[fields[idx]["key"]],
                                    password=fields[idx].get("password", False))
        values[fields[idx]["key"]] = val

        if last_key == ESC:
            return None
        elif last_key in (ENTER, DOWN, TAB):
            idx = (idx + 1) % len(fields)
            if last_key == ENTER and idx == 0:
                return values
        elif last_key == UP:
            idx = (idx - 1) % len(fields)

# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION / CONFIRM
# ═══════════════════════════════════════════════════════════════════════════════
def notify(title, lines, color=None, wait=True):
    rows, cols = tsz()
    w = min(64, cols - 4)
    h = len(lines) + 4
    r = (rows - h) // 2
    c = (cols - w) // 2
    color = color or C["fg"]

    hide()
    box(r, c, w, h, title)
    for i, line in enumerate(lines):
        mv(r + 1 + i, c + 1)
        print(" " + color + cut(line, w-4) + R + " " * (w-4-len(cut(line,w-4))),
              end="", flush=True)
    if wait:
        mv(r + h - 2, c + 1)
        print(" " + C["muted"] + "Press any key to continue…" + R,
              end="", flush=True)
        show()
        getch()
        hide()

def confirm(title, lines, yes="Y", no="N"):
    rows, cols = tsz()
    w = min(66, cols - 4)
    h = len(lines) + 5
    r = (rows - h) // 2
    c = (cols - w) // 2

    hide()
    box(r, c, w, h, title)
    for i, line in enumerate(lines):
        mv(r + 1 + i, c + 1)
        print(" " + C["yellow"] + cut(line, w-4) + R, end="", flush=True)

    mv(r + h - 2, c + 1)
    print(" " + C["muted"] + f"[{yes}] Confirm   [{no}] Cancel" + R,
          end="", flush=True)
    show()
    while True:
        k = getch()
        if k.upper() == yes.upper(): return True
        if k.upper() == no.upper() or k == ESC: return False

def status_bar(rows, cols, msg, color=None):
    color = color or C["muted"]
    mv(rows, 1)
    print(color + " " + cut(msg, cols - 2) + R + " " * max(0, cols - len(msg) - 2),
          end="", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SETUP / LOGIN SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
def screen_setup():
    saved = load_cfg()
    remote = git_remote()
    o_def, r_def = parse_url(remote)

    while True:
        rows, cols = tsz()
        w = min(68, cols - 4)
        h = 26
        r = max(1, (rows - h) // 2)
        c = (cols - w) // 2

        clr()
        hide()

        # Logo area
        box(r, c, w, h, " Oxygen  GitHub Manager ")

        # Big logo
        logo = [
            "   ⊙  OXYGEN",
            "   GitHub Manager  v3.0",
        ]
        for i, line in enumerate(logo):
            mv(r + 1 + i, c + 1)
            col = C["title"] + B if i == 0 else C["muted"]
            print(" " + col + pad(line, w-4, "center") + R, end="", flush=True)

        mv(r + 4, c + 1)
        print(" " + C["border"] + "─"*(w-2) + R, end="", flush=True)

        mv(r + 5, c + 1)
        print(" " + C["muted"] + pad("GitHub Personal Access Token needed", w-4, "center") + R,
              end="", flush=True)
        mv(r + 6, c + 1)
        print(" " + C["muted"] + pad("github.com → Settings → Developer settings → PAT", w-4, "center") + R,
              end="", flush=True)
        mv(r + 7, c + 1)
        print(" " + C["muted"] + pad("Required scope:  repo", w-4, "center") + R,
              end="", flush=True)

        mv(r + 8, c + 1)
        print(" " + C["border"] + "─"*(w-2) + R, end="", flush=True)

        # Try to read existing git user config as defaults
        def _git_cfg(key):
            try:
                return subprocess.check_output(
                    ["git", "config", "--global", key],
                    stderr=subprocess.DEVNULL, text=True).strip()
            except Exception:
                return ""

        fields = [
            {"label": "Token",  "key": "token",      "default": saved.get("token",""),                    "password": True},
            {"label": "Owner",  "key": "owner",      "default": saved.get("owner", o_def or ""),           "password": False},
            {"label": "Repo",   "key": "repo",       "default": saved.get("repo",  r_def or ""),           "password": False},
            {"label": "Branch", "key": "branch",     "default": saved.get("branch","main"),                "password": False},
            {"label": "Email",  "key": "git_email",  "default": saved.get("git_email", _git_cfg("user.email")), "password": False},
            {"label": "Name",   "key": "git_name",   "default": saved.get("git_name",  _git_cfg("user.name")),  "password": False},
        ]

        idx = 0
        values = {f["key"]: f["default"] for f in fields}

        def draw_fields():
            for i, f in enumerate(fields):
                row_f = r + 10 + i * 2
                active = (i == idx)
                mv(row_f, c + 2)
                bcol = C["accent"] if active else C["muted"]
                lbl = f["label"].ljust(9)
                val = values[f["key"]]
                disp = "*"*len(val) if f.get("password") else val
                disp = cut(disp, w - 18)
                bkg = C["bgsel"] if active else ""
                print(bcol + ("▶ " if active else "  ") + C["muted"] + lbl + " " +
                      bkg + C["fg"] + disp.ljust(w-18) + R, end="", flush=True)

        draw_fields()

        mv(r + h - 3, c + 1)
        print(" " + C["muted"] + pad("Tab/↓ next field   Enter connect   Esc quit", w-4, "center") + R,
              end="", flush=True)

        mv(r + h - 2, c + 1)
        print(" " + C["border"] + "─"*(w-2) + R, end="", flush=True)

        # Field editing loop
        editing = True
        error_msg = ""
        while editing:
            draw_fields()
            if error_msg:
                mv(r + h - 1, c + 1)
                print(" " + C["red"] + cut(error_msg, w-4) + R, end="", flush=True)

            f = fields[idx]
            row_f = r + 10 + idx * 2
            val, last = input_field(row_f, c + 13, w - 14,
                                    default=values[f["key"]],
                                    password=f.get("password", False))
            values[f["key"]] = val

            if last == ESC:
                clr(); show()
                return None
            elif last in (DOWN, TAB):
                idx = (idx + 1) % len(fields)
            elif last == UP:
                idx = (idx - 1) % len(fields)
            elif last == ENTER:
                idx = (idx + 1) % len(fields)
                if idx == 0:
                    # Attempt connect
                    if not values["token"] or not values["owner"] or not values["repo"]:
                        error_msg = "All fields required."
                        continue
                    mv(r + h - 1, c + 1)
                    print(" " + C["muted"] + "Connecting…" + " "*(w-14) + R, end="", flush=True)
                    try:
                        info = loading_spin("Connecting to GitHub…",
                                           gh_repo, (values["token"], values["owner"], values["repo"]))
                        # Also verify branch
                        branches = gh_branches(values["token"], values["owner"], values["repo"])
                        if values["branch"] not in branches:
                            values["branch"] = branches[0] if branches else "main"
                        save_cfg(values)
                        clr(); show()
                        return values
                    except Exception as e:
                        error_msg = f"Connection failed: {e}"
                        continue

# ═══════════════════════════════════════════════════════════════════════════════
# PUSH SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
def run_git(cmd, cwd="."):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return -1, "", "git not found"

def screen_push(cfg):
    rows, cols = tsz()
    w = min(72, cols - 4)
    r_box = 2
    c_box = (cols - w) // 2
    log_lines = []

    def redraw_log():
        rows2, cols2 = tsz()
        h_log = rows2 - 6
        start = max(0, len(log_lines) - h_log)
        for i, line in enumerate(log_lines[start:start + h_log]):
            mv(r_box + 2 + i, c_box + 2)
            text, color = line
            print(color + cut(text, w - 4) + " " * max(0, w-4-len(cut(text,w-4))) + R,
                  end="", flush=True)
        # clear remaining
        for i in range(len(log_lines[start:start + h_log]), h_log):
            mv(r_box + 2 + i, c_box + 2)
            print(" " * (w - 4), end="", flush=True)

    def log(msg, color=None):
        color = color or C["fg"]
        log_lines.append((msg, color))
        redraw_log()

    clr(); hide()
    rows, cols = tsz()
    box(r_box, c_box, w, rows - 4, " Push to GitHub ")
    mv(r_box + 1, c_box + 1)
    info = f" {cfg['owner']}/{cfg['repo']}  [{cfg['branch']}]"
    print(C["muted"] + info + R, end="", flush=True)

    # Status bar at bottom
    mv(rows - 2, c_box)
    print(C["muted"] + " Running git operations…" + R, end="", flush=True)

    # ── check git ──
    code, out, _ = run_git(["git", "--version"])
    if code != 0:
        log("git not found — install from https://git-scm.com", C["red"])
        log("Press any key to return.", C["muted"])
        show(); getch(); return

    log(f"✓ {out}", C["green"])

    # ── init / remote ──
    if not os.path.isdir(".git"):
        log("Initializing git repository…", C["muted"])
        run_git(["git", "init", "-b", cfg["branch"]])
        run_git(["git", "remote", "add", "origin", cfg["repo_url"]])
        log("✓ git init done", C["green"])
    else:
        url = f"https://github.com/{cfg['owner']}/{cfg['repo']}.git"
        run_git(["git", "remote", "set-url", "origin", url])
        log("✓ git repo detected", C["green"])

    # ── .gitignore ──
    gitignore = "\n".join([
        "# Python", "__pycache__/", "*.pyc", "*.pyo",
        "# Build", "build/", "dist/", "*.egg-info/",
        "# Oxygen", ".oxygen_cfg.json", "oxygen.py.backup",
        "# Credentials", "cookies.txt", "*.json.bak",
    ])
    with open(".gitignore", "w") as f: f.write(gitignore)
    log("✓ .gitignore written", C["green"])

    # ── stage files ──
    log("Staging files…", C["muted"])
    to_stage = ["oxygen.py", "build.bat", "github_push.bat",
                "github_manager.py", "requirements.txt",
                "oxygen.ico", "oxygen.png", "README.md",
                "tr.ini", ".gitignore"]
    staged = []
    for f in to_stage:
        if os.path.isfile(f):
            code, _, _ = run_git(["git", "add", f])
            if code == 0:
                staged.append(f)
                log(f"  + {f}", C["file"])

    # Extra .py and .ini
    for ext in ("*.py", "*.ini"):
        import glob
        for f in glob.glob(ext):
            if f not in to_stage:
                run_git(["git", "add", f])
                staged.append(f)
                log(f"  + {f}", C["file"])

    # Binary size check
    for f in ["ffmpeg.exe","ffplay.exe","ffprobe.exe"] + \
              ["avcodec-62.dll","avdevice-62.dll","avfilter-11.dll",
               "avformat-62.dll","avutil-60.dll","swresample-6.dll","swscale-9.dll"]:
        if os.path.isfile(f):
            sz = os.path.getsize(f)
            if sz > 95 * 1024 * 1024:
                log(f"  ⚠ SKIP {f} ({human_size(sz)}) — over 100MB", C["yellow"])
            else:
                run_git(["git", "add", f])
                log(f"  + {f} ({human_size(sz)})", C["file"])

    # ── diff ──
    code, diff_out, _ = run_git(["git", "diff", "--cached", "--stat"])
    if diff_out:
        log("", C["muted"])
        for line in diff_out.splitlines()[:6]:
            log("  " + line, C["muted"])
    else:
        log("", C["muted"])
        log("Nothing new to commit — already up to date.", C["muted"])

    # ── configure git user (always apply saved values) ──
    git_email = cfg.get("git_email", "").strip()
    git_name  = cfg.get("git_name",  "").strip()

    if not git_email or not git_name:
        # Ask inline
        log("", C["muted"])
        log("Git user not configured — please enter:", C["yellow"])
        redraw_log()
        rows2, cols2 = tsz()

        def ask_inline(prompt, default=""):
            log(f"  {prompt}", C["muted"])
            redraw_log()
            # Find row of last log entry on screen
            h_log2 = rows2 - 6
            line_row = r_box + 2 + min(len(log_lines) - 1, h_log2 - 1)
            mv(line_row, c_box + 4 + len(prompt) + 2)
            val, _ = input_field(line_row, c_box + 4 + len(prompt), w - len(prompt) - 8, default=default)
            log_lines[-1] = (f"  {prompt}{val}", C["fg"])
            redraw_log()
            return val

        if not git_email:
            git_email = ask_inline("Email  : ", "")
        if not git_name:
            git_name  = ask_inline("Name   : ", "")

        cfg["git_email"] = git_email
        cfg["git_name"]  = git_name
        save_cfg(cfg)

    if git_email:
        run_git(["git", "config", "--global", "user.email", git_email])
        log(f"✓ git user.email = {git_email}", C["green"])
    if git_name:
        run_git(["git", "config", "--global", "user.name",  git_name])
        log(f"✓ git user.name  = {git_name}", C["green"])

    # ── commit ──
    commit_msg = f"Update — {time.strftime('%Y-%m-%d %H:%M')}"
    code, _, err = run_git(["git", "commit", "-m", commit_msg])
    if code == 0:
        log(f"✓ Committed: {commit_msg}", C["green"])
    elif "nothing to commit" in err.lower() or "nothing added" in err.lower():
        log("Nothing to commit — already up to date.", C["muted"])
    else:
        log(f"Commit error: {err[:120]}", C["yellow"])

    # ── push ──
    log("", C["muted"])
    log("Pushing to GitHub…", C["muted"])
    url = f"https://github.com/{cfg['owner']}/{cfg['repo']}.git"

    code, out, err = run_git(["git", "push", "-u", "origin", cfg["branch"]])
    if code == 0:
        log(f"✓ Push complete → {url}", C["green"])
    else:
        combined = (out + err).lower()
        log(f"Push failed: {(out+err).strip()[:100]}", C["yellow"])

        if "rejected" in combined or "fetch first" in combined or "tip of your current branch is behind" in combined:
            log("Remote has newer commits. Trying rebase…", C["muted"])
            run_git(["git", "fetch", "origin", cfg["branch"]])
            run_git(["git", "rebase", f"origin/{cfg['branch']}"])
            code2, out2, err2 = run_git(["git", "push", "-u", "origin", cfg["branch"]])
            if code2 == 0:
                log(f"✓ Push complete → {url}", C["green"])
            else:
                log("Rebase push failed too.", C["yellow"])
                log("", C["muted"])
                # Ask force push
                log("Force push will OVERWRITE remote. Press F to force, any other key to skip.", C["yellow"])
                redraw_log()
                show()
                fk = getch()
                hide()
                if fk in ('f', 'F'):
                    run_git(["git", "rebase", "--abort"])
                    code3, _, err3 = run_git(["git", "push", "--force", "-u", "origin", cfg["branch"]])
                    if code3 == 0:
                        log(f"✓ Force push complete → {url}", C["green"])
                    else:
                        log(f"Force push failed: {err3[:80]}", C["red"])
                else:
                    log("Force push skipped.", C["muted"])
        elif "authentication" in combined or "403" in combined or "credential" in combined:
            log("Authentication error. Check your token has 'repo' scope.", C["red"])
        else:
            log(f"Unknown error: {(out+err).strip()[:120]}", C["red"])

    log("", C["muted"])
    log("─" * (w - 8), C["border"])
    log("Done. Press any key to return to menu.", C["muted"])

    mv(rows - 2, c_box)
    print(C["green"] + " Finished." + " "*(w-12) + R, end="", flush=True)
    show(); getch()

# ═══════════════════════════════════════════════════════════════════════════════
# FILE MANAGER / DELETE SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
def screen_manager(cfg):
    # Load tree
    try:
        tree = loading_spin("Loading repository tree…",
                            gh_tree, (cfg["token"], cfg["owner"],
                                      cfg["repo"], cfg["branch"]))
    except Exception as e:
        notify("Error", [f"Could not load tree:", str(e)], C["red"])
        return

    files = [f for f in tree if f["type"] == "blob"]
    selected = set()
    cursor   = 0
    scroll   = 0
    flt      = ""
    filtering= False
    status   = ("Ready  —  SPACE select · D delete · / filter · R refresh · Q back", C["muted"])

    def flist():
        if not flt: return files
        fl = flt.lower()
        return [f for f in files if fl in f["path"].lower()]

    def draw():
        nonlocal cursor, scroll
        rows, cols = tsz()
        HTOP = 4
        HBOT = 3
        LH   = rows - HTOP - HBOT

        if cursor < 0: cursor = 0
        if cursor >= len(flist()): cursor = max(0, len(flist())-1)
        if cursor < scroll: scroll = cursor
        if cursor >= scroll + LH: scroll = cursor - LH + 1

        clr()

        # ── Header ──────────────────────────────────────────────────────────
        repo_str = f"  {cfg['owner']}/{cfg['repo']}  [{cfg['branch']}]"
        sel_str  = f"{len(selected)} selected  {len(flist())}/{len(files)} files  "
        mv(1, 1)
        gap = cols - len("  ⊙ OXYGEN  GitHub Manager") - len(repo_str) - len(sel_str) - 2
        print(
            C["title"] + B + "  ⊙ OXYGEN " + R +
            C["fg"]    + B + " GitHub Manager" + R +
            C["muted"] + repo_str + R +
            " " * max(0, gap) +
            (C["yellow"] + B if selected else C["muted"]) + sel_str + R,
            end="", flush=True
        )

        mv(2, 1); print(C["border"] + "─"*cols + R, end="", flush=True)

        mv(3, 1)
        if filtering:
            print(C["muted"] + "  Filter: " + C["fg"] + flt + C["accent"] + "█" +
                  R + " " * (cols - len(flt) - 12), end="", flush=True)
        else:
            hints = ("  " + C["muted"] +
                     "SPACE" + C["border"] + " select  " +
                     C["muted"] + "A" + C["border"] + " all  " +
                     C["muted"] + "D" + C["border"] + " delete  " +
                     C["muted"] + "/" + C["border"] + " filter  " +
                     C["muted"] + "R" + C["border"] + " refresh  " +
                     C["muted"] + "S" + C["border"] + " settings  " +
                     C["muted"] + "Q" + C["border"] + " back" + R)
            print(hints + " " * max(0, cols - 90), end="", flush=True)

        mv(4, 1); print(C["border"] + "─"*cols + R, end="", flush=True)

        # ── File list ────────────────────────────────────────────────────────
        fl = flist()
        for i in range(LH):
            idx = i + scroll
            mv(HTOP + 1 + i, 1)
            if idx >= len(fl):
                print(" " * cols, end="", flush=True)
                continue

            item   = fl[idx]
            is_cur = idx == cursor
            is_sel = item["path"] in selected

            path   = item["path"]
            parts  = path.rsplit("/", 1)
            dpart  = (parts[0] + "/") if len(parts) == 2 else ""
            fpart  = parts[-1]
            sz     = human_size(item.get("size", 0))

            chk = (C["check"] + "◉" + R) if is_sel else (C["uncheck"] + "○" + R)
            row_bg = C["bgsel"] if is_cur else ""
            max_p  = cols - 8 - len(sz)

            if is_cur:
                path_d = (C["muted"] + cut(dpart, max(0, max_p - len(fpart))) +
                          C["white"] + B + cut(fpart, max_p) + R)
            else:
                sel_c = C["accent"] if is_sel else C["file"]
                path_d = (C["muted"] + cut(dpart, max(0, max_p - len(fpart))) +
                          sel_c + cut(fpart, max_p) + R)

            line = (row_bg +
                    " " + chk + "  " +
                    path_d +
                    C["size"] + " " * max(0, cols - 6 - len(path) - len(sz)) + sz +
                    "  " + R)
            print(line, end="", flush=True)

        # ── Footer ───────────────────────────────────────────────────────────
        mv(rows - HBOT + 1, 1)
        print(C["border"] + "─"*cols + R, end="", flush=True)

        fl2 = flist()
        pct = int(100 * cursor / max(1, len(fl2)-1)) if fl2 else 0
        nav = f"  {cursor+1}/{len(fl2)}  {pct}%"
        mv(rows - HBOT + 2, 1)
        print(C["muted"] + nav + R, end="", flush=True)

        mv(rows - 1, 1)
        msg, col_s = status
        print(col_s + " " + cut(msg, cols - 3) + R +
              " " * max(0, cols - len(cut(msg, cols-3)) - 2),
              end="", flush=True)

    hide()

    while True:
        draw()
        k = getch()
        fl = flist()

        if filtering:
            if k in (ESC, ENTER):
                filtering = False
                status = (f"Filter: '{flt}'" if flt else "Filter cleared", C["muted"])
            elif k == BKSP:
                flt = flt[:-1]; cursor = 0; scroll = 0
            elif isinstance(k, str) and len(k) == 1 and k.isprintable():
                flt += k; cursor = 0; scroll = 0
            continue

        if k == UP    or k == 'k': cursor = max(0, cursor - 1)
        elif k == DOWN or k == 'j': cursor = min(len(fl)-1, cursor+1)
        elif k == PGUP:  cursor = max(0, cursor - 15)
        elif k == PGDN:  cursor = min(len(fl)-1, cursor+15)
        elif k == HOME or k == 'g': cursor = 0; scroll = 0
        elif k == END  or k == 'G': cursor = max(0, len(fl)-1)

        elif k == SPACE:
            if fl:
                p = fl[cursor]["path"]
                if p in selected: selected.discard(p); msg = f"Deselected: {os.path.basename(p)}"
                else:             selected.add(p);    msg = f"Selected: {os.path.basename(p)}"
                status = (msg, C["check"] if p in selected else C["muted"])
                cursor = min(len(fl)-1, cursor+1)

        elif k in ('a','A'):
            if len(selected) >= len(fl):
                selected.clear(); status = ("All deselected", C["muted"])
            else:
                selected = {f["path"] for f in fl}
                status = (f"All {len(selected)} files selected", C["check"])

        elif k == '/':
            filtering = True; flt = ""; cursor = 0; scroll = 0
            status = ("Typing filter… ESC/Enter to stop", C["accent"])

        elif k in ('c','C'):
            flt = ""; cursor = 0; scroll = 0
            status = ("Filter cleared", C["muted"])

        elif k in ('r','R'):
            status = ("Refreshing…", C["muted"]); draw()
            try:
                new = loading_spin("Refreshing tree…",
                                   gh_tree, (cfg["token"], cfg["owner"],
                                             cfg["repo"], cfg["branch"]))
                files = [f for f in new if f["type"] == "blob"]
                selected = {s for s in selected if any(f["path"]==s for f in files)}
                status = (f"Refreshed — {len(files)} files", C["green"])
            except Exception as e:
                status = (f"Refresh error: {e}", C["red"])

        elif k in ('d','D',DEL):
            if not selected:
                status = ("Nothing selected — use SPACE to mark files", C["yellow"])
            else:
                paths = sorted(selected)
                preview = [f"  {p}" for p in paths[:10]]
                if len(paths) > 10:
                    preview.append(f"  … and {len(paths)-10} more")
                if confirm(f" Delete {len(paths)} file(s)?", preview):
                    deleted, errors = [], []
                    perm_error = False

                    for idx_d, p in enumerate(paths):
                        # Show progress in status
                        status = (f"Deleting {idx_d+1}/{len(paths)}: {os.path.basename(p)}…", C["muted"])
                        draw()

                        try:
                            # Always fetch fresh SHA from Contents API — tree SHA may differ
                            fresh_sha = gh_contents_sha(
                                cfg["token"], cfg["owner"], cfg["repo"], p)
                            gh_delete(cfg["token"], cfg["owner"],
                                      cfg["repo"], p, fresh_sha)
                            deleted.append(p)
                            selected.discard(p)
                        except Exception as e:
                            err_s = str(e)
                            errors.append(f"{p}: {err_s}")
                            # Check for permission error — stop early and show hint
                            if "403" in err_s or "accessible" in err_s.lower():
                                perm_error = True
                                break

                    # Refresh tree after deletions
                    try:
                        new = loading_spin("Refreshing…",
                                           gh_tree, (cfg["token"], cfg["owner"],
                                                     cfg["repo"], cfg["branch"]))
                        files = [f for f in new if f["type"] == "blob"]
                        selected = {s for s in selected if any(f["path"]==s for f in files)}
                    except Exception:
                        pass
                    cursor = min(cursor, max(0, len(flist())-1))

                    if perm_error:
                        hint = _403_hint(errors[-1] if errors else "")
                        if hint:
                            notify(" Token Permission Error ",
                                   [f"Deleted {len(deleted)} before error.", ""] + list(hint),
                                   C["red"])
                        status = (f"Permission denied — token needs 'repo' scope. Deleted {len(deleted)}.", C["red"])
                    elif errors:
                        status = (f"Deleted {len(deleted)}, {len(errors)} error(s): {os.path.basename(errors[0].split(':')[0])}", C["yellow"])
                    else:
                        status = (f"✓ Deleted {len(deleted)} file(s)", C["green"])

        elif k in ('s','S'):
            # Quick settings: change branch
            rows, cols = tsz()
            bw, bh = 50, 8
            br, bc = (rows-bh)//2, (cols-bw)//2
            res = dialog_input(br, bc, bw, bh, " Settings ",
                [{"label": "Owner",  "key": "owner",  "default": cfg["owner"]},
                 {"label": "Repo",   "key": "repo",   "default": cfg["repo"]},
                 {"label": "Branch", "key": "branch", "default": cfg["branch"]}])
            if res:
                cfg.update(res); save_cfg(cfg)
                status = (f"Updated → {cfg['owner']}/{cfg['repo']} [{cfg['branch']}]", C["green"])
                # Reload
                try:
                    new = loading_spin("Reloading…",
                                       gh_tree, (cfg["token"], cfg["owner"],
                                                 cfg["repo"], cfg["branch"]))
                    files = [f for f in new if f["type"] == "blob"]
                    selected.clear(); cursor = 0; scroll = 0
                except Exception as e:
                    status = (f"Reload error: {e}", C["red"])

        elif k in ('q','Q',ESC):
            break

    show()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════
MENU_ITEMS = [
    ("push",    "↑  Push files to GitHub",           "Stage, commit and push your local files"),
    ("manager", "⊞  Browse & delete repo files",     "Interactive file manager with TUI"),
    ("settings","⚙  Change account / repo",          "Update token, owner, repo, branch"),
    ("quit",    "✕  Quit",                            ""),
]

def screen_menu(cfg):
    cursor = 0
    while True:
        rows, cols = tsz()
        w = min(70, cols - 4)
        h = len(MENU_ITEMS) * 3 + 8
        r = max(1, (rows - h) // 2)
        c = (cols - w) // 2

        clr(); hide()
        box(r, c, w, h, " Oxygen  GitHub Manager ")

        # Subtitle
        mv(r+1, c+1)
        sub = f"  {cfg['owner']}/{cfg['repo']}  [{cfg['branch']}]"
        print(" " + C["muted"] + pad(sub, w-4, "center") + R, end="", flush=True)
        mv(r+2, c+1)
        print(" " + C["border"] + "─"*(w-2) + R, end="", flush=True)

        for i, (key, label, desc) in enumerate(MENU_ITEMS):
            ri = r + 3 + i * 3
            active = i == cursor
            bg_c = C["bgsel"] if active else ""
            bullet = C["accent"] + B + "▶ " + R if active else C["muted"] + "  "
            lbl_c  = C["white"] + B if active else C["fg"]
            desc_c = C["accent"] if active else C["muted"]

            mv(ri, c+1)
            print(" " + bg_c + bullet + lbl_c + pad(label, w-7) + R, end="", flush=True)
            if desc:
                mv(ri+1, c+1)
                print(" " + C["muted"] + "    " + pad(desc, w-7) + R, end="", flush=True)

        mv(r+h-2, c+1)
        print(" " + C["muted"] + pad("↑↓ navigate   Enter select", w-4, "center") + R,
              end="", flush=True)
        show()

        k = getch()
        if k == UP    or k == 'k': cursor = (cursor - 1) % len(MENU_ITEMS)
        elif k == DOWN or k == 'j': cursor = (cursor + 1) % len(MENU_ITEMS)
        elif k in ('1','2','3','4'): cursor = int(k) - 1
        elif k in (ENTER, RIGHT, ' '):
            action = MENU_ITEMS[cursor][0]
            if action == "quit":
                return
            elif action == "push":
                # Need repo URL for push
                remote = git_remote()
                cfg["repo_url"] = remote or f"https://github.com/{cfg['owner']}/{cfg['repo']}.git"
                screen_push(cfg)
            elif action == "manager":
                screen_manager(cfg)
            elif action == "settings":
                new = screen_setup()
                if new: cfg = new
        elif k in ('q','Q',ESC):
            return

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    hide()
    try:
        cfg = screen_setup()
        if cfg:
            screen_menu(cfg)
    except KeyboardInterrupt:
        pass
    finally:
        show()
        clr()
        print(C["muted"] + "  Goodbye.\n" + R)

if __name__ == "__main__":
    main()
