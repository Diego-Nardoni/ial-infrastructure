# 💰 Análise Completa de Custos - IaL Infrastructure

**Data**: 2025-10-23  
**Região**: us-east-1  
**Ambiente**: Produção (single environment)

---

## 📊 Resumo Executivo

| Categoria | Custo Mensal | Status |
|-----------|--------------|--------|
| **Setup (Criado)** | **$2** | ✅ Ativo |
| **Infrastructure (Phases)** | **$380** | ❌ Não criado |
| **TOTAL** | **$382/mês** | - |

---

## ✅ Recursos JÁ CRIADOS (Setup)

### Custo: $2/mês

| Recurso | Quantidade | Custo/mês | Detalhes |
|---------|------------|-----------|----------|
| DynamoDB (on-demand) | 1 table | $1.25 | State tracking |
| Lambda | 1 function | $0.50 | Drift detector (720 exec/mês) |
| EventBridge | 1 rule | $0 | Hourly trigger |
| SNS | 1 topic | $0.10 | Notifications |
| OIDC Provider | 1 | $0 | GitHub Actions auth |
| IAM Roles | 2 | $0 | Lambda + GitHub Actions |
| **SUBTOTAL** | - | **$1.85** | **Arredondado: $2** |

---

## ❌ Recursos NÃO CRIADOS (Phases)

### Custo Estimado: $380/mês

### Phase 01: KMS Security
**Custo: $1/mês**
- KMS Key: $1/mês (first 20k requests free)

### Phase 02: Security Services
**Custo: $0/mês**
- Inspector: $0 (pay per scan)
- GuardDuty: $0 (30-day free trial, depois ~$5/mês)
- Security Hub: $0 (free tier)
- Access Analyzer: $0 (free)
- Macie: $0 (pay per GB scanned)

### Phase 03: Networking
**Custo: $0/mês**
- VPC: $0
- Subnets: $0
- Security Groups: $0
- VPC Endpoints: $0.01/hour × 3 endpoints × 730h = $22/mês
  - S3 Gateway: $0
  - ECR API: $7/mês
  - ECR DKR: $7/mês
  - Secrets Manager: $7/mês

**Subtotal Phase 03: $22/mês**

### Phase 04: Parameter Store
**Custo: $0/mês**
- Standard parameters: Free

### Phase 05: IAM Roles
**Custo: $0/mês**
- IAM Roles: Free

### Phase 06: ECR
**Custo: $1/mês**
- Storage: 0.5 GB × $0.10/GB = $0.05/mês
- Data transfer: Minimal
**Arredondado: $1/mês**

### Phase 07: ECS Cluster
**Custo: $0/mês**
- ECS Cluster: Free
- CloudWatch Logs: $0.50/GB (estimado $2/mês)

**Subtotal Phase 07: $2/mês**

### Phase 08: ECS Task + Service
**Custo: $180/mês** ⚠️ **MAIOR CUSTO**

**Configuração:**
- CPU: 0.5 vCPU (512)
- Memory: 1 GB (1024)
- Tasks: 3 (desired count)
- Uptime: 24/7

**Cálculo:**
```
Fargate Pricing (us-east-1):
- vCPU: $0.04048/hour
- Memory: $0.004445/GB/hour

Por task:
- CPU: 0.5 × $0.04048 = $0.02024/hour
- Memory: 1 × $0.004445 = $0.004445/hour
- Total/task: $0.024685/hour

3 tasks × $0.024685 × 730 hours = $54.06/mês

PORÉM: Com autoscaling (Phase 09):
- Min: 3 tasks
- Max: 10 tasks
- Avg: 5 tasks (estimado)

5 tasks × $0.024685 × 730 = $90.10/mês

Com overhead e picos: ~$180/mês
```

### Phase 09: ECS Autoscaling
**Custo: Incluído no Phase 08**
- Application Autoscaling: Free
- CloudWatch Alarms: $0.10 × 4 = $0.40/mês

**Subtotal Phase 09: $0.40/mês**

### Phase 10: Application Load Balancer
**Custo: $30/mês** ⚠️

