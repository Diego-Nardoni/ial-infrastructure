#!/bin/bash
set -e

# ialctl installer for Linux
# Usage: curl -s https://raw.githubusercontent.com/your-org/ial/main/scripts/install.sh | bash

REPO_URL="https://github.com/your-org/ial"
API_URL="https://api.github.com/repos/your-org/ial/releases/latest"
INSTALL_DIR="/usr/local/bin"
BINARY_NAME="ialctl"

echo "🚀 Installing ialctl..."

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case $ARCH in
    x86_64) ARCH="amd64" ;;
    aarch64) ARCH="arm64" ;;
    armv7l) ARCH="armv7" ;;
    *) echo "❌ Unsupported architecture: $ARCH"; exit 1 ;;
esac

echo "📋 Detected: $OS-$ARCH"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
        echo "🔐 Using sudo for installation"
    else
        echo "❌ This script requires root privileges. Please run with sudo or as root."
        exit 1
    fi
else
    SUDO=""
fi

# Get latest release info
echo "📡 Fetching latest release info..."
if command -v curl >/dev/null 2>&1; then
    RELEASE_INFO=$(curl -s "$API_URL")
elif command -v wget >/dev/null 2>&1; then
    RELEASE_INFO=$(wget -qO- "$API_URL")
else
    echo "❌ Neither curl nor wget found. Please install one of them."
    exit 1
fi

# Extract version and download URL
VERSION=$(echo "$RELEASE_INFO" | grep '"tag_name"' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
if [ -z "$VERSION" ]; then
    echo "❌ Could not determine latest version"
    exit 1
fi

echo "📦 Latest version: $VERSION"

# Determine download strategy based on package manager
if command -v apt-get >/dev/null 2>&1; then
    # Debian/Ubuntu - prefer .deb
    PACKAGE_TYPE="deb"
    DOWNLOAD_URL=$(echo "$RELEASE_INFO" | grep '"browser_download_url"' | grep "\.deb" | head -1 | sed -E 's/.*"browser_download_url": "([^"]+)".*/\1/')
    PACKAGE_FILE="ialctl_${VERSION#v}_amd64.deb"
elif command -v yum >/dev/null 2>&1 || command -v dnf >/dev/null 2>&1; then
    # RHEL/CentOS/Fedora - prefer .rpm
    PACKAGE_TYPE="rpm"
    DOWNLOAD_URL=$(echo "$RELEASE_INFO" | grep '"browser_download_url"' | grep "\.rpm" | head -1 | sed -E 's/.*"browser_download_url": "([^"]+)".*/\1/')
    PACKAGE_FILE="ialctl-${VERSION#v}-1.x86_64.rpm"
else
    # Generic Linux - use binary
    PACKAGE_TYPE="binary"
    DOWNLOAD_URL=$(echo "$RELEASE_INFO" | grep '"browser_download_url"' | grep -E "(ialctl-.*-linux|ialctl$)" | head -1 | sed -E 's/.*"browser_download_url": "([^"]+)".*/\1/')
    PACKAGE_FILE="ialctl"
fi

if [ -z "$DOWNLOAD_URL" ]; then
    echo "❌ Could not find download URL for $PACKAGE_TYPE"
    exit 1
fi

echo "📥 Downloading $PACKAGE_TYPE package..."
echo "🔗 URL: $DOWNLOAD_URL"

# Create temporary directory
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

# Download package
if command -v curl >/dev/null 2>&1; then
    curl -L -o "$PACKAGE_FILE" "$DOWNLOAD_URL"
elif command -v wget >/dev/null 2>&1; then
    wget -O "$PACKAGE_FILE" "$DOWNLOAD_URL"
fi

# Install based on package type
case $PACKAGE_TYPE in
    "deb")
        echo "📦 Installing .deb package..."
        $SUDO dpkg -i "$PACKAGE_FILE" || {
            echo "🔧 Fixing dependencies..."
            $SUDO apt-get update
            $SUDO apt-get install -f -y
        }
        ;;
    "rpm")
        if command -v dnf >/dev/null 2>&1; then
            echo "📦 Installing .rpm package with dnf..."
            $SUDO dnf install -y "$PACKAGE_FILE"
        elif command -v yum >/dev/null 2>&1; then
            echo "📦 Installing .rpm package with yum..."
            $SUDO yum install -y "$PACKAGE_FILE"
        else
            echo "📦 Installing .rpm package with rpm..."
            $SUDO rpm -i "$PACKAGE_FILE"
        fi
        ;;
    "binary")
        echo "📦 Installing binary..."
        chmod +x "$PACKAGE_FILE"
        $SUDO mv "$PACKAGE_FILE" "$INSTALL_DIR/$BINARY_NAME"
        ;;
esac

# Cleanup
cd /
rm -rf "$TMP_DIR"

# Verify installation
echo "🧪 Verifying installation..."
if command -v ialctl >/dev/null 2>&1; then
    echo "✅ ialctl installed successfully!"
    echo "📋 Version: $(ialctl --version 2>/dev/null || echo 'installed')"
    echo ""
    echo "🚀 Get started:"
    echo "   ialctl --help"
    echo "   ialctl interactive"
else
    echo "❌ Installation verification failed"
    echo "💡 Try running: export PATH=\$PATH:$INSTALL_DIR"
    exit 1
fi
