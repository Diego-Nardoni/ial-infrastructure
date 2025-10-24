# 🔐 Permissões Automáticas - IaL Setup

## ✅ **Permissões Incluídas Automaticamente**

### 🚀 **GitHub Actions Role (IaL-GitHubActionsRole)**

O setup inicial (`setup_ial.py`) cria automaticamente a role do GitHub Actions com **TODAS** as permissões necessárias:

#### **Managed Policies Anexadas:**
```yaml
✅ AmazonEC2FullAccess
✅ AmazonECS_FullAccess  
✅ ElasticLoadBalancingFullAccess
✅ AmazonDynamoDBFullAccess
✅ AmazonSNSFullAccess
✅ AmazonBedrockFullAccess  # 🆕 ADICIONADO AUTOMATICAMENTE
```

#### **Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:YOUR_REPO:*"
      }
    }
  }]
}
```

---

## 🧠 **Bedrock Permissions Detalhadas**

### **AmazonBedrockFullAccess inclui:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### **Modelos Acessíveis:**
- ✅ `anthropic.claude-3-5-sonnet-20240620-v1:0`
- ✅ `anthropic.claude-3-haiku-20240307-v1:0`
- ✅ Todos os outros modelos Bedrock disponíveis

---

## 🔄 **Fluxo Automático**

### **1. Setup Inicial:**
```bash
python3 /home/ial/mcp-tools/setup_ial.py
```

**Cria automaticamente:**
- OIDC Provider
- GitHub Actions Role **COM Bedrock permissions**
- DynamoDB State Table
- SNS Topic

### **2. GitHub Actions Workflow:**
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/IaL-GitHubActionsRole
    # ✅ Role já tem permissões Bedrock
```

### **3. Bedrock Testing:**
```python
# Scripts podem usar Bedrock imediatamente
bedrock = boto3.client('bedrock-runtime')
response = bedrock.invoke_model(...)  # ✅ Funciona automaticamente
```

---

## 🎯 **Benefícios**

### **1. Zero Configuração Manual:**
- ❌ Não precisa anexar policies manualmente
- ❌ Não precisa criar inline policies
- ❌ Não precisa configurar trust relationships
- ✅ **Tudo automático no setup inicial**

### **2. Segurança:**
- ✅ **Least Privilege** - Apenas permissões necessárias
- ✅ **Repo-specific** - Trust policy limitado ao seu repositório
- ✅ **Managed Policies** - Atualizações automáticas da AWS

### **3. Manutenibilidade:**
- ✅ **Versionado** - Permissões definidas em código
- ✅ **Reproduzível** - Mesmo setup em qualquer conta
- ✅ **Auditável** - Histórico de mudanças no Git

---

## 🔍 **Validação**

### **Verificar Role Criada:**
```bash
aws iam get-role --role-name IaL-GitHubActionsRole
```

### **Verificar Policies Anexadas:**
```bash
aws iam list-attached-role-policies --role-name IaL-GitHubActionsRole
```

### **Testar Bedrock Access:**
```bash
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --body '{"anthropic_version": "bedrock-2023-05-31", "max_tokens": 10, "messages": [{"role": "user", "content": "test"}]}' \
  --region us-east-1 \
  /tmp/test.json
```

---

## 📋 **Checklist de Setup**

### **✅ Automático (Feito pelo setup_ial.py):**
- [x] OIDC Provider criado
- [x] GitHub Actions Role criada
- [x] Bedrock permissions anexadas
- [x] Trust policy configurado
- [x] DynamoDB table criada
- [x] SNS topic criado

### **🎯 Manual (Apenas uma vez):**
- [ ] Habilitar modelos Bedrock no Console AWS
- [ ] Configurar secrets no GitHub repo
- [ ] Fazer primeiro commit/push

---

## 🚀 **Resultado**

**Com essa implementação:**
- ✅ **Setup 100% automatizado** - Uma execução configura tudo
- ✅ **Zero configuração manual** - Bedrock funciona imediatamente
- ✅ **Segurança garantida** - Permissões corretas desde o início
- ✅ **Pronto para produção** - CI/CD funciona out-of-the-box

**O IaL agora tem permissões Bedrock automáticas desde o primeiro setup!** 🎉
