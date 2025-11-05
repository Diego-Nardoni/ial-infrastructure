# 📦 ialctl Installation Guide

Infrastructure as Language CLI - Natural language AWS infrastructure management

## 🚀 Quick Install

### Linux (Ubuntu/Debian/RHEL/Amazon Linux)

```bash
# One-line installer
curl -s https://raw.githubusercontent.com/your-org/ial/main/scripts/install.sh | bash

# Or download and run manually
wget https://raw.githubusercontent.com/your-org/ial/main/scripts/install.sh
chmod +x install.sh
./install.sh
```

### Windows (PowerShell)

```powershell
# One-line installer (run as Administrator)
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/your-org/ial/main/scripts/install.ps1'))

# Or with custom install directory
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/your-org/ial/main/scripts/install.ps1')) -InstallDir "C:\Tools\ialctl"
```

## 📋 Manual Installation

### Linux Package Managers

#### Debian/Ubuntu (.deb)
```bash
# Download latest .deb package
wget https://github.com/your-org/ial/releases/latest/download/ialctl_VERSION_amd64.deb

# Install
sudo dpkg -i ialctl_VERSION_amd64.deb
sudo apt-get install -f  # Fix dependencies if needed
```

#### RHEL/CentOS/Fedora (.rpm)
```bash
# Download latest .rpm package
wget https://github.com/your-org/ial/releases/latest/download/ialctl-VERSION-1.x86_64.rpm

# Install with dnf (Fedora)
sudo dnf install ialctl-VERSION-1.x86_64.rpm

# Install with yum (RHEL/CentOS)
sudo yum install ialctl-VERSION-1.x86_64.rpm
```

#### AppImage (Universal Linux)
```bash
# Download AppImage
wget https://github.com/your-org/ial/releases/latest/download/ialctl-VERSION-x86_64.AppImage

# Make executable and run
chmod +x ialctl-VERSION-x86_64.AppImage
./ialctl-VERSION-x86_64.AppImage

# Optional: Install to system
sudo mv ialctl-VERSION-x86_64.AppImage /usr/local/bin/ialctl
```

### Windows Installers

#### MSI Installer
```powershell
# Download and run MSI installer
Invoke-WebRequest -Uri "https://github.com/your-org/ial/releases/latest/download/ialctl-VERSION.msi" -OutFile "ialctl.msi"
Start-Process msiexec.exe -ArgumentList "/i ialctl.msi /quiet" -Wait -Verb RunAs
```

#### Standalone Executable
```powershell
# Download standalone executable
Invoke-WebRequest -Uri "https://github.com/your-org/ial/releases/latest/download/ialctl.exe" -OutFile "ialctl.exe"

# Move to desired location (e.g., C:\Tools)
New-Item -ItemType Directory -Force -Path "C:\Tools"
Move-Item ialctl.exe "C:\Tools\ialctl.exe"

# Add to PATH (optional)
$env:PATH += ";C:\Tools"
```

## 🔐 Verification

### Verify Installation
```bash
# Check version
ialctl --version

# Check help
ialctl --help

# Test interactive mode
ialctl interactive
```

### Verify Signatures (Recommended)

```bash
# Import GPG public key
curl -s https://raw.githubusercontent.com/your-org/ial/main/GPG-KEY | gpg --import

# Download checksums and signature
wget https://github.com/your-org/ial/releases/latest/download/checksums.txt
wget https://github.com/your-org/ial/releases/latest/download/checksums.txt.asc

# Verify signature
gpg --verify checksums.txt.asc checksums.txt

# Verify file integrity
sha256sum -c checksums.txt
```

## ⚙️ Configuration

### AWS Credentials
```bash
# Configure AWS credentials (required)
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1
```

### Bedrock Setup (Optional)
```bash
# Enable Bedrock models in your AWS region
# Visit AWS Console > Bedrock > Model Access
# Request access to Claude models

# Test Bedrock connectivity
ialctl status
```

## 🚀 Getting Started

### Basic Usage
```bash
# Interactive mode (recommended for beginners)
ialctl interactive

# Direct commands
ialctl deploy security
ialctl status
ialctl rollback compute
```

### Example Commands
```bash
# Deploy complete infrastructure
ialctl "Deploy a secure web application with database"

# Check infrastructure status
ialctl "Show me the status of all my resources"

# Cost optimization
ialctl "Analyze my AWS costs and suggest optimizations"

# Rollback changes
ialctl "Rollback the last deployment"
```

## 🔧 Troubleshooting

### Common Issues

#### Command not found
```bash
# Add to PATH manually
export PATH=$PATH:/usr/local/bin

# Or create symlink
sudo ln -s /usr/local/bin/ialctl /usr/bin/ialctl
```

#### Permission denied
```bash
# Make executable
chmod +x /usr/local/bin/ialctl

# Or reinstall with proper permissions
sudo ./install.sh
```

#### AWS credentials not configured
```bash
# Configure AWS CLI
aws configure

# Or use IAM roles (recommended for EC2)
# Attach appropriate IAM role to your EC2 instance
```

#### Bedrock access denied
```bash
# Request model access in AWS Console
# Bedrock > Model Access > Request Access

# Ensure IAM permissions include:
# - bedrock:InvokeModel
# - bedrock:ListFoundationModels
```

### Getting Help

- 📚 Documentation: [https://github.com/your-org/ial/docs](https://github.com/your-org/ial/docs)
- 🐛 Issues: [https://github.com/your-org/ial/issues](https://github.com/your-org/ial/issues)
- 💬 Discussions: [https://github.com/your-org/ial/discussions](https://github.com/your-org/ial/discussions)

## 🔄 Updating

### Automatic Update
```bash
# Re-run installer to get latest version
curl -s https://raw.githubusercontent.com/your-org/ial/main/scripts/install.sh | bash
```

### Manual Update
```bash
# Check current version
ialctl --version

# Download and install latest release manually
# Follow installation instructions above
```

## 🗑️ Uninstallation

### Package Manager
```bash
# Debian/Ubuntu
sudo apt remove ialctl

# RHEL/CentOS/Fedora
sudo dnf remove ialctl  # or yum remove ialctl
```

### Manual Removal
```bash
# Remove binary
sudo rm -f /usr/local/bin/ialctl /usr/bin/ialctl

# Remove bash completion
sudo rm -f /etc/bash_completion.d/ialctl

# Remove configuration (optional)
rm -rf ~/.ial
```

### Windows
```powershell
# If installed via MSI
Start-Process msiexec.exe -ArgumentList "/x ialctl.msi /quiet" -Wait -Verb RunAs

# If installed manually
Remove-Item "C:\Tools\ialctl.exe"
# Remove from PATH manually via System Properties
```
