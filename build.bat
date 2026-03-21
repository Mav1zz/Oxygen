@echo off
setlocal enabledelayedexpansion
title Oxygen - Build EXE

echo.
echo ==========================================
echo   Oxygen - EXE Build Script  v3.1
echo ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v found

echo.
echo [1/4] Installing build dependencies...
pip install pyinstaller yt-dlp Pillow --quiet --upgrade
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo [OK] Dependencies ready

echo.
echo [2/4] Collecting assets...

set "DATA_ARGS="
set "BINARY_ARGS="
set "ICON_ARG="

if exist "oxygen.ico" (
    set "DATA_ARGS=!DATA_ARGS! --add-data "oxygen.ico;.""
    set "ICON_ARG=--icon=oxygen.ico"
    echo [OK] oxygen.ico found
)
if exist "oxygen.png" (
    set "DATA_ARGS=!DATA_ARGS! --add-data "oxygen.png;.""
    echo [OK] oxygen.png found
)

if exist "ffmpeg.exe" (
    set "BINARY_ARGS=!BINARY_ARGS! --add-binary "ffmpeg.exe;.""
    echo [OK] ffmpeg.exe found - will bundle
) else (
    echo [WARN] ffmpeg.exe not found. Place it next to Oxygen.exe after build.
    echo        Download: https://ffmpeg.org/download.html
)

echo.
echo [3/4] Building Oxygen.exe...
echo       (bundling yt-dlp + Pillow - this takes a minute)
echo.

pyinstaller ^
    --onedir ^
    --noconsole ^
    --name=Oxygen ^
    %ICON_ARG% ^
    %DATA_ARGS% ^
    %BINARY_ARGS% ^
    --collect-all yt_dlp ^
    --collect-all PIL ^
    --hidden-import yt_dlp ^
    --hidden-import yt_dlp.utils ^
    --hidden-import yt_dlp.extractor ^
    --hidden-import yt_dlp.postprocessor ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.filedialog ^
    --hidden-import tkinter.messagebox ^
    --clean ^
    oxygen.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build FAILED. See output above.
    pause
    exit /b 1
)

echo.
echo [4/4] Copying ffmpeg to output folder...
if exist "ffmpeg.exe" (
    copy /y "ffmpeg.exe" "dist\Oxygenfmpeg.exe" >nul 2>&1
    echo [OK] ffmpeg.exe copied to dist\Oxygen)
if exist "ffplay.exe" (
    copy /y "ffplay.exe" "dist\Oxygenfplay.exe" >nul 2>&1
)
if exist "ffprobe.exe" (
    copy /y "ffprobe.exe" "dist\Oxygenfprobe.exe" >nul 2>&1
)

echo.
echo ==========================================
echo   Build complete!
echo.
echo   Run : dist\Oxygen\Oxygen.exe
echo.
echo   IMPORTANT: ffmpeg.exe must be inside
echo   dist\Oxygen\  for video downloads.
echo ==========================================
echo.
pause
