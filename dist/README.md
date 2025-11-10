# IAL Installers

This directory contains compiled IAL installers with complete dual-logic system.

## 🚀 Latest Version: v6.7 (Dual Logic System)

- `ialctl` - **Latest stable version (v6.7)**
- `ialctl_v6.7_dual_logic` - Dual logic system with separated CORE/USER paths

## 📋 Version History

- **v6.7** - Dual logic: CORE (direct) + USER (hybrid routing)
- **v6.4** - Complete individual resource deletion with dependency cleanup
- **v6.3** - Phase deletion functionality
- **v6.2** - Complete pipeline with GitOps integration

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
