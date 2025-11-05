# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))
sys.path.insert(0, project_root)

block_cipher = None

a = Analysis(
    ['../natural_language_processor.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        ('../config', 'config'),
        ('../phases', 'phases'),
        ('../templates', 'templates'),
        ('../schemas', 'schemas'),
        ('../rules', 'rules'),
    ],
    hiddenimports=[
        'boto3',
        'botocore',
        'yaml',
        'json',
        'readline',
        'uuid',
        'datetime',
        'typing',
        'pathlib',
        'subprocess',
        'requests',
        'openai',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ialctl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
