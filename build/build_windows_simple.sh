#!/bin/bash
# Build Windows executable - Simplified

set -e
cd /home/ial

echo "🪟 Building ialctl for Windows..."

VERSION=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
if [[ $(git status --porcelain 2>/dev/null) ]]; then
    VERSION="${VERSION}-dirty"
fi

echo "📦 Version: $VERSION"

# Create Windows dist directory
mkdir -p dist/windows

echo "🔨 Building Windows executable..."

# Simple PyInstaller build
pyinstaller --clean \
    --onefile \
    --name ialctl \
    --distpath dist/windows \
    --workpath build/build/windows \
    --hidden-import boto3 \
    --hidden-import yaml \
    --hidden-import openai \
    --console \
    natural_language_processor.py

# Create version file
echo "$VERSION" > dist/windows/VERSION

# Create Windows installer script
cat > dist/windows/install.ps1 << 'EOF'
# IAL Windows Installer
Write-Host "🚀 Installing IAL..." -ForegroundColor Green

if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Please run as Administrator" -ForegroundColor Red
    exit 1
}

$InstallDir = "C:\Program Files\IAL"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item "ialctl.exe" -Destination "$InstallDir\ialctl.exe" -Force

$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($CurrentPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$CurrentPath;$InstallDir", "Machine")
}

Write-Host "✅ IAL installed successfully!" -ForegroundColor Green
EOF

echo "✅ Windows build completed!"
ls -la dist/windows/
