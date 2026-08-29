@echo off
chcp 65001 >nul
title Stock Jus — Création installateur

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║      CREATION DE L'INSTALLATEUR          ║
echo  ║      StockJus_Setup_v5.exe                ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Vérifier que le .exe compilé existe
if not exist "dist\StockJus\StockJus.exe" (
    echo  [ERREUR] Le .exe n'a pas encore ete compile.
    echo  Lancez d'abord COMPILER_EXE.bat !
    pause & exit /b 1
)

:: Vérifier Inno Setup
set INNO="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO% (
    set INNO="C:\Program Files\Inno Setup 6\ISCC.exe"
)
if not exist %INNO% (
    echo  [ERREUR] Inno Setup n'est pas installe.
    echo  Telechargez-le sur : https://jrsoftware.org/isdl.php
    start https://jrsoftware.org/isdl.php
    pause & exit /b 1
)

mkdir installer 2>nul

echo  Compilation de l'installateur...
%INNO% stock_jus_setup.iss
if errorlevel 1 (
    echo  [ERREUR] La creation de l'installateur a echoue.
    pause & exit /b 1
)

echo.
echo  ════════════════════════════════════════════
echo   Installateur cree avec succes :
echo   installer\StockJus_Setup_v5.exe
echo  ════════════════════════════════════════════
echo.
echo  Distribuez ce fichier a vos utilisateurs !
echo.
pause
