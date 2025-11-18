# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ialctl_integrated.py'],
    pathex=['/home/ial'],
    binaries=[],
    datas=[
        ('phases', 'phases'),
        ('core', 'core'),
        ('config', 'config'),
        ('natural_language_processor.py', '.'),
    ],
    hiddenimports=[
        'natural_language_processor',
        'core.foundation_deployer',
        'core.phase_parser',
        'core.ial_master_engine_integrated',
        'boto3',
        'botocore',
        'yaml',
        'asyncio',
    ],
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
