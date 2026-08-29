@echo off
chcp 65001 >nul
title Stock Jus — Lancement

:: Vérifier si le .exe compilé existe
if exist "dist\StockJus\StockJus.exe" (
    echo  Lancement de Stock Jus (version compilee)...
    start "" "dist\StockJus\StockJus.exe"
    exit /b 0
)

:: Sinon lancer en Python
echo  Version compilee non trouvee.
echo  Lancement en mode Python...
echo.

:: Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERREUR] Python n'est pas installe.
    echo  Telechargez Python sur https://python.org
    pause & exit /b 1
)

:: Installer les dépendances si besoin
echo  Installation des librairies...
pip install customtkinter reportlab --quiet

:: Lancer l'application
echo  Demarrage...
cd src
python main.py
cd ..
