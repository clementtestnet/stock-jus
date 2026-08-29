@echo off
chcp 65001 >nul
title Stock Jus — Lancement intelligent

cd /d "%~dp0"

:: ── Chercher Python dans les emplacements courants ───────────────
set PY=

:: 1. Python dans le PATH ?
python --version >nul 2>&1
if not errorlevel 1 set PY=python

:: 2. py launcher (Windows) ?
if "%PY%"=="" (
    py --version >nul 2>&1
    if not errorlevel 1 set PY=py
)

:: 3. Chemins typiques d'installation
if "%PY%"=="" (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "C:\Python313\python.exe"
        "C:\Python312\python.exe"
        "C:\Python311\python.exe"
        "C:\Python310\python.exe"
        "C:\Program Files\Python313\python.exe"
        "C:\Program Files\Python312\python.exe"
    ) do (
        if exist %%P set PY=%%P
    )
)

:: ── Python trouvé ? ──────────────────────────────────────────────
if "%PY%"=="" (
    echo.
    echo  ❌ Python introuvable sur ce PC.
    echo.
    echo  ════════════════════════════════════════════
    echo   Pour installer Python :
    echo   1. Allez sur https://python.org/downloads
    echo   2. Téléchargez la dernière version
    echo   3. IMPORTANT : cochez "Add Python to PATH"
    echo   4. Cliquez "Install Now"
    echo   5. Relancez ce fichier .bat
    echo  ════════════════════════════════════════════
    echo.
    start https://python.org/downloads
    pause
    exit /b 1
)

echo  ✅ Python trouvé : %PY%
echo.

:: ── Installer les dépendances (toujours) ─────────────────────────
echo  Installation / vérification des dépendances...
%PY% -m pip install customtkinter reportlab pillow pyinstaller --quiet
if errorlevel 1 (
    echo  ❌ Échec installation pip.
    pause & exit /b 1
)
echo  ✅ Dépendances OK
echo.

:: ── Compiler si .exe absent ───────────────────────────────────────
if not exist "dist\StockJus\StockJus.exe" (
    echo  Compilation en cours — patientez 2 à 5 minutes...
    echo.
    %PY% -m PyInstaller stock_jus.spec --noconfirm --clean
    if errorlevel 1 (
        echo.
        echo  ❌ Compilation échouée. Lisez les erreurs ci-dessus.
        pause & exit /b 1
    )
    if exist "stock_jus.db" copy /y "stock_jus.db" "dist\StockJus\" >nul
    echo.
    echo  ✅ Compilation terminée !
) else (
    echo  ✅ Application déjà compilée.
)

echo.

:: ── Vérification finale ───────────────────────────────────────────
if not exist "dist\StockJus\StockJus.exe" (
    echo  ❌ dist\StockJus\StockJus.exe toujours absent après compilation.
    echo  Quelque chose a mal tourné — lisez les messages ci-dessus.
    pause & exit /b 1
)

echo  Lancement de Stock Jus...
start "" "dist\StockJus\StockJus.exe"
