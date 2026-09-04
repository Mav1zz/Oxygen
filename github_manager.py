"""
Oxygen GitHub Manager  –  v4.0 (Enhanced)
Pure Python TUI: push files, pull changes, view logs, browse repo, delete files, manage settings.
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
    return s if len(s) <= n else s[:n-1] + "…"

def pad(s, n, align="left"):
    s = cut(s, n)
    if align == "center": return s.center(n)
    if align == "right":  return s.rjust(n)
    return s.ljust(n)

def box(row, col, w, h, title=""):
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

def human_size(b):
    if not b: return ""
    for u in ("B","KB","MB","GB"):
        if b < 1024: return f"{b:.0f}{u}"
        b /= 1024
    return f"{b:.1f}GB"

def loading_spin(msg, fn, args=()):
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
def _req(token, path, method="GET", body=None, raw=False):
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    headers = {
        "Authorization": f"token {token}",
        "User-Agent":    "Oxygen-Manager/4.0",
    }
    if not raw:
        headers["Accept"] = "application/vnd.github.v3+json"
        if body: headers["Content-Type"] = "application/json"
    else:
        headers["Accept"] = "application/vnd.github.v3.raw"

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            if raw: return r.read().decode("utf-8", errors="replace")
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode(errors="ignore")
        try: msg = json.loads(body_txt).get("message", body_txt)
        except Exception: msg = body_txt[:120]
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
        for i in data.get("tree", []) if i["type"] in ("blob", "tree")
    ]

def gh_contents_sha(token, owner, repo, path):
    data = _req(token, f"/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}")
    if isinstance(data, list): raise RuntimeError(f"Path is a directory: {path}")
    return data["sha"]

def gh_delete(token, owner, repo, path, sha, msg="Remove via Oxygen Manager"):
    encoded = urllib.parse.quote(path, safe="")
    return _req(token, f"/repos/{owner}/{repo}/contents/{encoded}",
                method="DELETE", body={"message": msg, "sha": sha})

def gh_raw_file(token, owner, repo, branch, path):
    encoded = urllib.parse.quote(path, safe="")
    return _req(token, f"/repos/{owner}/{repo}/contents/{encoded}?ref={branch}", raw=True)

def parse_url(url):
    url = url.strip().rstrip("/").removesuffix(".git")
    parts = url.split("/")
    if len(parts) >= 2: return parts[-2], parts[-1]
    return "", ""

def git_remote():
    try:
        return subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            stderr=subprocess.DEVNULL, text=True).strip()
    except Exception: return ""

# ═══════════════════════════════════════════════════════════════════════════════
# INPUT & DIALOG WIDGETS
# ═══════════════════════════════════════════════════════════════════════════════
def input_field(row, col, width, default="", password=False, label=""):
    if label:
        mv(row, col); print(C["muted"] + label + R, end="", flush=True)
        col += len(label); width -= len(label)
    buf = list(default)
    def redraw():
        mv(row, col)
        disp = "".join("*" if password else c for c in buf)[-(width-1):]
        print(C["fg"] + disp.ljust(width-1) + C["accent"] + "█" + R, end="", flush=True)
    show(); redraw()
    while True:
        k = getch()
        if k == ENTER: break
        elif k == ESC: buf = list(default); break
        elif k == BKSP and buf: buf.pop(); redraw()
        elif k in (LEFT, RIGHT, UP, DOWN, TAB): break
        elif isinstance(k, str) and len(k) == 1 and k.isprintable():
            buf.append(k); redraw()
    hide(); mv(row, col)
    val = "".join(buf)
    disp = "".join("*" if password else c for c in buf)[-(width-1):]
    print(C["fg"] + disp.ljust(width) + R, end="", flush=True)
    return val, k

def dialog_input(row, col, w, h, title, fields):
    box(row, col, w, h, title)
    values = {f["key"]: f.get("default", "") for f in fields}
    idx = 0
    while True:
        for i, f in enumerate(fields):
            r = row + 2 + i * 2; active = (i == idx)
            lbl = f["label"].ljust(14); mv(r, col + 2)
            bcol = C["accent"] if active else C["muted"]
            print(bcol + ("▶ " if active else "  ") + C["muted"] + lbl + R, end="", flush=True)
            mv(r, col + 18)
            disp = ("*" * len(values[f["key"]]) if f.get("password") else values[f["key"]])
            print((C["bgsel"] if active else "") + C["fg"] + cut(disp, w - 20).ljust(w - 20) + R, end="", flush=True)
        mv(row + h - 2, col + 2)
        print(C["muted"] + "Tab/↑↓ navigate   Enter confirm   Esc cancel" + R, end="", flush=True)
        r = row + 2 + idx * 2
        val, last_key = input_field(r, col + 18, w - 19, default=values[fields[idx]["key"]], password=fields[idx].get("password", False))
        values[fields[idx]["key"]] = val
        if last_key == ESC: return None
        elif last_key in (ENTER, DOWN, TAB):
            idx = (idx + 1) % len(fields)
            if last_key == ENTER and idx == 0: return values
        elif last_key == UP: idx = (idx - 1) % len(fields)

def notify(title, lines, color=None, wait=True):
    rows, cols = tsz()
    w = min(68, cols - 4); h = len(lines) + 4
    r = (rows - h) // 2; c = (cols - w) // 2
    color = color or C["fg"]
    hide(); box(r, c, w, h, title)
    for i, line in enumerate(lines):
        mv(r + 1 + i, c + 1)
        print(" " + color + cut(line, w-4) + R + " " * (w-4-len(cut(line,w-4))), end="", flush=True)
    if wait:
        mv(r + h - 2, c + 1)
        print(" " + C["muted"] + "Press any key to continue…" + R, end="", flush=True)
        show(); getch(); hide()

def confirm(title, lines, yes="Y", no="N"):
    rows, cols = tsz()
    w = min(66, cols - 4); h = len(lines) + 5
    r = (rows - h) // 2; c = (cols - w) // 2
    hide(); box(r, c, w, h, title)
    for i, line in enumerate(lines):
        mv(r + 1 + i, c + 1); print(" " + C["yellow"] + cut(line, w-4) + R, end="", flush=True)
    mv(r + h - 2, c + 1)
    print(" " + C["muted"] + f"[{yes}] Confirm   [{no}] Cancel" + R, end="", flush=True)
    show()
    while True:
        k = getch()
        if k.upper() == yes.upper(): return True
        if k.upper() == no.upper() or k == ESC: return False

def run_git(cmd, cwd="."):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception as e: return -1, "", str(e)

# ═══════════════════════════════════════════════════════════════════════════════
# SCREENS: SETUP, PUSH, PULL, LOG
# ═══════════════════════════════════════════════════════════════════════════════
def screen_setup():
    saved = load_cfg(); remote = git_remote()
    o_def, r_def = parse_url(remote)
    def _git_cfg(key):
        try: return subprocess.check_output(["git", "config", "--global", key], stderr=subprocess.DEVNULL, text=True).strip()
        except: return ""

    fields = [
        {"label": "Token",  "key": "token",      "default": saved.get("token",""), "password": True},
        {"label": "Owner",  "key": "owner",      "default": saved.get("owner", o_def)},
        {"label": "Repo",   "key": "repo",       "default": saved.get("repo",  r_def)},
        {"label": "Branch", "key": "branch",     "default": saved.get("branch","main")},
        {"label": "Email",  "key": "git_email",  "default": saved.get("git_email", _git_cfg("user.email"))},
        {"label": "Name",   "key": "git_name",   "default": saved.get("git_name",  _git_cfg("user.name"))},
    ]

    while True:
        rows, cols = tsz(); w = min(68, cols - 4); h = 26
        r = max(1, (rows - h) // 2); c = (cols - w) // 2
        clr(); hide(); box(r, c, w, h, " Oxygen GitHub Manager ")
        logo = ["   ⊙  OXYGEN", "   GitHub Manager  v4.0"]
        for i, line in enumerate(logo):
            mv(r + 1 + i, c + 1); col = C["title"] + B if i == 0 else C["muted"]
            print(" " + col + pad(line, w-4, "center") + R, end="", flush=True)

        mv(r + 5, c + 1); print(" " + C["muted"] + pad("GitHub Personal Access Token needed (Scope: repo)", w-4, "center") + R, end="", flush=True)
        idx = 0; values = {f["key"]: f["default"] for f in fields}

        def draw_fields():
            for i, f in enumerate(fields):
                mv(r + 10 + i * 2, c + 2); active = (i == idx)
                disp = ("*"*len(values[f["key"]]) if f.get("password") else values[f["key"]])
                print((C["accent"] if active else C["muted"]) + ("▶ " if active else "  ") + C["muted"] + f["label"].ljust(9) + " " + (C["bgsel"] if active else "") + C["fg"] + cut(disp, w - 18).ljust(w-18) + R, end="", flush=True)

        error_msg = ""
        while True:
            draw_fields()
            if error_msg: mv(r + h - 1, c + 1); print(" " + C["red"] + cut(error_msg, w-4) + R, end="", flush=True)
            val, last = input_field(r + 10 + idx * 2, c + 13, w - 14, default=values[fields[idx]["key"]], password=fields[idx].get("password", False))
            values[fields[idx]["key"]] = val
            if last == ESC: clr(); show(); return None
            elif last in (DOWN, TAB): idx = (idx + 1) % len(fields)
            elif last == UP: idx = (idx - 1) % len(fields)
            elif last == ENTER:
                idx = (idx + 1) % len(fields)
                if idx == 0:
                    if not values["token"] or not values["owner"] or not values["repo"]:
                        error_msg = "Token, Owner, and Repo are required."
                        continue
                    try:
                        loading_spin("Connecting to GitHub…", gh_repo, (values["token"], values["owner"], values["repo"]))
                        branches = gh_branches(values["token"], values["owner"], values["repo"])
                        if values["branch"] not in branches: values["branch"] = branches[0] if branches else "main"
                        save_cfg(values); clr(); show(); return values
                    except Exception as e: error_msg = f"Failed: {e}"

def tui_git_runner(title, action_callback):
    """Generic UI box for running git commands and showing streaming logs."""
    rows, cols = tsz(); w = min(72, cols - 4)
    r_box = 2; c_box = (cols - w) // 2
    log_lines = []

    def redraw_log():
        rows2, _ = tsz(); h_log = rows2 - 6; start = max(0, len(log_lines) - h_log)
        for i, line in enumerate(log_lines[start:start + h_log]):
            mv(r_box + 2 + i, c_box + 2); text, color = line
            print(color + cut(text, w - 4).ljust(w - 4) + R, end="", flush=True)

    def log(msg, color=None):
        log_lines.append((msg, color or C["fg"])); redraw_log()

    clr(); hide(); box(r_box, c_box, w, rows - 4, title)
    action_callback(log)
    mv(rows - 2, c_box); print(C["green"] + " Finished. Press any key." + " "*(w-26) + R, end="", flush=True)
    show(); getch()

def screen_push(cfg):
    def action(log):
        log(f"Target: {cfg['owner']}/{cfg['repo']} [{cfg['branch']}]", C["muted"])
        code, out, _ = run_git(["git", "--version"])
        if code != 0: log("git not found", C["red"]); return
        
        if not os.path.isdir(".git"):
            run_git(["git", "init", "-b", cfg["branch"]])
            run_git(["git", "remote", "add", "origin", cfg["repo_url"]])
            log("✓ git init done", C["green"])
        else:
            run_git(["git", "remote", "set-url", "origin", cfg["repo_url"]])

        log("Staging files…", C["muted"])
        code, _, _ = run_git(["git", "add", "."])
        
        code, diff_out, _ = run_git(["git", "status", "-s"])
        if diff_out:
            for line in diff_out.splitlines()[:10]: log("  " + line, C["file"])
            if len(diff_out.splitlines()) > 10: log("  ... and more.", C["file"])
        else:
            log("Nothing new to commit.", C["muted"])
            return

        if cfg.get("git_email"): run_git(["git", "config", "user.email", cfg["git_email"]])
        if cfg.get("git_name"): run_git(["git", "config", "user.name", cfg["git_name"]])

        msg = f"Update — {time.strftime('%Y-%m-%d %H:%M')}"
        code, _, err = run_git(["git", "commit", "-m", msg])
        if code == 0: log(f"✓ Committed: {msg}", C["green"])
        
        log("Pushing to GitHub…", C["muted"])
        code, out, err = run_git(["git", "push", "-u", "origin", cfg["branch"]])
        if code == 0: log("✓ Push complete!", C["green"])
        else: log(f"Push failed: {err[:120]}", C["red"])
    
    tui_git_runner(" Push to GitHub ", action)

def screen_pull(cfg):
    def action(log):
        log(f"Pulling from: {cfg['owner']}/{cfg['repo']} [{cfg['branch']}]", C["muted"])
        if not os.path.isdir(".git"):
            log("No local git repo found. Initialize and link first.", C["red"])
            return
        run_git(["git", "remote", "set-url", "origin", cfg["repo_url"]])
        
        log("Fetching remote changes...", C["muted"])
        code, out, err = run_git(["git", "pull", "origin", cfg["branch"]])
        if code == 0:
            log("✓ Pull successful.", C["green"])
            for line in out.splitlines()[:15]: log("  " + line, C["file"])
        else:
            log(f"Pull failed (Merge conflict or dirty tree?):", C["red"])
            log(err[:150], C["yellow"])

    tui_git_runner(" Pull from GitHub ", action)

def screen_log(cfg):
    def action(log):
        log("Recent Commits:", C["title"])
        code, out, err = run_git(["git", "log", "-n", "15", "--oneline", "--decorate", "--color=never"])
        if code == 0:
            for line in out.splitlines():
                parts = line.split(" ", 1)
                if len(parts) == 2: log(f" {parts[0][:7]:<8} | {parts[1]}", C["fg"])
        else:
            log("Could not retrieve logs. Is this a valid git repo?", C["red"])
            log(err, C["muted"])

    tui_git_runner(" Git Log ", action)

# ═══════════════════════════════════════════════════════════════════════════════
# FILE MANAGER / DELETE / VIEW SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
def screen_manager(cfg):
    try: tree = loading_spin("Loading repo tree…", gh_tree, (cfg["token"], cfg["owner"], cfg["repo"], cfg["branch"]))
    except Exception as e: notify("Error", [f"Tree load failed:", str(e)], C["red"]); return

    files = [f for f in tree if f["type"] == "blob"]
    selected = set(); cursor = 0; scroll = 0; flt = ""; filtering = False
    status = ("Ready — SPACE sel · D del · V view · / filter · R ref · Q back", C["muted"])

    def flist():
        return [f for f in files if flt.lower() in f["path"].lower()] if flt else files

    def draw():
        nonlocal cursor, scroll
        rows, cols = tsz(); HTOP = 4; HBOT = 3; LH = rows - HTOP - HBOT
        fl = flist()
        cursor = max(0, min(cursor, len(fl)-1))
        if cursor < scroll: scroll = cursor
        if cursor >= scroll + LH: scroll = cursor - LH + 1

        clr()
        mv(1, 1); gap = cols - 50
        print(C["title"]+B+"  ⊙ OXYGEN File Manager "+R+C["muted"]+f" {cfg['branch']} "+R+" "*max(0, gap)+C["yellow"]+f"{len(selected)} sel  {len(fl)}/{len(files)} files "+R, end="")
        mv(2, 1); print(C["border"] + "─"*cols + R, end="")
        mv(3, 1)
        if filtering: print(C["muted"]+"  Filter: "+C["fg"]+flt+C["accent"]+"█"+R, end="")
        else: print(C["muted"]+"  SPACE sel  V view  D del  / filter  R ref  Q back", end="")
        mv(4, 1); print(C["border"] + "─"*cols + R, end="")

        for i in range(LH):
            idx = i + scroll; mv(HTOP + 1 + i, 1)
            if idx >= len(fl): print(" "*cols, end=""); continue
            item = fl[idx]; path = item["path"]
            chk = C["check"]+"◉"+R if path in selected else C["uncheck"]+"○"+R
            bg_c = C["bgsel"] if idx == cursor else ""
            sz = human_size(item.get("size", 0))
            name = path.split("/")[-1]
            p_dir = path[:-len(name)]
            name_c = C["white"]+B if idx == cursor else (C["accent"] if path in selected else C["file"])
            print(bg_c + " " + chk + "  " + C["muted"] + cut(p_dir, 30).ljust(30) + name_c + cut(name, 35).ljust(35) + C["size"] + sz.rjust(10) + R + " "*max(0, cols-85), end="")

        mv(rows - HBOT + 1, 1); print(C["border"] + "─"*cols + R, end="")
        mv(rows - 1, 1); msg, col_s = status
        print(col_s + " " + cut(msg, cols - 3).ljust(cols - 3) + R, end="", flush=True)
    hide()

    while True:
        draw(); k = getch(); fl = flist()
        if filtering:
            if k in (ESC, ENTER): filtering = False; status = ("Filter mode exited.", C["muted"])
            elif k == BKSP: flt = flt[:-1]; cursor = scroll = 0
            elif isinstance(k, str) and len(k) == 1 and k.isprintable(): flt += k; cursor = scroll = 0
            continue

        if k == UP or k == 'k': cursor -= 1
        elif k == DOWN or k == 'j': cursor += 1
        elif k == PGUP: cursor -= 15
        elif k == PGDN: cursor += 15
        elif k == SPACE and fl:
            p = fl[cursor]["path"]
            if p in selected: selected.remove(p)
            else: selected.add(p)
            cursor += 1
        elif k == '/': filtering = True; flt = ""; cursor = scroll = 0; status = ("Typing filter...", C["accent"])
        elif k in ('v', 'V') and fl:
            p = fl[cursor]["path"]
            try:
                content = loading_spin(f"Reading {os.path.basename(p)}...", gh_raw_file, (cfg["token"], cfg["owner"], cfg["repo"], cfg["branch"], p))
                lines = content.splitlines()
                disp_lines = lines[:20]
                if len(lines) > 20: disp_lines.append(f"... (and {len(lines)-20} more lines)")
                notify(f" Preview: {os.path.basename(p)} ", disp_lines, C["fg"])
            except Exception as e: notify("Read Error", [str(e)], C["red"])
        elif k in ('d', 'D') and selected:
            paths = sorted(selected); prev = [f"  {p}" for p in paths[:10]]
            if confirm(f" Delete {len(paths)} file(s)?", prev):
                deleted = 0
                for i, p in enumerate(paths):
                    status = (f"Deleting {i+1}/{len(paths)}...", C["muted"]); draw()
                    try:
                        sha = gh_contents_sha(cfg["token"], cfg["owner"], cfg["repo"], p)
                        gh_delete(cfg["token"], cfg["owner"], cfg["repo"], p, sha)
                        deleted += 1
                    except Exception as e: status = (f"Error: {e}", C["red"]); break
                selected.clear(); status = (f"Deleted {deleted} files.", C["green"])
                # Auto refresh
                tree = loading_spin("Refreshing repo tree…", gh_tree, (cfg["token"], cfg["owner"], cfg["repo"], cfg["branch"]))
                files = [f for f in tree if f["type"] == "blob"]
        elif k in ('r', 'R'):
            try:
                tree = loading_spin("Refreshing repo tree…", gh_tree, (cfg["token"], cfg["owner"], cfg["repo"], cfg["branch"]))
                files = [f for f in tree if f["type"] == "blob"]
                status = ("Refreshed.", C["green"])
            except Exception as e: status = (str(e), C["red"])
        elif k in ('q', 'Q', ESC): break

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════
MENU_ITEMS = [
    ("push",    "↑  Push files to GitHub",       "Stage, commit and push your local files"),
    ("pull",    "↓  Pull from GitHub",           "Fetch and merge remote changes"),
    ("log",     "≡  View Commit Log",            "See recent commit history (local)"),
    ("manager", "⊞  Browse & Manage files",      "TUI File manager (Delete / View)"),
    ("settings","⚙  Change account / repo",      "Update token, owner, repo, branch"),
    ("quit",    "✕  Quit",                        ""),
]

def screen_menu(cfg):
    cursor = 0
    while True:
        rows, cols = tsz(); w = min(70, cols - 4); h = len(MENU_ITEMS) * 3 + 8
        r = max(1, (rows - h) // 2); c = (cols - w) // 2
        clr(); hide(); box(r, c, w, h, " Oxygen  GitHub Manager ")
        mv(r+1, c+1)
        print(" " + C["muted"] + pad(f"  {cfg['owner']}/{cfg['repo']}  [{cfg['branch']}]", w-4, "center") + R, end="")
        mv(r+2, c+1); print(" " + C["border"] + "─"*(w-2) + R, end="")

        for i, (key, label, desc) in enumerate(MENU_ITEMS):
            ri = r + 3 + i * 3; active = i == cursor
            mv(ri, c+1)
            print(" " + (C["bgsel"] if active else "") + (C["accent"]+B+"▶ "+R if active else C["muted"]+"  ") + (C["white"]+B if active else C["fg"]) + pad(label, w-7) + R, end="")
            if desc: mv(ri+1, c+1); print(" " + C["muted"] + "    " + pad(desc, w-7) + R, end="")

        mv(r+h-2, c+1); print(" " + C["muted"] + pad("↑↓ navigate   Enter select", w-4, "center") + R, end="", flush=True)
        show(); k = getch()
        
        if k == UP or k == 'k': cursor = (cursor - 1) % len(MENU_ITEMS)
        elif k == DOWN or k == 'j': cursor = (cursor + 1) % len(MENU_ITEMS)
        elif k in (ENTER, RIGHT, ' '):
            action = MENU_ITEMS[cursor][0]
            cfg["repo_url"] = git_remote() or f"https://github.com/{cfg['owner']}/{cfg['repo']}.git"
            
            if action == "quit": return
            elif action == "push": screen_push(cfg)
            elif action == "pull": screen_pull(cfg)
            elif action == "log": screen_log(cfg)
            elif action == "manager": screen_manager(cfg)
            elif action == "settings":
                new = screen_setup()
                if new: cfg = new
        elif k in ('q', 'Q', ESC): return

def main():
    hide()
    try:
        cfg = screen_setup()
        if cfg: screen_menu(cfg)
    except KeyboardInterrupt: pass
    finally: show(); clr(); print(C["muted"] + "  Goodbye.\n" + R)

if __name__ == "__main__":
    main()