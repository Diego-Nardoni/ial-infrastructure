# 🚀 IaL - Quick Reference

## 🎯 Setup (One-Time)

```bash
# 1. Instalar Q CLI + MCP
# Siga: docs/setup-guide.md

# 2. Configurar IaL
q chat "Configure IaL para minha conta AWS"
```

---

## 💬 Comandos Naturais

### Setup & Configuração
```bash
# Setup inicial
q chat "Configure IaL para minha conta AWS"

# Verificar status
q chat "Show IaL status"

# Listar recursos
q chat "List all infrastructure resources"
```

### Gerenciar Security Groups
```bash
# Adicionar porta
q chat "Add port 8443 to ALB security group"

# Remover porta
q chat "Remove port 22 from ALB security group"

# Listar regras
q chat "Show ALB security group rules"
```

### Gerenciar ECS
```bash
# Aumentar memória
q chat "Increase ECS task memory to 2GB"

# Escalar tasks
q chat "Scale ECS service to 5 tasks"

# Atualizar imagem
q chat "Update ECS task to use image version 1.2.3"
```

### Drift Detection
```bash
# Verificar drift
q chat "Check infrastructure drift"

# Mostrar drifts
q chat "Show detected drifts"

# Corrigir drift
q chat "Fix infrastructure drift"
```

### Rollback
```bash
# Rollback para commit
q chat "Rollback to commit abc123"

# Rollback para versão anterior
q chat "Rollback to previous version"

# Mostrar histórico
q chat "Show deployment history"
```

---

## 🔧 Comandos Diretos (Fallback)

### Setup Manual
```bash
# Se Q não estiver disponível
python3 /home/ial/mcp-tools/setup_ial.py
```

### Deploy Manual
```bash
# Atualizar YAML
vim phases/03-networking.yaml

# Commit e push
git add phases/03-networking.yaml
git commit -m "Add port 8443"
git push

# GitHub Actions deploys automaticamente
```

### Verificar Recursos
```bash
# DynamoDB
aws dynamodb describe-table --table-name mcp-provisioning-checklist

# Lambda
aws lambda get-function --function-name drift-detector

# EventBridge
aws events describe-rule --name drift-detection-scheduled

# GitHub
gh repo view
```

---

## 📊 Estrutura de Arquivos

```
/home/ial/
├── docs/setup-guide.md        # Setup Q + MCP
├── phases/*.yaml              # Infraestrutura
├── mcp-tools/setup_ial.py     # Setup automatizado
├── scripts/reconcile.py       # Reconciliação
├── lambda/drift-detector/     # Drift detection
└── tests/*.sh                 # Testes
```

---

## 🐛 Troubleshooting

### Q não responde
```bash
# Verificar instalação
q --version

# Verificar MCP config
cat ~/.config/amazon-q/mcp-config.json

# Testar conexão
q chat "Hello"
```

### MCP tools não funcionam
```bash
# Verificar server
python3 /home/ial/mcp-tools/server.py setup_ial '{}'

# Verificar permissões
ls -la /home/ial/mcp-tools/
```

### AWS credenciais
```bash
# Verificar
aws sts get-caller-identity

# Reconfigurar
aws configure
```

### GitHub não configurado
```bash
# Instalar gh CLI
sudo apt install gh

# Autenticar
gh auth login

# Testar
gh api user
```

---

## 📚 Documentação Completa

- [Setup Guide](docs/setup-guide.md) - Instalação completa
- [Architecture](ARCHITECTURE.md) - Design do sistema
- [CI/CD Guide](docs/ci-cd-guide.md) - GitHub Actions
- [Implementation](IMPLEMENTATION_COMPLETE.md) - O que foi feito

---

## 💡 Dicas

### Comandos Mais Usados
```bash
# Top 3
q chat "Configure IaL"                    # Setup inicial
q chat "Add port X to Y security group"   # Modificar SG
q chat "Check infrastructure drift"       # Verificar drift
```

### Boas Práticas
- ✅ Use linguagem natural clara
- ✅ Especifique recursos por nome
- ✅ Verifique drift regularmente
- ✅ Teste mudanças em dev primeiro

### Performance
- Setup: 20 min (one-time)
- Deploy: 2-3 min
- Rollback: 2 min
- Drift check: 1 min

---

**IaL = Infrastructure as Language** 🚀
