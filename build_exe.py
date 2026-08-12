## Prérequis Windows
## pip install reportlab pyinstaller

import PyInstaller.__main__
import os

src = os.path.join(os.path.dirname(__file__), "src", "main.py")

PyInstaller.__main__.run([
    src,
    "--onefile",
    "--windowed",
    "--name", "StockJus",
    "--add-data", r"src\frames;frames",
    "--hidden-import", "reportlab",
    "--hidden-import", "reportlab.pdfbase._fontdata",
    "--hidden-import", "reportlab.lib.styles",
    "--clean",
])
print("\n✅ Packaging terminé. Consultez le dossier dist/")
