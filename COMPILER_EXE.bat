@echo off
chcp 65001 >nul
title Stock Jus — Compilation EXE Windows

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║       🧃 STOCK JUS — COMPILATION .EXE        ║
echo  ║       Génère une vraie application Windows    ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ── Vérifier Python ────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Python introuvable.  Téléchargez-le sur https://python.org
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  ✅ %%v détecté

:: ── Installer les dépendances ───────────────────────────────────
echo.
echo  [1/5] Installation des dépendances Python...
pip install --upgrade pyinstaller customtkinter reportlab pillow --quiet
if errorlevel 1 (
    echo  ❌ Échec pip install.
    pause & exit /b 1
)
echo  ✅ Dépendances OK

:: ── Nettoyer les anciens builds ─────────────────────────────────
echo.
echo  [2/5] Nettoyage des anciens builds...
if exist "dist\StockJus" rmdir /s /q "dist\StockJus"
if exist "build\StockJus" rmdir /s /q "build\StockJus"
echo  ✅ Nettoyage OK

:: ── Générer l'icône si absente ──────────────────────────────────
echo.
echo  [3/5] Vérification de l'icône...
if not exist "assets\icon.ico" (
    echo  ⚠️  assets\icon.ico absent — génération automatique...
    python -c "
from PIL import Image, ImageDraw
sizes = [16,32,48,64,128,256]
imgs = []
for s in sizes:
    img = Image.new('RGBA',(s,s),(0,0,0,0))
    d = ImageDraw.Draw(img)
    d.ellipse([2,2,s-2,s-2], fill='#1f6aa5')
    imgs.append(img)
imgs[0].save('assets/icon.ico', format='ICO', sizes=[(s,s) for s in sizes], append_images=imgs[1:])
print('Icone generee.')
"
    if errorlevel 1 echo  ⚠️  Icône non générée, on continue sans icône.
)
echo  ✅ Icône OK

:: ── Compiler avec PyInstaller ───────────────────────────────────
echo.
echo  [4/5] Compilation en cours (2-5 min selon votre PC)...
python -m PyInstaller stock_jus.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo  ❌ La compilation a échoué — lisez les erreurs ci-dessus.
    pause & exit /b 1
)
echo  ✅ Compilation terminée

:: ── Finalisation ────────────────────────────────────────────────
echo.
echo  [5/5] Finalisation...

:: Copier la base de données si elle existe
if exist "stock_jus.db" (
    copy /y "stock_jus.db" "dist\StockJus\" >nul
    echo  ✅ Base de données copiée
)

:: Vérifier que l'exe existe vraiment
if not exist "dist\StockJus\StockJus.exe" (
    echo  ❌ StockJus.exe introuvable dans dist\StockJus\ !
    pause & exit /b 1
)

echo.
echo  ════════════════════════════════════════════════
echo    ✅ APPLICATION CRÉÉE AVEC SUCCÈS !
echo.
echo    📁 Emplacement : dist\StockJus\StockJus.exe
echo.
echo    Pour distribuer :
echo      • Copiez tout le dossier dist\StockJus\
echo      • Ou lancez CREER_INSTALLATEUR.bat
echo        pour créer un setup.exe clé-en-main
echo  ════════════════════════════════════════════════
echo.

set /p LANCER="  Lancer l'application maintenant ? (o/n) : "
if /i "%LANCER%"=="o" (
    start "" "dist\StockJus\StockJus.exe"
)

echo.
pause
