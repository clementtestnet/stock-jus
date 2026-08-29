@echo off
chcp 65001 >nul
title Stock Jus — Compilation EXE

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║       COMPILATION STOCK JUS .EXE         ║
echo  ║       Powered by PyInstaller              ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo  Telechargez Python sur https://python.org
    pause & exit /b 1
)

:: Installer les dépendances
echo  [1/4] Installation des dependances...
pip install pyinstaller customtkinter reportlab pillow --quiet
if errorlevel 1 (
    echo  [ERREUR] Echec d'installation des dependances.
    pause & exit /b 1
)

:: Nettoyer les anciens builds
echo  [2/4] Nettoyage des anciens builds...
if exist "dist\StockJus" rmdir /s /q "dist\StockJus"
if exist "build\StockJus" rmdir /s /q "build\StockJus"

:: Compiler avec PyInstaller
echo  [3/4] Compilation en cours (peut prendre 2-3 minutes)...
python -m PyInstaller stock_jus.spec --noconfirm --clean
if errorlevel 1 (
    echo  [ERREUR] La compilation a echoue.
    echo  Consultez les logs ci-dessus pour plus de details.
    pause & exit /b 1
)

:: Copier la base de données si elle existe
echo  [4/4] Finalisation...
if exist "stock_jus.db" copy /y "stock_jus.db" "dist\StockJus\" >nul

:: Créer un raccourci dans dist
echo  [OK] Compilation terminee !
echo.
echo  ════════════════════════════════════════════
echo   Votre application est dans :
echo   dist\StockJus\StockJus.exe
echo  ════════════════════════════════════════════
echo.
echo  Vous pouvez maintenant :
echo   1. Copier le dossier dist\StockJus sur n'importe quel PC
echo   2. Lancer StockJus.exe
echo   3. Ou utiliser CREER_INSTALLATEUR.bat pour un .exe d'installation
echo.

:: Proposer de lancer directement
set /p LANCER="  Lancer l'application maintenant ? (o/n) : "
if /i "%LANCER%"=="o" start "" "dist\StockJus\StockJus.exe"

pause
