# 🍴 Guia para Fork do IaL

**Como usar o IaL no seu próprio fork**

---

## 🎯 Visão Geral

Este guia é para você que quer:
- ✅ Fazer fork do projeto IaL
- ✅ Usar na sua própria conta AWS
- ✅ Ter GitHub Actions funcionando automaticamente

---

## 📋 Passo-a-Passo

### 1. Fork no GitHub (1 min)

```bash
# Via CLI
gh repo fork Diego-Nardoni/ial-infrastructure

# OU via Web
# https://github.com/Diego-Nardoni/ial-infrastructure
# Clique em "Fork"
```

---

### 2. Clonar Seu Fork (1 min)

```bash
# Substitua SEU-USUARIO pelo seu username
git clone https://github.com/SEU-USUARIO/ial-infrastructure.git /home/ial
cd /home/ial
```

---

### 3. Instalar Ferramentas (15 min, one-time)

#### 3.1 Amazon Q CLI
```bash
curl -o q-installer.sh https://desktop-release.codewhisperer.us-east-1.amazonaws.com/latest/Amazon-Q-CLI-Installer.sh
chmod +x q-installer.sh
./q-installer.sh
```

#### 3.2 AWS CLI
```bash
aws configure
# Suas credenciais AWS
```

#### 3.3 GitHub CLI
```bash
sudo apt install gh
gh auth login
```

#### 3.4 MCP Server
```bash
mkdir -p ~/.config/amazon-q
cp /home/ial/mcp-server-config.json ~/.config/amazon-q/
```

---

### 4. Setup IaL (3 min) - AUTOMÁTICO!

```bash
q chat "Configure IaL para minha conta AWS"
```

**O que acontece:**

```
🚀 Iniciando setup do IaL...

✅ AWS Account: 999999999999  (sua conta)
✅ AWS Region: us-east-1
✅ GitHub User: SEU-USUARIO
✅ Repositório detectado: SEU-USUARIO/ial-infrastructure

📦 Criando OIDC Provider...
📦 Criando IAM role IaL-GitHubActionsRole...
   Trust policy: repo:SEU-USUARIO/ial-infrastructure:*
📦 Criando IAM role IaL-LambdaExecutionRole...
📦 Criando DynamoDB table...
📦 Criando SNS topic...
📦 Criando Lambda function...
📦 Criando EventBridge rule...

✅ Setup completo!

🚀 GitHub Actions configurado para: SEU-USUARIO/ial-infrastructure
   ✅ Workflows funcionarão automaticamente!
```

---

### 5. Configurar GitHub Variable (1 min)

```bash
# Configurar AWS_ROLE_ARN
gh variable set AWS_ROLE_ARN \
  --body "arn:aws:iam::999999999999:role/IaL-GitHubActionsRole"
  
# Verificar
gh variable list
```

---

### 6. Testar (2 min)

```bash
# Fazer uma mudança
echo "# My fork" >> README.md
git add README.md
git commit -m "Test: My fork setup"
git push

# Verificar Actions
gh run list
```

---

## ✅ Resultado

Agora você tem:
- ✅ Fork do IaL na sua conta GitHub
- ✅ Recursos AWS na sua conta
- ✅ GitHub Actions funcionando no SEU fork
- ✅ Trust policy específico para SEU repositório

---

## 🔄 Diferenças do Original

| Item | Original | Seu Fork |
|------|----------|----------|
| Repositório | Diego-Nardoni/ial-infrastructure | SEU-USUARIO/ial-infrastructure |
| AWS Account | 221082174220 | 999999999999 (sua) |
| IAM Role | ...221082174220:role/... | ...999999999999:role/... |
| Trust Policy | repo:Diego-Nardoni/... | repo:SEU-USUARIO/... |
| GitHub Variable | Configurado no original | Você configura no fork |

---

## 🎯 Por Que Funciona?

### Detecção Automática

O script `setup_ial.py` detecta automaticamente:

```python
# 1. Detecta seu usuário GitHub
github_user = gh api user
# → SEU-USUARIO

# 2. Detecta seu repositório
git remote get-url origin
# → https://github.com/SEU-USUARIO/ial-infrastructure.git
# → Extrai: SEU-USUARIO/ial-infrastructure

# 3. Cria trust policy específico
trust_policy = {
    "Condition": {
        "StringLike": {
            "token.actions.githubusercontent.com:sub": 
                "repo:SEU-USUARIO/ial-infrastructure:*"
        }
    }
}
```

### Isolamento Completo

- ✅ Sua conta AWS (separada)
- ✅ Seus recursos AWS (separados)
- ✅ Seu repositório GitHub (fork)
- ✅ Suas GitHub Variables (separadas)
- ✅ Seus workflows (executam no seu fork)

**Zero conflito com o repositório original!**

---

## 🐛 Troubleshooting

### Workflow Falha com "Unable to locate credentials"

**Causa:** Trust policy não está configurado para seu fork.

**Solução:**
```bash
# Execute setup novamente
q chat "Configure IaL para minha conta AWS"
# → Vai detectar o repo e atualizar trust policy
```

### "Repository not found"

**Causa:** Git remote não configurado.

**Solução:**
```bash
cd /home/ial
git remote -v
# Se vazio:
git remote add origin https://github.com/SEU-USUARIO/ial-infrastructure.git
```

### GitHub Variable não encontrada

**Causa:** Variable não configurada no fork.

**Solução:**
```bash
gh variable set AWS_ROLE_ARN \
  --body "arn:aws:iam::SUA-CONTA:role/IaL-GitHubActionsRole"
```

---

## 💡 Dicas

### Manter Fork Atualizado

```bash
# Adicionar upstream
git remote add upstream https://github.com/Diego-Nardoni/ial-infrastructure.git

# Atualizar
git fetch upstream
git merge upstream/main
git push
```

### Contribuir de Volta

```bash
# Fazer mudanças
git checkout -b feature/minha-feature
git commit -m "Add: nova feature"
git push origin feature/minha-feature

# Criar Pull Request
gh pr create --base Diego-Nardoni:main
```

---

## 🎉 Pronto!

Seu fork está configurado e funcionando!

**Próximos passos:**
- ✅ Explorar comandos naturais: `q chat "Add port 8443 to ALB"`
- ✅ Verificar drift: `q chat "Check infrastructure drift"`
- ✅ Customizar para suas necessidades

---

**IaL = Infrastructure as Language** 🚀

*Funciona perfeitamente em forks!*
