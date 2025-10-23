# ❌ POR QUE NÃO HÁ SCRIPTS SHELL?

## 🎯 PRINCÍPIO IaL (Infrastructure as Language)

**IaL = YAML + AWS CLI APENAS**

Scripts Shell, Python, Terraform, etc. **quebram o princípio IaL**.

---

## ❌ O QUE FOI REMOVIDO

### `parametrize.sh`
**Função**: Substituir valores hardcoded por placeholders  
**Por que remover**: Parametrização já foi feita (uma vez só)  
**Status**: ✅ Não é mais necessário

### `deploy.sh`
**Função**: Executar deploy automatizado  
**Por que remover**: IaL é **manual e intencional**  
**Status**: ❌ Quebra princípio IaL

---

## ✅ COMO USAR SEM SCRIPTS

### Substituir Placeholders (Manual)

```bash
# Carregar parâmetros
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=us-east-1
export PROJECT_NAME=my-project
export EXECUTOR_NAME=YourName

# Substituir em um arquivo específico
sed "s/{{AWS_ACCOUNT_ID}}/$AWS_ACCOUNT_ID/g" phases/00-dynamodb-state.yaml | \
sed "s/{{AWS_REGION}}/$AWS_REGION/g" | \
sed "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" | \
sed "s/{{EXECUTOR_NAME}}/$EXECUTOR_NAME/g" > temp.yaml

# Copiar comandos AWS CLI do temp.yaml e executar manualmente
```

### Executar Fase por Fase (Manual)

```bash
# 1. Abrir YAML
cat phases/00-dynamodb-state.yaml

# 2. Substituir placeholders mentalmente ou com sed
# 3. Copiar comando AWS CLI
# 4. Executar no terminal

aws dynamodb create-table \
  --table-name mcp-provisioning-checklist \
  --attribute-definitions \
    AttributeName=Project,AttributeType=S \
    AttributeName=ResourceName,AttributeType=S \
  --key-schema \
    AttributeName=Project,KeyType=HASH \
    AttributeName=ResourceName,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

---

## 🎯 POR QUE IaL É MANUAL?

### Intencionalidade
- ✅ Você **lê** cada comando antes de executar
- ✅ Você **entende** o que está criando
- ✅ Você **valida** cada recurso criado
- ✅ Você **aprende** AWS CLI na prática

### Segurança
- ✅ Zero automação cega
- ✅ Zero scripts executando sem revisão
- ✅ Zero "magic" acontecendo
- ✅ Controle total sobre cada recurso

### Rastreabilidade
- ✅ Cada comando é executado conscientemente
- ✅ Cada erro é visível imediatamente
- ✅ Cada recurso é verificado manualmente
- ✅ Histórico completo no terminal

---

## 📋 WORKFLOW IaL CORRETO

### 1. Preparar Parâmetros
```bash
# Criar arquivo de parâmetros (uma vez)
cat > my-params.txt << EOF
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
PROJECT_NAME=my-project
EXECUTOR_NAME=YourName
EOF
```

### 2. Abrir YAML da Fase
```bash
# Ler o YAML
cat phases/00-dynamodb-state.yaml
```

### 3. Substituir Placeholders (Mental ou Sed)
```bash
# Opção 1: Mentalmente (recomendado para aprendizado)
# Ler {{AWS_ACCOUNT_ID}} e substituir por 123456789012

# Opção 2: Com sed (mais rápido)
source my-params.txt
sed "s/{{AWS_ACCOUNT_ID}}/$AWS_ACCOUNT_ID/g" phases/00-dynamodb-state.yaml
```

### 4. Copiar e Executar Comando AWS CLI
```bash
# Copiar comando do YAML
# Colar no terminal
# Executar
# Verificar resultado
```

### 5. Validar Recurso Criado
```bash
# Verificar no AWS Console
# Ou via AWS CLI
aws dynamodb describe-table --table-name mcp-provisioning-checklist
```

### 6. Próxima Fase
```bash
# Repetir processo para próxima fase
cat phases/01-kms-security.yaml
```

---

## 🤔 E SE EU QUISER AUTOMAÇÃO?

### Opção 1: Usar CloudFormation (NÃO É IaL)
```bash
# Converter YAMLs para CloudFormation
# Executar stack
aws cloudformation create-stack ...
```

### Opção 2: Usar Terraform (NÃO É IaL)
```bash
# Converter YAMLs para Terraform
# Executar apply
terraform apply
```

### Opção 3: Criar Script Próprio (NÃO É IaL)
```bash
# Criar seu próprio script de automação
# Mas isso quebra o princípio IaL
```

**IaL = Manual e Intencional**

---

## ✅ VANTAGENS DO IaL MANUAL

### Aprendizado
- Você aprende AWS CLI de verdade
- Você entende cada parâmetro
- Você vê cada erro e aprende com ele
- Você não depende de abstrações

### Controle
- Zero surpresas
- Zero "magic"
- Zero automação cega
- Controle total

### Segurança
- Você revisa cada comando
- Você valida cada recurso
- Você sabe exatamente o que existe
- Zero recursos órfãos

### Simplicidade
- Zero dependências (só AWS CLI)
- Zero scripts para manter
- Zero bugs em automação
- Zero complexidade

---

## 🎯 CONCLUSÃO

**IaL não tem scripts porque IaL é sobre:**
- Ler YAML
- Entender comando
- Executar manualmente
- Validar resultado
- Aprender no processo

**Se você quer automação, use CloudFormation ou Terraform.**  
**Se você quer aprender e ter controle total, use IaL.**

**IaL = Infrastructure as Language, não Infrastructure as Script** ✅
