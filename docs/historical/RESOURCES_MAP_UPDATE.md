# 📊 ATUALIZAÇÃO DO RESOURCES_MAP

## Nova Fase Adicionada

### Phase 05b: IAM Bedrock Policies for GitHub Actions
- **Arquivo**: `05b-iam-bedrock-github.yaml`
- **Recursos**: 1 (IAM Inline Policy)
- **Propósito**: Adicionar permissão Bedrock ao GitHubActionsECRDeployRole
- **Dependências**: Phase 00 (DynamoDB state)
- **Custo**: $0 (IAM policies são gratuitas)
- **Tempo**: 5 minutos

### Recurso Criado
1. **BedrockInvokeModel** (IAM Inline Policy)
   - Tipo: AWS::IAM::RolePolicy
   - Role: GitHubActionsECRDeployRole
   - Permissão: bedrock:InvokeModel
   - Modelo: anthropic.claude-3-sonnet-20240229-v1:0
   - Escopo: Região parametrizada

---

## Total de Recursos Atualizado

**Antes**: 60 recursos em 16 fases  
**Depois**: 61 recursos em 17 fases

### Breakdown por Fase
- Phase 00: 2 recursos (DynamoDB)
- Phase 01: 1 recurso (KMS)
- Phase 02: 6 recursos (Security Services)
- Phase 03: 19 recursos (Networking)
- Phase 04: 3 recursos (Parameter Store)
- Phase 05: 3 recursos (IAM Roles)
- **Phase 05b: 1 recurso (IAM Bedrock Policy)** ← NOVO
- Phase 06: 1 recurso (ECR)
- Phase 07: 2 recursos (ECS Cluster)
- Phase 08: 2 recursos (ECS Task/Service)
- Phase 09: 4 recursos (Auto Scaling)
- Phase 10: 3 recursos (ALB)
- Phase 11: 1 recurso (Redis)
- Phase 12: 2 recursos (WAF/CloudFront)
- Phase 13: 5 recursos (VPC Flow Logs)
- Phase 14: 6 recursos (Observability)
- Phase 15: 0 recursos (Assessment)

**Total**: 61 recursos AWS