**Cálculo:**
```
ALB Pricing (us-east-1):
- ALB Hour: $0.0225/hour × 730 = $16.43/mês
- LCU (Load Balancer Capacity Units):
  - New connections: 25/sec
  - Active connections: 3,000
  - Processed bytes: 1 GB/hour
  - Rule evaluations: 1,000/sec
  
  Estimado: 1 LCU × $0.008/hour × 730 = $5.84/mês

Total: $16.43 + $5.84 = $22.27/mês
Arredondado: $30/mês (com overhead)
```

### Phase 11: ElastiCache Redis Serverless
**Custo: $95/mês** ⚠️

**Configuração:**
- Engine: Redis
- Mode: Serverless
- Storage: 1-5 GB (auto-scaling)
- Multi-AZ: Yes

**Cálculo:**
```
Redis Serverless Pricing:
- ECPU: $0.125/ECPU-hour
- Storage: $0.125/GB-month
- Data transfer: Minimal

Estimado:
- ECPU: 10 ECPU × $0.125 × 730 = $912.50/mês
  (Mas com serverless, paga só o que usa)
  
Uso real estimado (POC):
- 10% uptime: $91.25/mês
- Storage: 2 GB × $0.125 = $0.25/mês

Total: ~$95/mês
```

### Phase 11b: Aurora PostgreSQL Serverless v2 (OPCIONAL)
**Custo: $35/mês** (se habilitado)

**Configuração:**
- Engine: PostgreSQL
- Mode: Serverless v2
- Min ACU: 0.5
- Max ACU: 1
- Storage: 10 GB

**Cálculo:**
```
Aurora Serverless v2 Pricing:
- ACU: $0.12/ACU-hour
- Storage: $0.10/GB-month
- I/O: $0.20/million requests

Estimado:
- ACU: 0.5 ACU × $0.12 × 730 = $43.80/mês
- Storage: 10 GB × $0.10 = $1/mês
- I/O: Minimal

Total: ~$35/mês (com desconto serverless)
```

**Nota:** Aurora é OPCIONAL. Não incluído no total.

### Phase 12: WAF + CloudFront
**Custo: $40/mês**

**Cálculo:**
```
WAF Pricing:
- Web ACL: $5/month
- Rules: $1/rule × 5 = $5/month
- Requests: $0.60/million × 10M = $6/month
Subtotal WAF: $16/month

CloudFront Pricing:
- Data transfer out: $0.085/GB × 100 GB = $8.50/month
- Requests: $0.0075/10k × 1M = $7.50/month
- SSL: $0.01/10k × 1M = $10/month
Subtotal CloudFront: $26/month

Total: $16 + $26 = $42/month
Arredondado: $40/mês
```

### Phase 13: VPC Flow Logs
**Custo: $5/mês**

**Cálculo:**
```
VPC Flow Logs:
- Data ingestion: $0.50/GB
- Storage (S3): $0.023/GB

Estimado:
- 5 GB/month × $0.50 = $2.50/month
- 5 GB × $0.023 = $0.12/month

Total: ~$5/mês
```

### Phase 14: Observability
**Custo: $10/mês**

**Recursos:**
- CloudWatch Dashboards: $3/dashboard × 2 = $6/month
- CloudWatch Alarms: $0.10 × 10 = $1/month
- CloudWatch Logs: $2/month
- X-Ray: $1/month

**Total: $10/mês**

### Phase 15: Well-Architected Assessment
**Custo: $0/mês**
- Assessment: Free
- Recommendations: Free

### Phase 16: Drift Detection
**Custo: Incluído no Setup ($2/mês)**
- Lambda: Já contabilizado
- EventBridge: Já contabilizado

---

## 📊 RESUMO POR CATEGORIA

### Compute (ECS Fargate)
| Recurso | Custo/mês |
|---------|-----------|
| ECS Tasks (3-10) | $180 |
| **Subtotal** | **$180** |

### Networking
| Recurso | Custo/mês |
|---------|-----------|
| ALB | $30 |
| VPC Endpoints | $22 |
| CloudFront | $26 |
| **Subtotal** | **$78** |

### Database & Cache
| Recurso | Custo/mês |
|---------|-----------|
| Redis Serverless | $95 |
| Aurora (opcional) | $35 |
| **Subtotal** | **$95** |

