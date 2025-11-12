#!/bin/bash
set -e

echo "🚀 Building IALCTL Complete Package"
echo "===================================="

# Version
VERSION="2.0.0"

# 1. Build binary with PyInstaller
echo ""
echo "📦 Step 1/3: Building binary..."
pyinstaller --onefile \
    --name ialctl \
    --add-data "config:config" \
    --add-data "phases:phases" \
    --hidden-import=boto3 \
    --hidden-import=yaml \
    --hidden-import=asyncio \
    ialctl

# 2. Create packages directory
echo ""
echo "📦 Step 2/3: Creating packages..."
mkdir -p dist/packages

# 3. Build .deb package
echo "Building .deb..."
fpm -s dir -t deb \
    --name ialctl \
    --version "$VERSION" \
    --description "IAL - Infrastructure as Language CLI" \
    --maintainer "IAL Team" \
    --license "MIT" \
    --architecture amd64 \
    --package "dist/packages/ialctl_${VERSION}_amd64.deb" \
    dist/ialctl=/usr/local/bin/ialctl

# 4. Build .rpm package
echo "Building .rpm..."
fpm -s dir -t rpm \
    --name ialctl \
    --version "$VERSION" \
    --description "IAL - Infrastructure as Language CLI" \
    --maintainer "IAL Team" \
    --license "MIT" \
    --architecture x86_64 \
    --package "dist/packages/ialctl-${VERSION}-1.x86_64.rpm" \
    dist/ialctl=/usr/local/bin/ialctl

echo ""
echo "✅ Build complete!"
echo "📁 Packages:"
ls -lh dist/packages/
