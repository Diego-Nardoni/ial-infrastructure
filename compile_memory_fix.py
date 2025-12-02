#!/usr/bin/env python3
"""
Compilação MEMORY FIX - v3.14.2
Cria versão com sistema de memória funcional
"""

import os
import subprocess
import sys
from datetime import datetime

def main():
    print("🧠 MEMORY FIX Compilation - v3.14.2")
    print("=" * 50)
    
    os.chdir('/home/ial')
    
    # Update version following semantic versioning (SemVer)
    version = f"3.14.2+memory.{datetime.now().strftime('%Y%m%d')}"
    
    # Create spec file with memory integration
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

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
        'core.memory.memory_manager',
        'core.memory.context_engine',
        'natural_language_processor',
        'mcp_orchestrator',
        'mcp_registry'
    ],
    hookspath=[],
    hooksconfig={{}},
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
"""
    
    with open('ialctl-memory.spec', 'w') as f:
        f.write(spec_content)
    
    # Build with PyInstaller
    print("🔄 Building with memory integration...")
    result = subprocess.run("pyinstaller --clean ialctl-memory.spec", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Build failed: {result.stderr}")
        return False
    
    # Create .deb package
    print("📦 Creating .deb package...")
    
    pkg_dir = f"ialctl-{version}"
    os.makedirs(f"dist/{pkg_dir}/DEBIAN", exist_ok=True)
    os.makedirs(f"dist/{pkg_dir}/usr/local/bin", exist_ok=True)
    
    # Copy binary
    subprocess.run(f"cp dist/ialctl dist/{pkg_dir}/usr/local/bin/", shell=True, check=True)
    
    # Create control file
    control_content = f"""Package: ialctl
Version: {version}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: IAL Team <ial@example.com>
Description: IAL Infrastructure Assistant with Infinite Memory
 v3.14.2+memory Implementation - Complete Memory Integration
 .
 Features:
 - Infinite conversation memory with DynamoDB + S3
 - Intent detection for query vs create operations
 - Professional CI/CD mode with ialctl ci commands
 - Memory queries: "quais foram minhas ultimas solicitações?"
 - Auto-save all conversations with semantic search
 - Cost: $0.15/user/month for infinite memory
"""
    
    with open(f"dist/{pkg_dir}/DEBIAN/control", 'w') as f:
        f.write(control_content)
    
    # Build .deb
    subprocess.run(f"dpkg-deb --build dist/{pkg_dir}", shell=True, check=True)
    
    # Move to packages directory
    os.makedirs("dist/packages", exist_ok=True)
    subprocess.run(f"mv dist/{pkg_dir}.deb dist/packages/ialctl-{version}.deb", shell=True, check=True)
    
    print(f"🎉 MEMORY FIX Compilation Complete!")
    print(f"📦 Package: dist/packages/ialctl-{version}.deb")
    print(f"🧠 Memory: Infinite conversation history")
    print(f"🔧 Install: dpkg -i dist/packages/ialctl-{version}.deb")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
