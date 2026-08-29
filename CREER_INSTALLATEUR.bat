@echo off
chcp 65001 >nul
title Stock Jus — Créer l'installateur Windows

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   🧃 STOCK JUS — CRÉER SETUP.EXE             ║
echo  ║   Génère un installateur professionnel        ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Vérifier que le .exe compilé existe
if not exist "dist\StockJus\StockJus.exe" (
    echo  ❌ dist\StockJus\StockJus.exe introuvable !
    echo.
    echo  Lancez d'abord COMPILER_EXE.bat pour compiler l'application.
    pause & exit /b 1
)
echo  ✅ Application compilée détectée

:: Chercher Inno Setup
set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe
if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 5\ISCC.exe

if "%ISCC%"=="" (
    echo.
    echo  ❌ Inno Setup introuvable sur ce PC.
    echo.
    echo  Téléchargez-le gratuitement :
    echo  👉  https://jrsoftware.org/isdl.php
    echo.
    echo  Après installation, relancez ce script.
    pause & exit /b 1
)
echo  ✅ Inno Setup trouvé

:: Compiler l'installateur
echo.
echo  Création du setup.exe en cours...
"%ISCC%" stock_jus_setup.iss
if errorlevel 1 (
    echo  ❌ Échec de la création de l'installateur.
    pause & exit /b 1
)

echo.
echo  ════════════════════════════════════════════════
echo    ✅ INSTALLATEUR CRÉÉ AVEC SUCCÈS !
echo.
echo    📁 Fichier : dist\StockJus_Setup_v5.0.exe
echo.
echo    Vous pouvez partager ce fichier — il s'installe
echo    sur n'importe quel PC Windows 10/11 en 2 clics.
echo  ════════════════════════════════════════════════
echo.

if exist "dist\StockJus_Setup_v5.0.exe" (
    set /p OUVRIR="  Ouvrir le dossier dist\ maintenant ? (o/n) : "
    if /i "!OUVRIR!"=="o" explorer dist\
)

pause
