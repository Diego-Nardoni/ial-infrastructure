#!/bin/bash
set -e

echo "📦 Building .deb and .rpm packages with FPM..."

# Get version
IAL_VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev-$(date +%Y%m%d)")
IAL_VERSION_CLEAN=$(echo "$IAL_VERSION" | sed 's/^v//' | sed 's/-dirty$//' | sed 's/-g[a-f0-9]*$//')

# Ensure binary exists
if [ ! -f "dist/linux/ialctl" ]; then
    echo "❌ Binary not found. Run build_linux.sh first."
    exit 1
fi

# Create package directories
mkdir -p dist/packages

# Build .deb package
echo "🔨 Building .deb package..."
fpm -s dir -t deb \
    --name ialctl \
    --version "$IAL_VERSION_CLEAN" \
    --description "Infrastructure as Language - Natural language AWS infrastructure management" \
    --url "https://github.com/your-org/ial" \
    --maintainer "IAL Team <team@ial.dev>" \
    --license "MIT" \
    --architecture amd64 \
    --depends "python3 >= 3.8" \
    --depends "python3-pip" \
    --package "dist/packages/ialctl_${IAL_VERSION_CLEAN}_amd64.deb" \
    --after-install scripts/post_install.sh \
    --before-remove scripts/pre_remove.sh \
    dist/linux/ialctl=/usr/local/bin/ialctl

# Build .rpm package  
echo "🔨 Building .rpm package..."
fpm -s dir -t rpm \
    --name ialctl \
    --version "$IAL_VERSION_CLEAN" \
    --description "Infrastructure as Language - Natural language AWS infrastructure management" \
    --url "https://github.com/your-org/ial" \
    --maintainer "IAL Team <team@ial.dev>" \
    --license "MIT" \
    --architecture x86_64 \
    --depends "python3 >= 3.8" \
    --depends "python3-pip" \
    --package "dist/packages/ialctl-${IAL_VERSION_CLEAN}-1.x86_64.rpm" \
    --after-install scripts/post_install.sh \
    --before-remove scripts/pre_remove.sh \
    dist/linux/ialctl=/usr/local/bin/ialctl

echo "✅ Package generation completed!"
echo "📁 Packages created:"
ls -la dist/packages/
