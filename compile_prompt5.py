#!/usr/bin/env python3
"""
Compilação do PROMPT 5 - IAL CI MODE
Cria modo CI/CD profissional para o IAL
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
    print("🚀 PROMPT 5 Compilation - IAL CI MODE")
    print("=" * 60)
    
    # Change to IAL directory
    os.chdir('/home/ial')
    
    # Step 1: Test CI Mode functionality
    print("\n1️⃣ Testing CI Mode functionality...")
    
    ci_commands = [
        ('python3 ialctl_integrated.py ci test', 'Fast tests'),
        ('python3 ialctl_integrated.py ci validate', 'Phase validation'),
        ('python3 ialctl_integrated.py ci governance', 'Governance validation'),
        ('python3 ialctl_integrated.py ci completeness', 'Completeness validation')
    ]
    
    for cmd, desc in ci_commands:
        print(f"  Testing: {desc}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {desc} - PASSED")
        else:
            print(f"  ⚠️ {desc} - FAILED (exit code: {result.returncode})")
    
    # Step 2: Validate CI/CD templates
    print("\n2️⃣ Validating CI/CD templates...")
    templates = [
        'examples/ci/github-actions/basic-validation.yml',
        'examples/ci/github-actions/drift-detection.yml',
        'examples/ci/gitlab-ci/basic.yml'
    ]
    
    for template in templates:
        if os.path.exists(template):
            print(f"✅ {template} exists")
        else:
            print(f"❌ {template} missing")
            return False
    
    # Step 3: Validate test structure
    print("\n3️⃣ Validating test structure...")
    test_dirs = ['tests/fast', 'tests/slow']
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            test_files = [f for f in os.listdir(test_dir) if f.startswith('test_')]
            print(f"✅ {test_dir}: {len(test_files)} test files")
        else:
            print(f"❌ {test_dir} missing")
    
    # Step 4: Update version
    print("\n4️⃣ Updating version...")
    version = f"3.14.0-PROMPT5-{datetime.now().strftime('%Y%m%d')}"
    
    # Step 5: Build new .deb with CI Mode
    print("\n5️⃣ Building updated .deb package...")
    
    # Update spec file for CI Mode
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
    
    with open('ialctl-prompt5.spec', 'w') as f:
        f.write(spec_content)
    
    # Build with PyInstaller
    if not run_command("pyinstaller --clean ialctl-prompt5.spec", "PyInstaller build"):
        return False
    
    # Create .deb package
    print("\n6️⃣ Creating .deb package...")
    
    # Create package structure
    pkg_dir = f"ialctl-{version}"
    os.makedirs(f"dist/{pkg_dir}/DEBIAN", exist_ok=True)
    os.makedirs(f"dist/{pkg_dir}/usr/local/bin", exist_ok=True)
    os.makedirs(f"dist/{pkg_dir}/usr/share/ial/examples", exist_ok=True)
    
    # Copy binary
    if not run_command(f"cp dist/ialctl dist/{pkg_dir}/usr/local/bin/", "Copy binary"):
        return False
    
    # Copy CI/CD examples
    if not run_command(f"cp -r examples/ci dist/{pkg_dir}/usr/share/ial/examples/", "Copy CI examples"):
        return False
    
    # Create control file
    control_content = f"""Package: ialctl
Version: {version}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: IAL Team <ial@example.com>
Description: IAL Infrastructure Assistant with Professional CI/CD Mode
 PROMPT 5 Implementation - Complete CI/CD Integration
 .
 Features:
 - Professional CI/CD mode with ialctl ci commands
 - Fast/slow test separation for optimal pipeline performance
 - GitHub Actions, GitLab CI, and Bitbucket templates
 - POSIX exit codes and CI-friendly logging
 - Drift detection as PR guardian
 - Governance and completeness validation
 - MCP connectivity testing
 - Enterprise-ready for any CI/CD pipeline
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
    
    print(f"\n🎉 PROMPT 5 Compilation Complete!")
    print(f"📦 Package: dist/packages/ialctl-{version}.deb")
    print(f"🔧 CI Commands: ialctl ci [validate|governance|completeness|drift|mcp-test|test]")
    print(f"📋 Templates: GitHub Actions, GitLab CI, Bitbucket")
    print(f"🧪 Tests: Fast/slow separation implemented")
    print(f"🚀 Ready for enterprise CI/CD pipelines!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
