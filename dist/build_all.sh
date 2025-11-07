#!/bin/bash
# Build all IAL v3.1 distribution packages

set -e

echo "🚀 Building IAL v3.1 distribution packages..."

# Build Linux binary
echo "📦 Building Linux binary..."
cd /home/ial
source venv/bin/activate
pyinstaller ialctl.spec --clean --onefile
cp dist/ialctl dist/linux/ialctl

# Build Windows binary (if wine available)
if command -v wine >/dev/null 2>&1; then
    echo "📦 Building Windows binary..."
    # Note: Requires wine and Windows Python setup
    echo "⚠️ Windows build requires manual setup with wine"
else
    echo "⚠️ Skipping Windows build (wine not available)"
fi

# Update package versions
echo "📝 Updating package metadata..."
sed -i 's/Version: 2.0.0/Version: 3.1.0/g' /home/ial/build/ialctl.spec 2>/dev/null || true

# Build DEB package
if command -v fpm >/dev/null 2>&1; then
    echo "📦 Building DEB package..."
    fpm -s dir -t deb -n ialctl -v 3.1.0 \
        --description "Infrastructure as Language - Natural language AWS infrastructure management" \
        --url "https://github.com/Diego-Nardoni/ial-infrastructure" \
        --maintainer "IAL Team" \
        --license "MIT" \
        --depends nodejs \
        --depends awscli \
        dist/linux/ialctl=/usr/local/bin/ialctl
    
    mv ialctl_3.1.0_amd64.deb dist/packages/
    
    echo "📦 Building RPM package..."
    fpm -s dir -t rpm -n ialctl -v 3.1.0 \
        --description "Infrastructure as Language - Natural language AWS infrastructure management" \
        --url "https://github.com/Diego-Nardoni/ial-infrastructure" \
        --maintainer "IAL Team" \
        --license "MIT" \
        --depends nodejs \
        --depends awscli \
        dist/linux/ialctl=/usr/local/bin/ialctl
    
    mv ialctl-3.1.0-1.x86_64.rpm dist/packages/
else
    echo "⚠️ Skipping package build (fpm not available)"
fi

echo "✅ Build complete!"
echo ""
echo "📦 Generated files:"
echo "  dist/linux/ialctl - Linux binary"
echo "  dist/windows/ialctl.exe - Windows binary (manual)"
echo "  dist/packages/*.deb - Debian package"
echo "  dist/packages/*.rpm - RPM package"
echo ""
echo "🎯 Test installation:"
echo "  cd dist/linux && ./install.sh"
echo "  cd dist/windows && powershell -ExecutionPolicy Bypass -File install.ps1"
