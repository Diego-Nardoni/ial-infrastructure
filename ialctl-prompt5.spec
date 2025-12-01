# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ialctl_integrated.py'],
    pathex=['/home/ial'],
    binaries=[],
    datas=[
        ('phases', 'phases'),
        ('core', 'core'),
        ('config', 'config'),
        ('templates', 'templates'),
        ('schemas', 'schemas'),
        ('examples', 'examples'),
        ('tests/fast', 'tests/fast'),
    ],
    hiddenimports=[
        'core.foundation_deployer',
        'core.bedrock_agent_core', 
        'core.enhanced_fallback_system',
        'core.agent_tools_lambda',
        'core.ci_mode',
        'natural_language_processor',
        'mcp_orchestrator',
        'mcp_registry'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
