# IAL MCP Servers

Servidores MCP integrados do repositório [awslabs/mcp](https://github.com/awslabs/mcp).

## 🔥 Core (Always Active - 9 servidores)

### Infrastructure as Code
- **cfn-mcp-server** - CloudFormation (IaC principal)

### FinOps & Cost Management
- **cost-explorer-mcp-server** - Custos históricos ✅
- **aws-pricing-mcp-server** - Estimativas futuras (Pre-YAML Guardrails)
- **billing-cost-management-mcp-server** - Budgets e alertas

### Security & Compliance
- **iam-mcp-server** - Políticas IAM
- **well-architected-security-mcp-server** - Security Pillar (IAS Sandbox)

### Observability & Audit
- **cloudwatch-mcp-server** - Logs e métricas
- **cloudtrail-mcp-server** - Auditoria (Proof-of-Creation)

### Knowledge
- **aws-documentation-mcp-server** - RAG oficial AWS

## ⚡ Domain (Lazy Load - 7 servidores)

### Compute
- **ecs-mcp-server** - Containers
- **eks-mcp-server** - Kubernetes
- **lambda-tool-mcp-server** - Serverless

### Data & Storage
- **dynamodb-mcp-server** - NoSQL
- **s3-tables-mcp-server** - Object storage
- **elasticache-mcp-server** - Cache (Redis/Memcached)

### DevOps
- **cdk-mcp-server** - AWS CDK
- **aws-support-mcp-server** - Trusted Advisor

## 📋 Total: 16 MCP Servers

**Core (sempre ativo):** 9 servidores
**Domain (lazy load):** 7 servidores

## 🚀 Uso

Configuração em: `/home/ial/config/mcp-mesh-complete.yaml`

```bash
# Testar servidor individual
cd /home/ial/mcp-servers
PYTHONPATH=/home/ial/mcp-servers python3 -m awslabs.cost_explorer_mcp_server.server
```

## 🎯 Arquitetura IAL

```
NL Intent → IAS (well-architected-security)
         → Pre-YAML Cost (aws-pricing)
         → Phase Builder (cfn)
         → GitHub PR
         → CI/CD
         → Proof-of-Creation (cloudtrail)
         → Post-deploy (cloudwatch + iam)
         → Drift Detection
```

## 📦 Dependências

Todos os servidores são Python e requerem:
- boto3
- mcp[cli]
- pydantic
- loguru

Instaladas globalmente em: `/usr/local/lib/python3.12/dist-packages/`
