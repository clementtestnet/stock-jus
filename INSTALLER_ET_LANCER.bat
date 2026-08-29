@echo off
chcp 65001 >nul
title Stock Jus — Lancer

:: Aller dans le dossier du script
cd /d "%~dp0"

:: Vérifier si l'application compilée existe
if exist "dist\StockJus\StockJus.exe" (
    start "" "dist\StockJus\StockJus.exe"
    exit /b 0
)

:: Sinon lancer depuis le code source Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python non trouvé. Téléchargez-le sur https://python.org
    pause & exit /b 1
)

pip install customtkinter reportlab pillow --quiet
python src\main.py
