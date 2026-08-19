@echo off
title Installation Stock Jus
color 0A
echo.
echo  =============================================
echo   INSTALLATION STOCK JUS - Jus en Bouteille
echo  =============================================
echo.

:: Etape 1 - Verifier Python
echo [1/4] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  PYTHON N'EST PAS INSTALLE !
    echo.
    echo  Telechargement automatique de Python...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    echo  Installation de Python...
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
    echo  Python installe !
) else (
    echo  Python est deja installe. OK !
)

:: Etape 2 - Installer ReportLab
echo.
echo [2/4] Installation de ReportLab...
pip install reportlab --quiet
echo  ReportLab installe !

:: Etape 3 - Verifier les fichiers
echo.
echo [3/4] Verification des fichiers...
if not exist "src\main.py" (
    echo  ERREUR: Fichier src\main.py introuvable !
    echo  Assurez-vous d'etre dans le bon dossier.
    pause
    exit /b 1
)
echo  Tous les fichiers sont presents !

:: Etape 4 - Lancer le logiciel
echo.
echo [4/4] Lancement du logiciel...
echo.
echo  =============================================
echo   STOCK JUS DEMARRE !
echo  =============================================
echo.
python src\main.py

pause
