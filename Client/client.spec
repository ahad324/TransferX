# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os

# Path to the virtual environment's site-packages
venv_site_packages = os.path.join('myenv', 'Lib', 'site-packages')

iconpath = '../Logo/logo.ico'

a = Analysis(
    ['client.py', 'udp_connect.py','updater.py','developer_label.py'],  # Include udp_connect.py
    pathex=[os.path.dirname(os.path.abspath(__name__))],
    binaries=[],
    datas=collect_data_files('tkinterdnd2') + [(iconpath, 'Logo')],  # Include logo
    hiddenimports=['tkinterdnd2','requests','packaging'],
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
    name='TransferX',
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
    icon=iconpath,  # Add icon to the executable
)
