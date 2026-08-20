@echo off
title Installation et lancement - LE ROCHER
color 0A
echo.
echo  ============================================
echo   LE ROCHER - Gestion de Stock Jus
echo  ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  Python non installe. Telechargement...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
    echo  Python installe !
) else (
    echo  [1/3] Python OK
)

echo  [2/3] Installation ReportLab...
pip install reportlab --quiet

echo  [3/3] Lancement du logiciel...
echo.
python src\main.py
pause
