@echo off
setlocal enabledelayedexpansion
title Oxygen - GitHub Push

echo.
echo ==========================================
echo   Oxygen - GitHub Sync and Push v2.0
echo ==========================================
echo.

:: ---- CONFIGURE -----------------------------------------------------------
set "REPO_URL="
set "BRANCH=main"
set "COMMIT_MSG=Fixed Bugs and Added Features"
:: ---------------------------------------------------------------------------

if "%REPO_URL%"=="" (
    echo Enter your GitHub repository URL.
    echo Example: https://github.com/Mav1zz/oxygen.git
    echo.
    set /p REPO_URL="Repo URL: "
    echo.
)

if "%REPO_URL%"=="" (
    echo [ERROR] No repository URL entered.
    pause
    exit /b 1
)

git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] git not found. Download: https://git-scm.com/download/win
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('git --version 2^>^&1') do echo [OK] %%v

echo.
echo [INFO] Repository : %REPO_URL%
echo [INFO] Branch     : %BRANCH%
echo [INFO] Message    : %COMMIT_MSG%
echo.

:: ---- [1/6] Init or update remote -----------------------------------------
if not exist ".git" (
    echo [1/6] Initializing git repository...
    git init -b %BRANCH%
    if errorlevel 1 git init && git checkout -b %BRANCH% 2>nul
    git remote add origin %REPO_URL%
) else (
    echo [1/6] Git repo found.
    git remote set-url origin %REPO_URL% 2>nul || git remote add origin %REPO_URL%
)

:: ---- [2/6] Write .gitignore -----------------------------------------------
echo [2/6] Writing .gitignore...
(
    echo # Python
    echo __pycache__/
    echo *.pyc
    echo *.pyo
    echo # Build artifacts
    echo build/
    echo dist/
    echo *.egg-info/
    echo # Oxygen config
    echo .oxygen_cfg.json
    echo oxygen.py.backup
    echo # Cookies - do not commit
    echo cookies.txt
) > .gitignore

:: ---- [3/6] Stage files ----------------------------------------------------
echo [3/6] Staging project files...
echo.

git add oxygen.py        2>nul && echo [OK] oxygen.py
git add github_push.bat  2>nul && echo [OK] github_push.bat
git add build.bat        2>nul && echo [OK] build.bat
git add requirements.txt 2>nul && echo [OK] requirements.txt

if exist "oxygen.ico"  ( git add oxygen.ico  && echo [OK] oxygen.ico  )
if exist "oxygen.png"  ( git add oxygen.png  && echo [OK] oxygen.png  )
if exist "tr.ini"      ( git add tr.ini      && echo [OK] tr.ini      )
if exist "README.md"   ( git add README.md   && echo [OK] README.md   )
if exist ".gitignore"  ( git add .gitignore  && echo [OK] .gitignore  )

for %%f in (*.py) do (
    if /i not "%%f"=="oxygen.py" (
        git add "%%f" 2>nul && echo [OK] %%f
    )
)

for %%f in (*.ini) do (
    if /i not "%%f"==".gitignore" (
        git add "%%f" 2>nul && echo [OK] %%f
    )
)

echo.
echo [INFO] Checking binary file sizes...

for %%f in (ffmpeg.exe ffplay.exe ffprobe.exe) do (
    if exist "%%f" (
        for %%s in ("%%f") do set /a SIZE_MB=%%~zs / 1048576
        if !SIZE_MB! GTR 95 (
            echo [SKIP] %%f is !SIZE_MB! MB - over 100MB GitHub limit
        ) else (
            git add "%%f" 2>nul && echo [OK]   %%f  ^(!SIZE_MB! MB^)
        )
    )
)

for %%f in (avcodec-62.dll avdevice-62.dll avfilter-11.dll avformat-62.dll avutil-60.dll swresample-6.dll swscale-9.dll) do (
    if exist "%%f" (
        for %%s in ("%%f") do set /a SIZE_MB=%%~zs / 1048576
        if !SIZE_MB! GTR 95 (
            echo [SKIP] %%f is !SIZE_MB! MB - over 100MB GitHub limit
        ) else (
            git add "%%f" 2>nul && echo [OK]   %%f  ^(!SIZE_MB! MB^)
        )
    )
)

:: ---- [4/6] Show diff -------------------------------------------------------
echo.
echo [4/6] Changes to be committed:
git status --short
echo.

git diff --cached --quiet
if not errorlevel 1 (
    echo [INFO] Nothing new to commit - all files are already up to date.
    echo.
    goto :push
)

:: ---- [5/6] Commit ----------------------------------------------------------
echo [5/6] Committing...
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo [ERROR] Commit failed. Configure git user first:
    echo   git config --global user.email "you@email.com"
    echo   git config --global user.name  "YourName"
    pause
    exit /b 1
)

:: ---- [6/6] Push ------------------------------------------------------------
:push
echo.
echo [6/6] Pushing to GitHub...

git push -u origin %BRANCH%
if not errorlevel 1 goto :success

echo.
echo [INFO] Simple push failed - fetching remote first...
git fetch origin %BRANCH% 2>nul

:: Check if remote branch even exists yet
git ls-remote --heads origin %BRANCH% | findstr %BRANCH% >nul 2>&1
if errorlevel 1 (
    echo [INFO] Remote branch does not exist yet - creating...
    git push -u origin %BRANCH%
    if errorlevel 1 goto :push_failed
    goto :success
)

echo [INFO] Remote exists. Pulling then pushing...
git pull origin %BRANCH% --rebase --strategy-option=theirs 2>nul
if errorlevel 1 (
    echo [WARN] Rebase conflict - aborting and trying merge...
    git rebase --abort 2>nul
    git merge origin/%BRANCH% --strategy-option=theirs --no-edit 2>nul
)

git push -u origin %BRANCH%
if not errorlevel 1 goto :success

:: Last resort - force push with user confirmation
echo.
echo [WARN] Normal push still failed.
echo        Force push will OVERWRITE the remote with your local files.
echo.
set /p CONFIRM="Type YES to force push, anything else to cancel: "
if /i "%CONFIRM%"=="YES" (
    git push --force -u origin %BRANCH%
    if errorlevel 1 goto :push_failed
    goto :success
) else (
    echo [INFO] Cancelled.
    pause
    exit /b 0
)

:push_failed
echo.
echo ==========================================
echo [ERROR] Push FAILED. Check these:
echo.
echo   1. Repo URL is correct
echo   2. Git user configured:
echo        git config --global user.email "you@email.com"
echo        git config --global user.name  "YourName"
echo   3. Logged in to GitHub
echo   4. Internet connection is working
echo   5. avcodec-62.dll may be over 100MB (check [SKIP] lines)
echo.
echo   Large files - use Git LFS:
echo     git lfs install
echo     git lfs track "*.dll" "*.exe"
echo     (then re-run this script)
echo ==========================================
echo.
pause
exit /b 1

:success
echo.
echo ==========================================
echo   Push complete!
echo   %REPO_URL%
echo   Branch: %BRANCH%
echo ==========================================
echo.
pause
