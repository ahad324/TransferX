# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os

# Path to the virtual environment's site-packages
venv_site_packages = os.path.join('myenv', 'Lib', 'site-packages')

a = Analysis(
    ['client.py'],
    pathex=[os.path.dirname(os.path.abspath(__name__))],
    binaries=[],
    datas=collect_data_files('tkinterdnd2') + [('../Logo/logo.ico', 'Logo')],  # Include logo
    hiddenimports=['tkinterdnd2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../Logo/logo.ico',  # Add icon to the executable
)
