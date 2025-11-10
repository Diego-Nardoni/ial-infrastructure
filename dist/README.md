# IAL Installers

This directory contains compiled IAL installers with complete dual-logic system and CF YAML support.

## 🚀 Latest Version: v6.8 (CF YAML Fixed)

- `ialctl` - **Latest stable version (v6.8)**
- `ialctl_v6.8_cf_fixed` - CF YAML Loader fixed + Dual logic system

## 📋 Version History

- **v6.8** - CF YAML Loader fixed + Dual logic system
- **v6.7** - Dual logic: CORE (direct) + USER (hybrid routing)
- **v6.4** - Complete individual resource deletion with dependency cleanup
- **v6.3** - Phase deletion functionality
- **v6.2** - Complete pipeline with GitOps integration

## 🔧 v6.8 Improvements

### ✅ CF YAML Loader Fixed
- No more "CF YAML Loader not available" warnings
- Proper CloudFormation template parsing
- Support for intrinsic functions (!Ref, !GetAtt, !Join, !Sub, etc.)
- Clean YAML processing without fallbacks

### ✅ Dual Logic System Maintained
- CORE resources: Direct deployment via MCP Infrastructure Manager
- USER resources: Hybrid routing (MCP Router vs Cognitive Engine)

## 🏗️ Dual Logic System

### LÓGICA 1: CORE Resources (ialctl start)
```bash
./ialctl start  # Direct deployment of 42 foundation components
```

### LÓGICA 2: USER Resources (natural language)
```bash
# Simple operations → MCP Router (direct)
./ialctl "create s3 bucket"

# Complex operations → Cognitive Engine (GitOps)
./ialctl "delete production database"
```

## 📦 Installation

### Linux
```bash
chmod +x ialctl
./ialctl start
```

### Windows
See `windows/` directory for Windows installers.

## 🎯 Usage Examples

```bash
# Deploy IAL foundation (CORE - direct)
./ialctl start

# Configure settings
./ialctl configure

# Interactive mode
./ialctl interactive

# Simple resource creation (USER - MCP Router)
./ialctl "create S3 bucket for data storage"

# Complex operations (USER - Cognitive Engine)
./ialctl "delete production RDS instance"
```

## 🔧 Architecture

- **CORE Path**: MCP Infrastructure Manager → Direct AWS deployment
- **USER Simple**: Intelligent MCP Router → aws-real-executor
- **USER Complex**: Cognitive Engine → IAS → Cost → YAML → GitHub PR
- **CF YAML**: Proper CloudFormation template parsing with intrinsic functions
