#!/bin/bash
# Build script para instalador IAL com otimizações DynamoDB + Phase Discovery

set -e

echo "🚀 Building IAL Installer with DynamoDB Optimizations + Phase Discovery..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ialctl __pycache__/

# Install/update dependencies (skip pip install due to managed environment)
echo "📦 Checking dependencies..."
python3 -c "import boto3, yaml" 2>/dev/null && echo "✅ Core dependencies available" || echo "⚠️ Some dependencies missing"

# Verify Phase Discovery Tool is included
echo "🔍 Verifying Phase Discovery Tool..."
if [ -f "phase_discovery_tool.py" ]; then
    echo "✅ Phase Discovery Tool found"
else
    echo "❌ Phase Discovery Tool missing!"
    exit 1
fi

# Build with PyInstaller
echo "🔨 Building executable..."
pyinstaller ialctl.spec --clean --noconfirm

# Verify build
if [ -f "dist/ialctl" ]; then
    echo "✅ Build successful!"
    
    # Get file size
    SIZE=$(du -h dist/ialctl | cut -f1)
    echo "📊 Binary size: $SIZE"
    
    # Test basic functionality
    echo "🧪 Testing basic functionality..."
    ./dist/ialctl --help > /dev/null 2>&1 && echo "✅ Help command works" || echo "❌ Help command failed"
    
    # Copy to final location with version tag
    TIMESTAMP=$(date +%Y%m%d)
    echo "📋 Copying to distribution directory..."
    cp dist/ialctl dist/ialctl-phase-discovery-$TIMESTAMP
    
    echo "🎉 IAL Installer with Phase Discovery built successfully!"
    echo "📍 Location: $(pwd)/dist/ialctl"
    echo "📍 Versioned: $(pwd)/dist/ialctl-phase-discovery-$TIMESTAMP"
    
    # Update changelog
    echo "📝 Updating changelog..."
    cat > dist/CHANGELOG-PHASE-DISCOVERY.md << EOF
# IAL Installer - Phase Discovery Update

## Version: phase-discovery-$TIMESTAMP

### 🆕 New Features
- **Phase Discovery Tool**: Descoberta automática de fases via MCP GitHub Server + fallback filesystem
- **Comandos de Fase**: \`list phases\`, \`deployment order\`, \`show phase XX-nome\`
- **Integração MCP**: Usa infraestrutura MCP GitHub Server existente
- **Fallback Robusto**: Funciona mesmo sem MCP ativo

### 🐛 Bug Fixes
- **Fase Discovery**: Corrigido bug que reportava "nenhuma fase disponível" 
- **RAG Integration**: Melhorada descoberta de 92 templates em 10 fases

### 📊 Descobertas
- **10 fases** organizadas de 00-foundation até 99-misc
- **92 templates YAML** totais disponíveis
- **Ordem de deployment** recomendada automaticamente

### 🔧 Technical Details
- Integração transparente com IAL Master Engine
- Cache TTL de 5 minutos para performance
- Suporte a comandos em português e inglês
- Padrão de detecção automática XX-nome

### 📦 Build Info
- Build Date: $(date)
- Binary Size: $SIZE
- Includes: DynamoDB optimizations + Phase Discovery
EOF
    
else
    echo "❌ Build failed!"
    exit 1
fi
