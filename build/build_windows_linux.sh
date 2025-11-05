#!/bin/bash
# Build Windows executable on Linux using PyInstaller

set -e

cd /home/ial

echo "🪟 Building ialctl for Windows (cross-platform)..."

# Get version
VERSION=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
if [[ $(git status --porcelain 2>/dev/null) ]]; then
    VERSION="${VERSION}-dirty"
fi

echo "📦 Version: $VERSION"

# Create Windows dist directory
mkdir -p dist/windows

echo "🔨 Building Windows executable with PyInstaller..."

# Build with Windows-specific spec
pyinstaller --clean \
    --onefile \
    --name ialctl \
    --distpath dist/windows \
    --workpath build/build/windows \
    --specpath build \
    --add-data "config:config" \
    --add-data "templates:templates" \
    --add-data "schemas:schemas" \
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
Write-Host "🚀 Installing IAL (Infrastructure as Language)..." -ForegroundColor Green

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Please run as Administrator" -ForegroundColor Red
    exit 1
}

# Create program directory
$InstallDir = "C:\Program Files\IAL"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# Copy executable
Copy-Item "ialctl.exe" -Destination "$InstallDir\ialctl.exe" -Force

# Add to PATH
$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($CurrentPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$CurrentPath;$InstallDir", "Machine")
    Write-Host "✅ Added IAL to system PATH" -ForegroundColor Green
}

Write-Host "✅ IAL installed successfully!" -ForegroundColor Green
Write-Host "Open a new Command Prompt or PowerShell and run: ialctl" -ForegroundColor Yellow
EOF

echo "🧪 Creating Windows test script..."
cat > dist/windows/test.bat << 'EOF'
@echo off
echo Testing IAL Windows build...
ialctl.exe --help
if %ERRORLEVEL% EQU 0 (
    echo ✅ Windows build test passed
) else (
    echo ❌ Windows build test failed
)
pause
EOF

echo "✅ Windows build completed!"
echo "📁 Files created in dist/windows/:"
ls -la dist/windows/
