# IAL Installers

This directory contains the latest compiled IAL installer with complete dual-logic system and all fixes.

## 🚀 Current Version: v6.9 (All Fixes Applied)

- `ialctl` - **Production-ready installer (v6.9)**
- `ialctl_v6.9_all_fixes` - Source version with all critical fixes

## 🔧 v6.9 Features

### ✅ All Critical Issues Resolved
- **Audit Validator**: Fixed observability_engine and ResourceState imports
- **IAS ValidationResult**: Fixed method calls and object handling  
- **Phases Directory**: Fixed absolute path resolution and YAML loading
- **CF YAML Loader**: Proper CloudFormation template parsing
- **System Stability**: Clean startup without warnings or errors

### ✅ Dual Logic System
- **CORE Resources**: Direct deployment via MCP Infrastructure Manager
- **USER Resources**: Hybrid routing (MCP Router vs Cognitive Engine)

## 🏗️ Usage

### LÓGICA 1: CORE Resources (Foundation)
```bash
./ialctl start  # Direct deployment of 42 foundation components
```

### LÓGICA 2: USER Resources (Natural Language)
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

## 🎯 Commands

```bash
# Deploy IAL foundation (CORE - direct)
./ialctl start

# Configure settings
./ialctl configure

# Interactive mode
./ialctl interactive

# Execute infrastructure commands (USER)
./ialctl "create S3 bucket for data storage"
./ialctl "delete production RDS instance"
```

## 🔧 Architecture

- **CORE Path**: MCP Infrastructure Manager → Direct AWS deployment
- **USER Simple**: Intelligent MCP Router → aws-real-executor  
- **USER Complex**: Cognitive Engine → IAS → Cost → YAML → GitHub PR
- **All Systems**: Clean imports, proper error handling, robust path resolution

## 📊 Version History

Previous versions (v6.2-v6.8) have been archived. v6.9 includes all previous features plus critical stability fixes.
