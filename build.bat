@echo off
setlocal enabledelayedexpansion
title Oxygen - Build EXE

echo.
echo ==========================================
echo   Oxygen - EXE Build Script  v3.0
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v found

:: Install dependencies
echo.
echo [1/3] Installing build dependencies...
pip install pyinstaller yt-dlp Pillow --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo [OK] Dependencies ready

:: Collect assets
echo.
echo [2/3] Collecting assets...

set "DATA_ARGS="
set "BINARY_ARGS="
set "ICON_ARG="

if exist "oxygen.ico" (
    set "DATA_ARGS=!DATA_ARGS! --add-data "oxygen.ico;.""
    set "ICON_ARG=--icon=oxygen.ico"
    echo [OK] oxygen.ico found - will bundle
) else (
    echo [WARN] oxygen.ico not found - app will use fallback icon
)

if exist "oxygen.png" (
    set "DATA_ARGS=!DATA_ARGS! --add-data "oxygen.png;.""
    echo [OK] oxygen.png found - will bundle
)

if exist "ffmpeg.exe" (
    set "BINARY_ARGS=!BINARY_ARGS! --add-binary "ffmpeg.exe;.""
    echo [OK] ffmpeg.exe found - will bundle alongside Oxygen.exe
) else (
    echo [WARN] ffmpeg.exe not found in this folder.
    echo        Place ffmpeg.exe next to Oxygen.exe after build.
    echo        Download: https://ffmpeg.org/download.html
    echo.
)

:: Build
echo.
echo [3/3] Building Oxygen.exe - please wait...
echo.

pyinstaller ^
    --onedir ^
    --noconsole ^
    --name=Oxygen ^
    %ICON_ARG% ^
    %DATA_ARGS% ^
    %BINARY_ARGS% ^
    --clean ^
    oxygen.py

if errorlevel 1 (
    echo.
    echo ==========================================
    echo [ERROR] Build FAILED. See output above.
    echo ==========================================
    pause
    exit /b 1
)

:: Copy ffmpeg next to exe
if exist "ffmpeg.exe" (
    copy /y "ffmpeg.exe" "dist\Oxygen\ffmpeg.exe" >nul 2>&1
    echo [OK] ffmpeg.exe copied to dist\Oxygen\
)

echo.
echo ==========================================
echo   Build complete!
echo.
echo   Run : dist\Oxygen\Oxygen.exe
echo.
echo   Keep the entire dist\Oxygen\ folder.
echo   Place ffmpeg.exe inside dist\Oxygen\
echo   and Oxygen will find it automatically.
echo ==========================================
echo.
pause
