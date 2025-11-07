# IAL v3.1 - Distribution Files

## 📦 Available Packages

### Windows
- **ialctl.exe** - Windows executable
- **install.ps1** - PowerShell installer script
- **VERSION** - Version information

### Linux
- **ialctl** - Linux executable  
- **install.sh** - Bash installer script
- **VERSION** - Version information

### Packages
- **ialctl_3.1.0_amd64.deb** - Debian/Ubuntu package
- **ialctl-3.1.0-1.x86_64.rpm** - RedHat/CentOS package

## 🚀 Installation

### Windows (PowerShell as Administrator)
```powershell
cd dist/windows
.\install.ps1
```

### Linux (Bash)
```bash
cd dist/linux
./install.sh
```

### Package Managers
```bash
# Debian/Ubuntu
sudo dpkg -i dist/packages/ialctl_3.1.0_amd64.deb

# RedHat/CentOS
sudo rpm -i dist/packages/ialctl-3.1.0-1.x86_64.rpm
```

## 📋 Requirements

### System Requirements
- **Node.js** v16+ (for CDK support)
- **AWS CLI** v2+ (configured with credentials)
- **Python** 3.11+ (included in binary)

### AWS Requirements
- Valid AWS account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Sufficient IAM permissions for CloudFormation

## 🎯 Quick Start

After installation:

```bash
# Deploy IAL infrastructure
ialctl start

# Configure settings
ialctl configure

# Interactive mode
ialctl interactive

# Get help
ialctl
```

## 🔧 New in v3.1

- **`ialctl start`** - One-command infrastructure deployment via CDK
- **CDK Integration** - Bootstrap foundation infrastructure atomically
- **Enhanced Validation** - Intent validation and cost guardrails
- **Intelligent MCP Router** - Automatic service detection and routing
- **Node.js Support** - Full CDK CLI integration

## 📚 Documentation

- **GitHub**: https://github.com/Diego-Nardoni/ial-infrastructure
- **Architecture**: See ARCHITECTURE.md
- **Contributing**: See CONTRIBUTING.md

## 🆘 Support

If you encounter issues:

1. Check Node.js is installed: `node --version`
2. Check AWS CLI is configured: `aws sts get-caller-identity`
3. Check IAL version: `ialctl --version`
4. Open issue on GitHub with error details

---

*IAL v3.1 - Infrastructure as Language - November 2025*
