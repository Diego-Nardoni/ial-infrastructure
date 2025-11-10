# IAL Installers

This directory contains compiled IAL installers with complete dual-logic system and all fixes.

## 🚀 Latest Version: v6.9 (All Fixes Applied)

- `ialctl` - **Latest stable version (v6.9)**
- `ialctl_v6.9_all_fixes` - All critical fixes + Dual logic system

## 📋 Version History

- **v6.9** - All fixes: Audit Validator, IAS ValidationResult, Phases directory paths
- **v6.8** - CF YAML Loader fixed + Dual logic system
- **v6.7** - Dual logic: CORE (direct) + USER (hybrid routing)
- **v6.4** - Complete individual resource deletion with dependency cleanup
- **v6.3** - Phase deletion functionality
- **v6.2** - Complete pipeline with GitOps integration

## 🔧 v6.9 Critical Fixes

### ✅ All Import Errors Resolved
- **Audit Validator**: Fixed observability_engine and ResourceState imports
- **IAS ValidationResult**: Fixed method calls and object handling
- **Phases Directory**: Fixed absolute path resolution and YAML loading
- **CF YAML Loader**: Proper CloudFormation template parsing

### ✅ System Stability
- No more import warnings or errors
- Clean startup without error messages
- Robust path handling regardless of execution context
- Proper fallbacks for missing dependencies

## 🏗️ Dual Logic System (Maintained)

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
- **All Systems**: Clean imports, proper error handling, robust path resolution
