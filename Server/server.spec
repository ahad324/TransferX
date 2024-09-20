# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os

iconpath = '../Logo/logo.ico'

a = Analysis(
    ['server.py', 'udp_connect.py','updater.py','developer_label.py'],  # Include udp_connect.py
    pathex=[os.path.dirname(os.path.abspath(__name__))],
    binaries=[],
    datas=[(iconpath, 'Logo')],  # Include logo
    hiddenimports=['requests','packaging'],  # Add any hidden imports required
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
    name='TransferXServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you need a console window for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=iconpath,  # Add icon to the executable
)