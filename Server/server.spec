# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import os

iconpath = '../Logo/logo.ico'

a = Analysis(
    ['server.py', 'mdns_connect.py','updater.py','developer_label.py'],
    pathex=[os.path.dirname(os.path.abspath(__name__))],
    binaries=[],
    datas=[(iconpath, 'Logo')],  # Include logo
    hiddenimports=['requests','packaging','zeroconf', 'zeroconf._utils','zeroconf._utils.ipaddress', 'zeroconf._services', 'zeroconf._core', 'zeroconf._engine', 'zeroconf._listener','zeroconf._handlers.answers'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib','numpy','pandas','scipy','PIL','cryptography'],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=iconpath,
)