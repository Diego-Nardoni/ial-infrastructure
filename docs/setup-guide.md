# 🚀 IaL Setup Guide - 100% Automatizado

**Setup completo do IaL usando Amazon Q Developer com MCP no Ubuntu**

Tempo total: **20 minutos** (one-time setup)

---

## 📋 Pré-requisitos

### Sistema
- Ubuntu 20.04+ (ou similar Linux)
- Python 3.11+
- Git instalado

### Contas
- AWS Account com credenciais configuradas
- GitHub Account (opcional, para CI/CD)

---

## 🔧 Passo 1: Instalar Ferramentas (15 min)

### 1.1 Amazon Q CLI (5 min)

```bash
# Download
curl -o q-installer.sh https://desktop-release.codewhisperer.us-east-1.amazonaws.com/latest/Amazon-Q-CLI-Installer.sh

# Instalar
chmod +x q-installer.sh
./q-installer.sh

# Verificar
q --version
```

### 1.2 AWS CLI (2 min)

```bash
# Configurar credenciais
aws configure
# AWS Access Key ID: [sua key]
# AWS Secret Access Key: [seu secret]
# Default region: us-east-1
# Default output: json

# Verificar
aws sts get-caller-identity
```

### 1.3 GitHub CLI (3 min) - OPCIONAL

```bash
# Instalar (Ubuntu)
sudo apt install gh

# Autenticar
gh auth login

# Verificar
gh api user
```

### 1.4 ccapi-mcp-server (5 min)

```bash
# Instalar (escolha um método)
npm install -g @aws/ccapi-mcp-server
# OU
pip install ccapi-mcp-server

# Criar config MCP
mkdir -p ~/.config/amazon-q

# Criar configuração
cat > ~/.config/amazon-q/mcp-config.json << 'EOF'
{
  "mcpServers": {
    "ccapi": {
      "command": "ccapi-mcp-server",
      "args": [],
      "env": {
        "AWS_REGION": "us-east-1"
      }
    },
    "ial-tools": {
      "command": "python3",
      "args": ["/home/ial/mcp-tools/server.py"],
      "env": {}
    }
  }
}
EOF

# Testar
q chat "Hello"
```

---

## 📦 Passo 2: Clonar Projeto (2 min)

```bash
# Clonar
git clone https://github.com/YOUR_ORG/ial-infrastructure.git /home/ial

# Entrar
cd /home/ial

# Verificar
ls -la
```

---

## 🎯 Passo 3: Configurar IaL - 100% AUTOMATIZADO (3 min)

### Um Único Comando:

```bash
q chat "Configure IaL para minha conta AWS"
```

### O Que Acontece Automaticamente:

#### ✅ Detecção Automática
- AWS Account ID
- AWS Region
- GitHub User (se configurado)

#### ✅ Criação Automática de Recursos

**1. IAM Role** (`IaL-LambdaExecutionRole`)
- Trust policy para Lambda
- Managed policies:
  - AWSLambdaBasicExecutionRole
  - AmazonDynamoDBFullAccess
  - AmazonSNSFullAccess
- Inline policy para Bedrock

**2. DynamoDB Table** (`mcp-provisioning-checklist`)
- Key schema: Project (HASH) + ResourceName (RANGE)
- Billing: PAY_PER_REQUEST
- TTL habilitado (AttributeName: TTL)

**3. SNS Topic** (`ial-alerts-critical`)
- Para notificações de drift e deploy

**4. Lambda Function** (`drift-detector`)
- Runtime: Python 3.11
- Handler: index.lambda_handler
- Timeout: 300s
- Memory: 512MB
- Role: IaL-LambdaExecutionRole

**5. EventBridge Rule** (`drift-detection-scheduled`)
- Schedule: rate(1 hour)
- Target: Lambda drift-detector
- Permissões configuradas

---

## 📧 Passo 4: Configurar Email (2 min)

Após o setup, você receberá o comando para subscrever email:

```bash
# Copie o comando exibido, exemplo:
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:ial-alerts-critical \
  --protocol email \
  --notification-endpoint seu-email@example.com

# Confirme o email (check inbox)
```

---

## ✅ Passo 5: Validação (1 min)

```bash
# Verificar recursos criados
aws iam get-role --role-name IaL-LambdaExecutionRole
aws dynamodb describe-table --table-name mcp-provisioning-checklist
aws lambda get-function --function-name drift-detector
aws events describe-rule --name drift-detection-scheduled
aws sns list-topics | grep ial-alerts-critical
```

---

## 🎉 Pronto para Usar!

Agora você pode gerenciar infraestrutura via linguagem natural:

```bash
# Adicionar porta ao security group
q chat "Add port 8443 to ALB security group"

# Verificar drift
q chat "Check infrastructure drift"

# Fazer rollback
q chat "Rollback to previous version"
```

---

## 📊 Recursos Criados Automaticamente

| Recurso | Nome | Descrição |
|---------|------|-----------|
| IAM Role | IaL-LambdaExecutionRole | Permissões para Lambda |
| DynamoDB | mcp-provisioning-checklist | State management |
| SNS Topic | ial-alerts-critical | Notificações |
| Lambda | drift-detector | Drift detection |
| EventBridge | drift-detection-scheduled | Trigger horário |

---

## 🐛 Troubleshooting

### Setup falhou

```bash
# Ver logs detalhados
python3 /home/ial/mcp-tools/setup_ial.py

# Verificar permissões AWS
aws iam get-user
```

### Q não responde

```bash
# Verificar instalação
q --version

# Verificar MCP config
cat ~/.config/amazon-q/mcp-config.json

# Testar
q chat "Hello"
```

### AWS credenciais

```bash
# Verificar
aws sts get-caller-identity

# Reconfigurar
aws configure
```

---

## 💡 Notas Importantes

### Permissões AWS Necessárias

O usuário AWS precisa de permissões para:
- IAM (criar roles e policies)
- DynamoDB (criar tables)
- Lambda (criar functions)
- EventBridge (criar rules)
- SNS (criar topics)

### Custos

Setup não tem custo adicional. Custos operacionais:
- DynamoDB: ~$1.25/mês
- Lambda: ~$0.50/mês
- SNS: ~$0.10/mês
- **Total**: ~$2/mês

### Bedrock Access

Habilite Bedrock model access no console AWS (one-time):
1. AWS Console → Bedrock
2. Model access → Manage
3. Enable: Claude 3 Haiku

---

## 📚 Próximos Passos

1. ✅ Subscrever email no SNS
2. ✅ Confirmar email
3. ✅ Habilitar Bedrock access
4. ✅ Testar: `q chat "Add port 8443 to ALB"`
5. ✅ Ler [Quick Reference](../QUICK_REFERENCE.md)

---

**Setup 100% automatizado! Zero configuração manual de recursos AWS.** 🚀
