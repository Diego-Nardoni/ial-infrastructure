#!/usr/bin/env python3
"""
Cross-platform build script for Windows
"""
import subprocess
import sys
import os

def build_windows():
    """Build Windows executable"""
    print("🔨 Building Windows executable...")
    
    # Use wine + PyInstaller for Windows build
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name', 'ialctl',
        '--distpath', 'dist/windows',
        '--hidden-import=boto3',
        '--hidden-import=yaml', 
        '--hidden-import=openai',
        '--hidden-import=core.github_integration',
        '--hidden-import=core.intent_parser',
        '--hidden-import=core.template_generator',
        '--hidden-import=core.cdk_deployment_manager',
        '--hidden-import=lib.ial_master_engine',
        'natural_language_processor.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # Rename to .exe
        os.rename('dist/windows/ialctl', 'dist/windows/ialctl.exe')
        print("✅ Windows build completed")
        return True
    else:
        print(f"❌ Windows build failed: {result.stderr}")
        return False

if __name__ == "__main__":
    build_windows()
