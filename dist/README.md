# IAL Installers

This directory contains the final production-ready IAL installer with all runtime errors fixed.

## 🚀 Current Version: v6.12 (Production Ready)

- `ialctl` - **Production installer (v6.12)**
- `ialctl_v6.12_final` - Source version with all fixes

## 🔧 v6.12 Final Features

### ✅ All Runtime Errors Fixed
- **Master Engine Import**: Fixed ial_master_engine import error
- **Graph Module Import**: Fixed relative import paths for dependency graph
- **Audit Validator**: Fixed observability_engine and ResourceState imports
- **IAS ValidationResult**: Fixed method calls and object handling  
- **Phases Directory**: Fixed absolute path resolution and YAML loading
- **CF YAML Loader**: Proper CloudFormation template parsing

### ✅ System Stability
- Clean startup with minimal warnings
- All critical components loading successfully
- Graceful fallbacks for optional dependencies
- Production-ready execution

### ✅ Dual Logic System
- **CORE Resources**: Direct deployment via MCP Infrastructure Manager
- **USER Resources**: Hybrid routing (MCP Router vs Cognitive Engine)

## 🏗️ Usage

### Foundation Deployment
```bash
./ialctl start  # Deploy 42 foundation components
```

### Natural Language Interface
```bash
# Simple operations → MCP Router
./ialctl "create s3 bucket with encryption"

# Complex operations → Cognitive Engine
./ialctl "delete production database with safety checks"
```

## 📦 Installation

### Linux
```bash
chmod +x ialctl
./ialctl configure
./ialctl start
```

## 🎯 Commands

```bash
# Foundation deployment
./ialctl start

# Configuration
./ialctl configure

# Interactive mode
./ialctl interactive

# Natural language commands
./ialctl "your infrastructure request"
```

## 🔧 Architecture

- **CORE Path**: MCP Infrastructure Manager → Direct AWS deployment
- **USER Simple**: Intelligent MCP Router → aws-real-executor  
- **USER Complex**: Cognitive Engine → IAS → Cost → YAML → GitHub PR
- **All Systems**: Clean imports, robust error handling, production stability

## 📊 Version History

v6.12 represents the culmination of all previous versions with complete runtime stability:
- All import errors resolved
- All critical components functional
- Production-ready deployment
- Comprehensive error handling
