# stock_jus.spec — Configuration PyInstaller pour Stock Jus
# Ce fichier est utilisé par PyInstaller pour créer le .exe Windows
# Exécuter : pyinstaller stock_jus.spec

import os

block_cipher = None

# Collecte tous les fichiers sources
a = Analysis(
    ['src/main.py'],
    pathex=['.', 'src', 'src/frames'],
    binaries=[],
    datas=[
        # Inclure customtkinter (thèmes + assets)
        ('src', 'src'),
    ],
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.colors',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.platypus',
        'sqlite3',
        'hashlib',
        'threading',
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Ajouter les assets de customtkinter automatiquement
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)
a.datas += Tree(ctk_path, prefix='customtkinter')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StockJus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # Pas de fenêtre console noire
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico', # Icône de l'application
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StockJus',
)
