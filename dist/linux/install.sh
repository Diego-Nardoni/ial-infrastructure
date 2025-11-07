#!/bin/bash
# IAL Linux Installer v3.1

set -e

echo "🚀 Installing IAL v3.1..."

# Check if running as root for system-wide install
if [[ $EUID -eq 0 ]]; then
    INSTALL_DIR="/usr/local/bin"
    echo "📁 Installing system-wide to $INSTALL_DIR"
else
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
    echo "📁 Installing to user directory $INSTALL_DIR"
fi

# Check Node.js requirement
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js found: $NODE_VERSION"
else
    echo "⚠️ Node.js not found. Installing via package manager..."
    
    if command -v apt >/dev/null 2>&1; then
        echo "📦 Installing Node.js via apt..."
        sudo apt update && sudo apt install -y nodejs npm
    elif command -v yum >/dev/null 2>&1; then
        echo "📦 Installing Node.js via yum..."
        sudo yum install -y nodejs npm
    elif command -v snap >/dev/null 2>&1; then
        echo "📦 Installing Node.js via snap..."
        sudo snap install node --classic
    else
        echo "❌ Please install Node.js manually from https://nodejs.org/"
        exit 1
    fi
fi

# Check AWS CLI
if command -v aws >/dev/null 2>&1; then
    AWS_VERSION=$(aws --version)
    echo "✅ AWS CLI found: $AWS_VERSION"
else
    echo "⚠️ AWS CLI not found. Please install from https://aws.amazon.com/cli/"
fi

# Install IAL binary
cp ialctl "$INSTALL_DIR/ialctl"
chmod +x "$INSTALL_DIR/ialctl"

# Update PATH if needed
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "📝 Adding $INSTALL_DIR to PATH..."
    if [[ $EUID -ne 0 ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo "🔄 Please run: source ~/.bashrc"
    fi
fi

echo ""
echo "✅ IAL v3.1 installed successfully!"
echo ""
echo "🎯 Quick Start:"
echo "  ialctl start        - Deploy IAL infrastructure"
echo "  ialctl configure    - Configure settings"
echo "  ialctl interactive  - Interactive mode"
echo ""
echo "📚 Documentation: https://github.com/Diego-Nardoni/ial-infrastructure"
