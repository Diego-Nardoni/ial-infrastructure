# IAL v3.15.0-CONVERSATIONAL - Sistema de Diálogo Inteligente

## 🎯 INSTALAÇÃO RÁPIDA

```bash
# Instalar pacote
sudo dpkg -i packages/ialctl-3.15.0-CONVERSATIONAL-20251202.deb

# Ou usar binário diretamente
chmod +x bin/ialctl
sudo cp bin/ialctl /usr/local/bin/
```

## 🚀 USO

```bash
# Interface conversacional
ialctl

# Deploy foundation
ialctl start

# Modo CI/CD
ialctl ci validate
```

## 🎯 NOVA FUNCIONALIDADE

### Sistema Conversacional Inteligente
- Detecta requisitos ambíguos automaticamente
- Faz perguntas contextuais por tipo de serviço
- Transforma diálogo em especificações técnicas precisas

### Exemplo Real
```
Input: "crie uma ecs"
Output: Perguntas sobre aplicação, rede, scaling
Resultado: Templates ECS refinados e específicos
```

## 📋 REQUISITOS

- AWS CLI configurado
- Credenciais AWS válidas
- Bedrock habilitado (para LLM)
- Python 3.8+ (para desenvolvimento)

## 🔧 ARQUITETURA

- **LLM Primary**: Análise inteligente via Bedrock
- **MCP Fallback**: Detecção técnica de gaps
- **Emergency Fallback**: Nunca falha, sempre prossegue
- **17 MCP Servers**: Cobertura completa de serviços AWS

Versão enterprise-grade com diálogo conversacional real.
