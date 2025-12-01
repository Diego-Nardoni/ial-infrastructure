#!/usr/bin/env python3
"""
Compilação do PROMPT 4 - Bedrock Agent Integration
Atualiza o .deb com as implementações completas
"""

import os
import subprocess
import sys
from datetime import datetime

def run_command(cmd, description):
    """Execute command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False

def main():
    print("🚀 PROMPT 4 Compilation - Bedrock Agent Integration")
    print("=" * 60)
    
    # Change to IAL directory
    os.chdir('/home/ial')
    
    # Step 1: Validate templates
    print("\n1️⃣ Validating CloudFormation templates...")
    templates = [
        'phases/00-foundation/44-bedrock-agent-core.yaml',
        'phases/00-foundation/43-bedrock-agent-lambda.yaml'
    ]
    
    for template in templates:
        if os.path.exists(template):
            print(f"✅ {template} exists")
        else:
            print(f"❌ {template} missing")
            return False
    
    # Step 2: Test Foundation Deployer
    print("\n2️⃣ Testing Foundation Deployer integration...")
    test_cmd = '''python3 -c "
import sys
sys.path.insert(0, '/home/ial')
from core.foundation_deployer import FoundationDeployer
deployer = FoundationDeployer()
print('✅ Foundation Deployer with Bedrock Agent support loaded')
"'''
    
    if not run_command(test_cmd, "Foundation Deployer test"):
        return False
    
    # Step 3: Update version
    print("\n3️⃣ Updating version...")
    version = f"3.13.0-PROMPT4-{datetime.now().strftime('%Y%m%d')}"
    
    # Step 4: Build new .deb
    print("\n4️⃣ Building updated .deb package...")
    
    # Update spec file
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
    ],
    hiddenimports=[
        'core.foundation_deployer',
        'core.bedrock_agent_core', 
        'core.enhanced_fallback_system',
        'core.agent_tools_lambda',
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
    
    with open('ialctl-prompt4.spec', 'w') as f:
        f.write(spec_content)
    
    # Build with PyInstaller
    if not run_command("pyinstaller --clean ialctl-prompt4.spec", "PyInstaller build"):
        return False
    
    # Create .deb package
    print("\n5️⃣ Creating .deb package...")
    
    # Create package structure
    pkg_dir = f"ialctl-{version}"
    os.makedirs(f"dist/{pkg_dir}/DEBIAN", exist_ok=True)
    os.makedirs(f"dist/{pkg_dir}/usr/local/bin", exist_ok=True)
    
    # Copy binary
    if not run_command(f"cp dist/ialctl dist/{pkg_dir}/usr/local/bin/", "Copy binary"):
        return False
    
    # Create control file
    control_content = f"""Package: ialctl
Version: {version}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: IAL Team <ial@example.com>
Description: IAL Infrastructure Assistant with Bedrock Agent Core
 PROMPT 4 Implementation - Complete Bedrock Agent Integration
 .
 Features:
 - CloudFormation-first Bedrock Agent deployment
 - Enhanced Fallback System (AGENT_CORE → FALLBACK_NLP → SANDBOX)
 - Agent Tools Lambda with IAL operations
 - Local agent configuration management
 - Idempotent ialctl start command
"""
    
    with open(f"dist/{pkg_dir}/DEBIAN/control", 'w') as f:
        f.write(control_content)
    
    # Build .deb
    if not run_command(f"dpkg-deb --build dist/{pkg_dir}", "Build .deb package"):
        return False
    
    # Move to packages directory
    os.makedirs("dist/packages", exist_ok=True)
    if not run_command(f"mv dist/{pkg_dir}.deb dist/packages/ialctl-{version}.deb", "Move package"):
        return False
    
    print(f"\n🎉 PROMPT 4 Compilation Complete!")
    print(f"📦 Package: dist/packages/ialctl-{version}.deb")
    print(f"🧠 Features: Bedrock Agent Core integration via CloudFormation")
    print(f"🔄 Fallback: AGENT_CORE → FALLBACK_NLP → SANDBOX")
    print(f"⚙️  Config: ~/.ial/agent_config.json")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
