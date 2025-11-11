#!/bin/bash
# IAL Infrastructure CLI - Installation Script v6.29.3 Direct Bedrock
# Supports: Ubuntu, Debian, Amazon Linux, CentOS, RHEL, Fedora

set -e

VERSION="6.29.3-direct-bedrock"
GITHUB_REPO="Diego-Nardoni/ial-infrastructure"
BINARY_NAME="ialctl"

echo "🚀 IAL Infrastructure CLI v${VERSION} - Installation"
echo "=================================================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo "❌ Cannot detect OS. Unsupported system."
    exit 1
fi

echo "🔍 Detected OS: $OS $VER"

# Function to install via .deb package
install_deb() {
    echo "📦 Installing via .deb package..."
    
    # Download .deb package
    DEB_URL="https://github.com/${GITHUB_REPO}/raw/main/dist/packages/ialctl_6.29.3_direct_bedrock_amd64.deb"
    
    echo "⬇️ Downloading: $DEB_URL"
    wget -q "$DEB_URL" -O "/tmp/ialctl.deb"
    
    # Install package
    echo "📦 Installing package..."
    sudo dpkg -i "/tmp/ialctl.deb" || {
        echo "🔧 Fixing dependencies..."
        sudo apt-get update
        sudo apt-get install -f -y
    }
    
    # Cleanup
    rm -f "/tmp/ialctl.deb"
    
    echo "✅ Installation completed via .deb package"
}

# Function to install via .rpm package
install_rpm() {
    echo "📦 Installing via .rpm package..."
    
    # Download .rpm package
    RPM_URL="https://github.com/${GITHUB_REPO}/raw/main/dist/packages/ialctl-6.29.3_direct-1.x86_64.rpm"
    
    echo "⬇️ Downloading: $RPM_URL"
    wget -q "$RPM_URL" -O "/tmp/ialctl.rpm"
    
    # Install package
    echo "📦 Installing package..."
    if command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y "/tmp/ialctl.rpm"
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y "/tmp/ialctl.rpm"
    else
        sudo rpm -i "/tmp/ialctl.rpm"
    fi
    
    # Cleanup
    rm -f "/tmp/ialctl.rpm"
    
    echo "✅ Installation completed via .rpm package"
}

# Function to install via binary
install_binary() {
    echo "📦 Installing via binary..."
    
    # Download binary
    BINARY_URL="https://github.com/${GITHUB_REPO}/raw/main/dist/ialctl"
    
    echo "⬇️ Downloading: $BINARY_URL"
    sudo wget -q "$BINARY_URL" -O "/usr/local/bin/ialctl"
    sudo chmod +x "/usr/local/bin/ialctl"
    
    echo "✅ Installation completed via binary"
}

# Install based on OS
case $OS in
    ubuntu|debian)
        echo "🐧 Ubuntu/Debian detected - using .deb package"
        install_deb
        ;;
    amzn|centos|rhel|fedora)
        echo "🎩 Red Hat family detected - using .rpm package"
        install_rpm
        ;;
    *)
        echo "⚠️ Unknown OS, trying binary installation"
        install_binary
        ;;
esac

# Verify installation
echo ""
echo "🧪 Verifying installation..."
if command -v ialctl >/dev/null 2>&1; then
    echo "✅ ialctl installed successfully!"
    echo ""
    echo "📋 Quick Start:"
    echo "  ialctl --help                    # Show help"
    echo "  ialctl start                     # Deploy IAL foundation"
    echo "  ialctl \"oi tudo bem?\"            # Natural conversation (Bedrock)"
    echo "  ialctl \"que dia é hoje?\"         # Date/time with context"
    echo "  ialctl \"create ECS cluster\"      # Infrastructure deployment"
    echo ""
    echo "🎉 IAL v${VERSION} ready to use!"
    echo "🗣️ Now with direct Bedrock conversation like Amazon Q!"
else
    echo "❌ Installation failed. Please check the logs above."
    exit 1
fi