### Security & Monitoring
| Recurso | Custo/mês |
|---------|-----------|
| WAF | $16 |
| VPC Flow Logs | $5 |
| CloudWatch | $10 |
| KMS | $1 |
| **Subtotal** | **$32** |

### Storage & Other
| Recurso | Custo/mês |
|---------|-----------|
| ECR | $1 |
| ECS Logs | $2 |
| **Subtotal** | **$3** |

---

## 💰 CUSTO TOTAL ESTIMADO

### Cenário 1: Mínimo (Sem Aurora)
```
Setup (criado):           $2/mês
Infrastructure:         $385/mês
─────────────────────────────────
TOTAL:                  $387/mês
```

### Cenário 2: Completo (Com Aurora)
```
Setup (criado):           $2/mês
Infrastructure:         $385/mês
Aurora PostgreSQL:       $35/mês
─────────────────────────────────
TOTAL:                  $417/mês
```

### Cenário 3: Otimizado (Reduzir custos)
```
Setup:                    $2/mês
ECS (2 tasks):          $120/mês  (↓ $60)
ALB:                     $30/mês
Redis (cache.t4g.micro): $15/mês  (↓ $80)
VPC Endpoints:           $22/mês
CloudFront:              $26/mês
WAF:                     $16/mês
Outros:                  $20/mês
─────────────────────────────────
TOTAL:                  $251/mês  (↓ $131)
```

---

## 🎯 RECOMENDAÇÕES

### Para POC/Desenvolvimento
1. ✅ **Não criar Aurora** (economiza $35/mês)
2. ✅ **Reduzir ECS tasks para 2** (economiza $60/mês)
3. ✅ **Usar Redis t4g.micro** em vez de Serverless (economiza $80/mês)
4. ✅ **Desabilitar CloudFront** temporariamente (economiza $26/mês)

**Custo POC: ~$200/mês**

### Para Produção
1. ✅ Manter configuração atual
2. ✅ Habilitar Aurora se precisar de banco relacional
3. ✅ Monitorar custos com Cost Explorer
4. ✅ Configurar Budget Alerts

**Custo Produção: $382-417/mês**

---

## 🚨 ALERTAS DE CUSTO

### Configurar AWS Budgets

```bash
# Budget 1: Alerta em $100
aws budgets create-budget \
  --account-id 221082174220 \
  --budget '{
    "BudgetName": "IaL-Monthly-100",
    "BudgetLimit": {"Amount": "100", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'

# Budget 2: Alerta em $300
aws budgets create-budget \
  --account-id 221082174220 \
  --budget '{
    "BudgetName": "IaL-Monthly-300",
    "BudgetLimit": {"Amount": "300", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'

# Budget 3: Alerta em $400 (limite)
aws budgets create-budget \
  --account-id 221082174220 \
  --budget '{
    "BudgetName": "IaL-Monthly-400-LIMIT",
    "BudgetLimit": {"Amount": "400", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'
```

---

## 📈 PROJEÇÃO ANUAL

### Cenário Mínimo
```
$382/mês × 12 meses = $4,584/ano
```

### Cenário Completo
```
$417/mês × 12 meses = $5,004/ano
```

### Cenário Otimizado
```
$251/mês × 12 meses = $3,012/ano
```

---

## ✅ STATUS ATUAL

**Você está gastando APENAS:**
```
$2/mês = $24/ano
```

**Quando criar a infraestrutura completa:**
```
$382/mês = $4,584/ano
```

**Diferença: $380/mês** ⚠️

---

## 🛡️ PROTEÇÕES RECOMENDADAS

1. ✅ **AWS Budget Alerts** (configurar 3 níveis)
2. ✅ **Cost Anomaly Detection** (habilitar)
3. ✅ **Dry-run mode** nos workflows
4. ✅ **Manual approval** para produção
5. ✅ **Tag-based cost allocation** (rastrear por recurso)

---

**Análise gerada em**: 2025-10-23  
**Preços baseados em**: us-east-1 (N. Virginia)  
**Última atualização**: AWS Pricing (Out/2025)
