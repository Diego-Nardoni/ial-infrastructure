# -*- mode: python ; coding: utf-8 -*-

# Collect all files from core/, lib/, cdk/, lambda/ directories
import os

def collect_files(directory, extensions=['.py']):
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                full_path = os.path.join(root, filename)
                files.append((full_path, root))
    return files

# Collect all necessary files
core_files = collect_files('core')
lib_files = collect_files('lib') 
cdk_files = collect_files('cdk', ['.py', '.json', '.txt'])
lambda_files = collect_files('lambda')
phase_files = collect_files('phases', ['.yaml'])

a = Analysis(
    ['natural_language_processor.py'],
    pathex=['/home/ial'],
    binaries=[],
    datas=core_files + lib_files + cdk_files + lambda_files + phase_files + [
        ('parameters.env', '.'),
        ('README.md', '.'),
        ('requirements.txt', '.')
    ],
    hiddenimports=[
        'boto3', 
        'yaml', 
        'openai',
        'requests',
        'aws_cdk',
        'aws_cdk_lib',
        'constructs',
        'core.github_integration',
        'core.intent_parser', 
        'core.template_generator',
        'core.cdk_deployment_manager',
        'lib.ial_master_engine'
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
