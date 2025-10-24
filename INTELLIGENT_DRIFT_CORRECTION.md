# 🧠 Intelligent Drift Correction with Bedrock

## 🎯 Overview

O IaL agora implementa **correção automática inteligente de drift** usando Amazon Bedrock para análise contextual e tomada de decisões.

### ✨ **Diferencial Único:**
- **🧠 Inteligência Contextual** - Bedrock analisa cada drift individualmente
- **🤖 Auto-Remediation** - Corrige drifts seguros automaticamente  
- **👨‍💻 Human Escalation** - Escalona casos complexos com contexto completo
- **📚 Aprendizado Contínuo** - Melhora com experiência

---

## 🔄 **Fluxo Inteligente**

```
EventBridge (hourly)
    ↓
Lambda Drift Detector
    ├─ 1. Scan AWS Resources (EC2, RDS, S3...)
    ├─ 2. Compare with DynamoDB desired state  
    ├─ 3. Identify drifts
    ↓
For each drift:
    ├─ 4. Bedrock Intelligence Analysis
    ├─ 5. Generate remediation commands
    ├─ 6. Assess safety for auto-fix
    ↓
Decision:
    ├─ Auto-fixable? → Execute + Log
    ├─ Complex? → Escalate to human + Context
    ↓
7. Summary notification
```

---

## 🧠 **Bedrock Intelligence**

### **Análise Contextual:**
```json
{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "impact_analysis": "Security group allows SSH from 0.0.0.0/0 - CRITICAL security risk",
  "auto_fixable": false,
  "escalation_reason": "CRITICAL security changes require human approval",
  "remediation_commands": [
    "aws ec2 revoke-security-group-ingress --group-id sg-123 --protocol tcp --port 22 --cidr 0.0.0.0/0",
    "aws ec2 authorize-security-group-ingress --group-id sg-123 --protocol tcp --port 22 --cidr 10.0.0.0/8"
  ],
  "rollback_commands": [
    "aws ec2 authorize-security-group-ingress --group-id sg-123 --protocol tcp --port 22 --cidr 0.0.0.0/0"
  ],
  "reasoning": "SSH access should be restricted to private networks only"
}
```

### **Fatores Considerados:**
- ✅ **Severidade** do drift (CRITICAL, HIGH, MEDIUM, LOW)
- ✅ **Horário comercial** (business hours vs maintenance window)
- ✅ **Impacto operacional** (serviços em execução)
- ✅ **Complexidade do rollback**
- ✅ **Histórico** de drifts similares
- ✅ **Políticas de segurança**

---

## 🤖 **Auto-Remediation**

### **Casos Auto-Fixáveis:**
```yaml
✅ Security Group rules (non-critical)
✅ S3 bucket encryption settings  
✅ Instance tags missing
✅ RDS backup settings
✅ CloudWatch log retention
```

### **Casos Escalados:**
```yaml
❌ CRITICAL security changes (SSH 0.0.0.0/0)
❌ Production database modifications
❌ Network changes during business hours
❌ Resource deletions
❌ Cost-impacting changes
```

### **Execução Segura:**
```python
# 1. Validação prévia
validate_commands(solution['remediation_commands'])

# 2. Execução com timeout
subprocess.run(cmd, timeout=60)

# 3. Validação pós-execução  
validate_fix(solution['validation_commands'])

# 4. Rollback automático se falhar
if not success:
    execute_rollback(solution['rollback_commands'])
```

---

## 👨‍💻 **Human Escalation**

### **Notificação Rica:**
```
🚨 DRIFT REQUIRES HUMAN INTERVENTION

Resource: sg-12345678
Type: AWS::EC2::SecurityGroup  
Severity: CRITICAL
Reason: Security rule allows SSH from 0.0.0.0/0

BEDROCK ANALYSIS:
Impact: Exposes SSH access to entire internet - immediate security risk
Reasoning: CRITICAL security changes require human approval and validation

SUGGESTED COMMANDS:
aws ec2 revoke-security-group-ingress --group-id sg-12345678 --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id sg-12345678 --protocol tcp --port 22 --cidr 10.0.0.0/8

ROLLBACK COMMANDS:
aws ec2 authorize-security-group-ingress --group-id sg-12345678 --protocol tcp --port 22 --cidr 0.0.0.0/0
```

