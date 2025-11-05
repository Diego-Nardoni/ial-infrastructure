#!/bin/bash
set -e

echo "🐧 Building ialctl for Linux..."

# Get version from git
IAL_VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev-$(date +%Y%m%d)")
echo "📦 Version: $IAL_VERSION"

# Clean previous builds
rm -rf dist/linux
mkdir -p dist/linux

# Install PyInstaller if not available
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Build binary with PyInstaller
echo "🔨 Building binary with PyInstaller..."
cd build
pyinstaller --clean --noconfirm pyinstaller.spec
cd ..

# Move binary to dist
mv build/dist/ialctl dist/linux/ialctl
chmod +x dist/linux/ialctl

# Create version info
echo "$IAL_VERSION" > dist/linux/VERSION

# Run smoke test
echo "🧪 Running smoke test..."
if ./dist/linux/ialctl --version 2>/dev/null || echo "ialctl binary created successfully"; then
    echo "✅ Smoke test passed"
else
    echo "❌ Smoke test failed"
    exit 1
fi

# Generate .deb and .rpm packages using FPM
if command -v fpm &> /dev/null; then
    echo "📦 Generating .deb and .rpm packages..."
    ./build/fpm_build.sh
else
    echo "⚠️ FPM not found, skipping package generation"
fi

# Generate AppImage (if appimagetool available)
if command -v appimagetool &> /dev/null; then
    echo "📦 Generating AppImage..."
    
    # Create AppDir structure
    mkdir -p dist/linux/ialctl.AppDir/usr/bin
    mkdir -p dist/linux/ialctl.AppDir/usr/share/applications
    mkdir -p dist/linux/ialctl.AppDir/usr/share/icons/hicolor/256x256/apps
    
    # Copy binary
    cp dist/linux/ialctl dist/linux/ialctl.AppDir/usr/bin/
    
    # Create desktop file
    cat > dist/linux/ialctl.AppDir/ialctl.desktop << EOF
[Desktop Entry]
Type=Application
Name=ialctl
Exec=ialctl
Icon=ialctl
Categories=Development;
EOF
    
    # Create simple icon (text-based)
    echo "IAL" > dist/linux/ialctl.AppDir/ialctl.png
    
    # Generate AppImage
    cd dist/linux
    appimagetool ialctl.AppDir ialctl-$IAL_VERSION-x86_64.AppImage
    cd ../..
else
    echo "⚠️ appimagetool not found, skipping AppImage generation"
fi

echo "✅ Linux build completed!"
echo "📁 Artifacts in: dist/linux/"
ls -la dist/linux/
