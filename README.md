# Oxygen v3.0 — Media Downloader

Multi-platform media downloader powered by **yt-dlp**.  
Supports YouTube, SoundCloud, X (Twitter), Instagram, and 1000+ more.

---

## 🚀 Quick Start (Python)

```bash
pip install -r requirements.txt
python oxygen.py
```

---

## 📦 Build EXE (Windows)

1. Place `ffmpeg.exe` in the project folder *(optional but recommended)*
2. Double-click **`build.bat`**
3. Find `Oxygen.exe` inside `dist\Oxygen\`

> **ffmpeg:** Download from https://ffmpeg.org/download.html  
> Pick the Windows build → extract → copy `ffmpeg.exe` here.

---

## 📁 Project Structure

```
oxygen_project/
├── oxygen.py         ← main application
├── build.bat         ← Windows EXE builder
├── requirements.txt
├── ffmpeg.exe        ← place here (downloaded separately)
├── oxygen.ico        ← app icon (optional)
└── oxygen.png        ← logo shown in-app (optional)
```

After building:
```
dist/Oxygen/
├── Oxygen.exe        ← run this
├── ffmpeg.exe        ← auto-copied if present
└── (other bundled files)
```

---

## 🎛️ Features

| Mode      | Description                              |
|-----------|------------------------------------------|
| **auto**  | Best video + audio merged                |
| **audio** | Audio only — choose format & quality     |
| **mute**  | Video only — no audio track              |

### Quality Controls
- **Resolution** (auto/mute): best · 4K · 1440p · 1080p · 720p · 480p · 360p · 240p · worst
- **Video format** (auto/mute): mp4 · mkv · webm · avi · mov
- **Audio quality** (audio mode): best · 320k · 256k · 192k · 128k · 96k · 64k
- **Audio format** (audio mode): mp3 · m4a · opus · flac · wav · aac

### Other
- ✅ Playlist download support
- ✅ Auto-paste from clipboard
- ✅ Dark / OLED / Light themes
- ✅ Custom accent color
- ✅ Multi-language support via `.ini` files
- ✅ Auto-detects `ffmpeg.exe` next to the app

---

## 🌍 Adding Languages

Create a file like `tr.ini` next to `oxygen.py`:

```ini
[oxygen]
title = Oxygen
btn_download = ↓   indir
btn_paste = 📋  yapıştır
```

Any key from `BUILTIN_EN` in `oxygen.py` can be overridden.

---

## 📝 Notes

- Controls change automatically based on selected mode
- ffmpeg is required for merging video+audio and audio extraction
- Oxygen will try to auto-install ffmpeg if not found
