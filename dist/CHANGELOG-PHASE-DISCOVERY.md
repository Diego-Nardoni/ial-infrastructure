# IAL Installer - Phase Discovery Update

## Version: phase-discovery-20251117

### 🆕 New Features
- **Phase Discovery Tool**: Descoberta automática de fases via MCP GitHub Server + fallback filesystem
- **Comandos de Fase**: `list phases`, `deployment order`, `show phase XX-nome`
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
- Build Date: Mon Nov 17 01:17:21 PM UTC 2025
- Binary Size: 76M
- Includes: DynamoDB optimizations + Phase Discovery
