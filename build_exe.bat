@echo off
echo ============================================
echo  Packaging StockJus en .exe avec PyInstaller
echo ============================================
echo.

:: Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH.
    pause
    exit /b 1
)

:: Installer dependances
echo [1/3] Installation des dependances...
pip install reportlab pyinstaller --quiet

:: Lancer PyInstaller
echo [2/3] Compilation en .exe...
pyinstaller --onefile --windowed --name "StockJus" ^
    --add-data "src\frames;frames" ^
    src\main.py

echo.
echo [3/3] Termine !
echo.
if exist dist\StockJus.exe (
    echo  Votre fichier .exe se trouve dans : dist\StockJus.exe
    echo  Vous pouvez le copier n'importe ou et le lancer directement.
) else (
    echo  ATTENTION: Le fichier .exe n'a pas ete cree. Verifiez les erreurs ci-dessus.
)
echo.
pause
