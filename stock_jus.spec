# stock_jus.spec — PyInstaller config pour Stock Jus
# Usage : pyinstaller stock_jus.spec --noconfirm --clean

import os, sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ---------- chemins ----------
BASE = os.path.abspath('.')
SRC  = os.path.join(BASE, 'src')
ASSETS = os.path.join(BASE, 'assets')

# ---------- données extra ----------
extra_datas = []

# Customtkinter (thèmes + polices)
try:
    import customtkinter
    ctk_dir = os.path.dirname(customtkinter.__file__)
    extra_datas += collect_data_files('customtkinter', includes=['**/*'])
except ImportError:
    pass

# Polices / assets locaux
if os.path.exists(ASSETS):
    extra_datas.append((ASSETS, 'assets'))

# ---------- imports cachés ----------
hidden = [
    'customtkinter',
    'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
    'reportlab', 'reportlab.lib', 'reportlab.lib.pagesizes',
    'reportlab.lib.colors', 'reportlab.lib.styles',
    'reportlab.lib.units', 'reportlab.platypus',
    'reportlab.pdfgen', 'reportlab.pdfgen.canvas',
    'sqlite3', 'hashlib', 'threading', 'datetime', 'os', 'sys',
    'PIL', 'PIL.Image', 'PIL.ImageTk',
]
hidden += collect_submodules('customtkinter')

# ---------- analyse ----------
a = Analysis(
    [os.path.join(SRC, 'main.py')],
    pathex=[BASE, SRC, os.path.join(SRC, 'frames')],
    binaries=[],
    datas=extra_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'test', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

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
    icon=os.path.join(ASSETS, 'icon.ico'),
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
