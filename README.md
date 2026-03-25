<p align="center"><img src="oxygen.png" alt="Oxygen Logo" width="120"></p>

<h1 align="center">Oxygen</h1>

<p align="center">Multi-platform media downloader powered by yt-dlp. Supports YouTube, SoundCloud, X, Instagram, and 1000+ sites.</p>

---

## :zap: Quick Start

### Method 1 — Run with Python

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Launch the app:
   ```
   python oxygen.py
   ```

---

### Method 2 — Build a Windows EXE :package:

1. *(Optional but recommended)* Place `ffmpeg.exe` in the project folder.
2. Double-click **`build.bat`**.
3. Find `Oxygen.exe` inside `dist\Oxygen\`.

> [!TIP]
> Download ffmpeg from https://ffmpeg.org/download.html — pick the Windows build, extract the archive, and copy `ffmpeg.exe` into the project folder. ffmpeg is required for merging video+audio and audio extraction. Oxygen will attempt to auto-install it if not found.

---

## :control_knobs: Features

| Mode      | Description                            |
|-----------|----------------------------------------|
| `auto`    | Best quality video + audio, merged     |
| `audio`   | Audio only — choose format & bitrate   |
| `mute`    | Video only — no audio track            |

**Resolution** *(auto / mute)*: best · 4K · 1440p · 1080p · 720p · 480p · 360p · 240p · worst

**Video format** *(auto / mute)*: mp4 · mkv · webm · avi · mov

**Audio quality** *(audio)*: best · 320k · 256k · 192k · 128k · 96k · 64k

**Audio format** *(audio)*: mp3 · m4a · opus · flac · wav · aac

- :white_check_mark: Playlist download support
- :white_check_mark: Auto-paste from clipboard
- :white_check_mark: Dark / OLED / Light themes with custom accent color
- :white_check_mark: Multi-language support via `.ini` files

---

## :earth_africa: Adding a Language

Create a `.ini` file (e.g. `tr.ini`) next to `oxygen.py`:

```ini
[oxygen]
title = Oxygen
btn_download = ↓   indir
btn_paste = 📋  yapıştır
```

Any key from `BUILTIN_EN` in `oxygen.py` can be overridden.

---

## :open_file_folder: Project Structure

```
oxygen_project/
├── oxygen.py           ← main application
├── build.bat           ← Windows EXE builder
├── requirements.txt
├── ffmpeg.exe          ← place here (downloaded separately)
├── oxygen.ico          ← app icon (optional)
└── oxygen.png          ← logo shown in-app (optional)
```

After building:

```
dist/Oxygen/
├── Oxygen.exe          ← run this
├── ffmpeg.exe          ← auto-copied if present
└── (other bundled files)
```

---

> [!NOTE]
> Controls update automatically based on the selected mode. ffmpeg must be present for video+audio merging and audio-only extraction.
