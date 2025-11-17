#!/bin/bash
# Build script para instalador IAL com otimizações DynamoDB

set -e

echo "🚀 Building IAL Installer with DynamoDB Optimizations..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ialctl __pycache__/

# Install/update dependencies (skip pip install due to managed environment)
echo "📦 Checking dependencies..."
python3 -c "import boto3, yaml" 2>/dev/null && echo "✅ Core dependencies available" || echo "⚠️ Some dependencies missing"

# Build with PyInstaller
echo "🔨 Building executable..."
pyinstaller ialctl.spec --clean --noconfirm

# Verify build
if [ -f "dist/ialctl" ]; then
    echo "✅ Build successful!"
    
    # Get file size
    SIZE=$(du -h dist/ialctl | cut -f1)
    echo "📊 Binary size: $SIZE"
    
    # Test basic functionality
    echo "🧪 Testing basic functionality..."
    ./dist/ialctl --help > /dev/null 2>&1 && echo "✅ Help command works" || echo "❌ Help command failed"
    
    # Copy to final location
    echo "📋 Copying to distribution directory..."
    cp dist/ialctl dist/ialctl-optimized-$(date +%Y%m%d)
    
    echo "🎉 IAL Installer with DynamoDB optimizations built successfully!"
    echo "📍 Location: $(pwd)/dist/ialctl"
    echo "📍 Backup: $(pwd)/dist/ialctl-optimized-$(date +%Y%m%d)"
    
else
    echo "❌ Build failed!"
    exit 1
fi