---

## 📊 **Monitoramento e Logs**

### **CloudWatch Metrics:**
- `DriftsDetected` - Total drifts encontrados
- `DriftsAutoFixed` - Drifts corrigidos automaticamente
- `DriftsEscalated` - Drifts escalados para humanos
- `AutoFixSuccessRate` - Taxa de sucesso da correção automática

### **DynamoDB Tracking:**
```json
{
  "Project": "ial",
  "ResourceName": "sg-12345678",
  "AutoFixApplied": true,
  "LastAutoFix": "2025-10-23T20:30:00Z",
  "AutoFixSolution": {
    "commands": ["aws ec2 revoke-security-group-ingress..."],
    "reasoning": "Removed overly permissive SSH rule"
  }
}
```

### **SNS Notifications:**
- **📊 Summary** - Resumo de cada execução
- **🚨 Escalations** - Drifts que precisam intervenção humana
- **✅ Success** - Confirmação de correções automáticas

---

## 🔧 **Configuração**

### **Environment Variables:**
```yaml
PROJECT_NAME: "ial"
SNS_TOPIC_ARN: "arn:aws:sns:us-east-1:ACCOUNT:ial-alerts-critical"
```

### **IAM Permissions:**
```yaml
# Bedrock Access
- bedrock:InvokeModel (Claude 3 Sonnet/Haiku)

# AWS Resources Read
- ec2:DescribeSecurityGroups
- rds:DescribeDBInstances  
- s3:GetBucketEncryption

# Auto-Remediation (Limited)
- ec2:AuthorizeSecurityGroupIngress
- ec2:RevokeSecurityGroupIngress
- s3:PutBucketEncryption
- rds:ModifyDBInstance
```

---

## 🚀 **Deployment**

### **1. Update Lambda Code:**
```bash
cd /home/ial/lambda/drift-detector
zip -r function.zip .

aws lambda update-function-code \
  --function-name ial-drift-detector \
  --zip-file fileb://function.zip
```

### **2. Update IAM Permissions:**
```bash
# Deploy Phase 16 with updated permissions
q chat "Deploy phase 16 with new IAM permissions"
```

### **3. Enable Bedrock Models:**
```bash
# Enable Claude 3 Sonnet in AWS Console
# Bedrock > Model access > Enable anthropic.claude-3-sonnet-20240229-v1:0
```

---

## 🎯 **Benefícios vs IaC Tradicional**

| Aspecto | IaL + Bedrock | Terraform | CloudFormation |
|---------|---------------|-----------|----------------|
| **Contextual Analysis** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Auto-Remediation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Human Context** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Learning Capability** | ⭐⭐⭐⭐⭐ | ❌ | ❌ |
| **Natural Language** | ⭐⭐⭐⭐⭐ | ❌ | ❌ |

---

## 📈 **Roadmap**

### **Phase 1 (Atual):**
- ✅ Drift detection
- ✅ Bedrock analysis  
- ✅ Auto-remediation básica
- ✅ Human escalation

### **Phase 2 (Futuro):**
- 🔄 Machine learning from fixes
- 🔄 Predictive drift prevention
- 🔄 Integration with AWS Config Rules
- 🔄 Multi-account drift management

### **Phase 3 (Visão):**
- 🔄 Natural language drift queries
- 🔄 Proactive infrastructure optimization
- 🔄 Cost optimization suggestions
- 🔄 Security posture improvements

---

## ✅ **Status**

**IMPLEMENTADO** ✅

- **Lambda Code:** Atualizado com Bedrock intelligence
- **IAM Permissions:** Configurado para auto-remediation
- **Documentation:** Completa
- **Testing:** Ready for deployment

**Próximo passo:** Deploy e teste em ambiente controlado! 🚀

---

## 🔍 **Testing**

### **Manual Test:**
```bash
# Trigger drift detection manually
aws lambda invoke \
  --function-name ial-drift-detector \
  --payload '{}' \
  response.json

cat response.json
```

### **Create Test Drift:**
```bash
# Create intentional drift for testing
aws ec2 authorize-security-group-ingress \
  --group-id sg-test \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Wait for hourly detection or trigger manually
```

**O IaL agora é verdadeiramente inteligente!** 🧠🚀
