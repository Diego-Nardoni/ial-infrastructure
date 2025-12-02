# ANÁLISE - RECURSOS CORE vs NÃO-CORE

## ✅ RECURSOS CORE (NECESSÁRIOS PARA IAL FUNCIONAR)

### DynamoDB Tables
- `ial-feature-flags` - Feature flags system
- `ial-conversation-history` - Conversas do usuário  
- `ial-user-sessions` - Sessões ativas
- `ial-conversation-cache` - Cache de conversas
- `ial-state` - Estado do sistema
- `ial-resource-catalog` - Catálogo de recursos
- `ial-rollback-checkpoints` - Pontos de rollback
- `ial-token-usage` - Uso de tokens
- `ial-knowledge-base` - Base de conhecimento
- `ial-dynamodb-tables` - Metadados das tabelas

### S3 Buckets
- `ial-artifacts-{account}` - Artefatos do sistema
- `ial-memory-{account}` - Memória persistente
- `ial-rag-store-{account}` - Vector store

### IAM Roles
- `ial-lambda-execution-role` - Para Lambdas core
- `ial-bedrock-access-role` - Para Bedrock
- `ial-dynamodb-access-role` - Para DynamoDB

### KMS Keys
- `ial-encryption-key` - Criptografia geral

### Lambda Functions (CORE)
- Memory management functions
- Conversation processing functions
- Basic orchestration functions

## ❌ RECURSOS NÃO-CORE (DEVEM ESTAR EM OUTRAS FASES)

### Network (20-network)
- VPC, Subnets, Route Tables
- NAT Gateways, Internet Gateways
- Security Groups, NACLs

### Compute (30-compute)  
- EC2 Instances
- Auto Scaling Groups
- Load Balancers

### Security (10-security)
- WAF, Shield
- GuardDuty, Security Hub
- Certificate Manager

### Monitoring (40-monitoring)
- CloudWatch Dashboards
- Alarms complexos
- Chaos Engineering

### CI/CD (50-cicd)
- GitOps Pipelines
- CodePipeline, CodeBuild
- Deployment automation

## 🎯 CONSOLIDAÇÃO PROPOSTA

```python
class CoreFoundationDeployer:
    """Deploy APENAS recursos core para IAL funcionar"""
    
    def deploy_core_foundation(self):
        # 1. DynamoDB tables (11 tabelas)
        # 2. S3 buckets (3 buckets)  
        # 3. IAM roles (mínimas necessárias)
        # 4. KMS keys (criptografia)
        # 5. Lambda functions (core apenas)
        # 6. Validação final
```

## ✅ RESULTADO
- IAL funciona 100%
- Recursos mínimos necessários
- Deploy rápido (~5-10 min)
- Sem dependências externas
