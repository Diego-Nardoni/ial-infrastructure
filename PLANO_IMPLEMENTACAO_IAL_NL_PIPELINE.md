# 📋 Plano de Implementação - IAL NL Intent Pipeline

**Data:** 2025-11-13  
**Status Geral:** 85% Completo  
**Versão:** 6.30.8-75

---

## ✅ COMPLETADO (85%)

### 1. GitOps Deployment Pipeline (Step Functions) ✅

**Localização:** `/home/ial/phases/00-foundation/17-nl-intent-pipeline.yaml`

**Recursos Criados na AWS:**
- Stack Name: `ial-nl-intent-pipeline`
- Region: `us-east-1`
- Account: `221082174220`
- State Machine ARN: `arn:aws:states:us-east-1:221082174220:stateMachine:ial-nl-intent-pipeline`

**9 Lambda Functions Deployadas:**
1. ✅ `ial-nl-ias-validation` - IAS security validation
2. ✅ `ial-nl-cost-estimation` - Pre-YAML cost guardrails
3. ✅ `ial-nl-phase-builder` - CloudFormation YAML generation
4. ✅ `ial-nl-git-commit-pr` - Git commit and PR creation
5. ✅ `ial-nl-wait-pr-approval` - Callback pattern for approval
6. ✅ `ial-nl-deploy-cfn` - CloudFormation deployment
7. ✅ `ial-nl-proof-of-creation` - Audit trail
8. ✅ `ial-nl-post-deploy-analysis` - WA + FinOps + Compliance
9. ✅ `ial-nl-drift-detection` - Drift detection

**Lambda Layer:**
- ✅ `ial-pipeline-dependencies` (IAS, Cost Guardrails, Phase Builder)

**S3 Artifacts:**
- Bucket: `s3://ial-artifacts-221082174220`
- Lambdas: `s3://ial-artifacts-221082174220/lambdas/*.zip`
- Layer: `s3://ial-artifacts-221082174220/lambda-layer/ial-pipeline-layer.zip`

**IAM Roles:**
- ✅ `IAL-Pipeline-Lambda-Role` - Para Lambdas
- ✅ `IAL-NL-Intent-Pipeline-Role` - Para Step Functions

---

### 2. IAS (Intent Validation Sandbox) ✅

**Localização:** `/home/ial/core/ias_sandbox.py`

**Funcionalidades:**
- ✅ Detecta riscos de segurança em linguagem natural
- ✅ Patterns: public_access, no_encryption, admin_access, no_backup
- ✅ Severity scoring (CRITICAL=40, HIGH=25, MEDIUM=15, LOW=5)
- ✅ Block automático se score >= 40

**Teste Realizado:**
```bash
aws lambda invoke \
  --function-name ial-nl-ias-validation \
  --payload '{"nl_intent":"public S3 bucket"}' \
  /tmp/output.json

# Resultado: BLOCKED (CRITICAL risk detected)
```

**Status:** ✅ Funcional isoladamente

---

### 3. Pre-YAML Cost Guardrails ✅

**Localização:** `/home/ial/core/cost_guardrails.py`

**Funcionalidades:**
- ✅ Pricing table: EC2, RDS, ElastiCache, S3, ALB, NAT Gateway
- ✅ Detecta instâncias por keywords (large, medium, small, micro)
- ✅ Budget validation (default: $500/mês)
- ✅ Gera alternativas para reduzir custo

**Pricing Table:**
```python
ec2: t3.micro ($0.0104/h), t3.small ($0.0208/h), m5.large ($0.096/h)
rds: db.t3.micro ($0.017/h), db.m5.large ($0.192/h)
elasticache: cache.t3.micro ($0.017/h)
s3: $0.023/GB
alb: $0.0225/h + $0.008/LCU
nat_gateway: $0.045/h + $0.045/GB
```

**Status:** ✅ Funcional

---

### 4. Intelligent Phase Builder ✅

**Localização:** `/home/ial/core/intelligent_phase_builder.py`

**Funcionalidades:**
- ✅ Usa Bedrock (Claude 3 Sonnet) para gerar YAML
- ✅ Aplica AWS best practices automaticamente
- ✅ Corrige riscos detectados pelo IAS
- ✅ Infere phase number e dependencies
- ✅ Adiciona tags: ManagedBy=IAL, CreatedAt

**Prompt Engineering:**
- Security: Encryption at rest/transit, least privilege IAM
- High Availability: Multi-AZ, Auto Scaling, Health checks
- Cost-Optimized: Right-sizing, Reserved Instances, Lifecycle policies
- Observability: CloudWatch Logs, Alarms, Tags

**Status:** ✅ Funcional

---

### 5. RAG Integration ✅

**Localização:** `/home/ial/services/rag/`

**Arquivos:**
- ✅ `retriever.py` - FAISS search
- ✅ `vector.py` - FaissStore
- ✅ `index_builder.py` - Index builder
- ✅ `rag_cli.py` - CLI interface

**Index Criado:**
- ✅ 222 chunks indexados
- ✅ Sources: docs/, phases/, templates/, schemas/
- ✅ Embeddings: amazon.titan-embed-text-v2:0
- ✅ Localização: `/home/ial/.rag/index.json`

**Integração Master Engine:**
- ✅ `_enrich_prompt_with_rag()` adicionado
- ✅ Enriquecimento automático de prompts
- ✅ Fallback gracioso se RAG indisponível

**Status:** ✅ Integrado (mas retrieval retorna 0 resultados - ver PENDENTE #3)

---

### 6. ialctl start - Deployment Automático ✅

**Localização:** `/home/ial/ialctl_integrated.py`

**4 Steps Implementados:**
1. ✅ Deploy Foundation (DynamoDB, S3, IAM, KMS, etc)
2. ✅ Initialize MCP Servers (17 servers)
3. ✅ Validate System Health (6 checks)
4. ✅ Deploy NL Intent Pipeline (9 Lambdas + Step Functions)

**Automação Step 4:**
```python
# Prepara Lambda artifacts (zip)
# Cria S3 bucket (ial-artifacts-{account})
# Upload Lambdas e Layer para S3
# Deploy CloudFormation stack
# Step Functions pronto para uso
```

**Status:** ✅ Funcional

---

### 7. Lambda Handlers ✅

**Localização:** `/home/ial/lambdas/`

**Handlers Criados:**
1. ✅ `ias_validation_handler.py`
2. ✅ `cost_estimation_handler.py`
3. ✅ `phase_builder_handler.py`
4. ✅ `git_commit_pr_handler.py`
5. ✅ `wait_pr_approval_handler.py`
6. ✅ `deploy_cloudformation_handler.py`
7. ✅ `proof_of_creation_handler.py`
8. ✅ `post_deploy_analysis_handler.py`
9. ✅ `drift_detection_handler.py`

**Status:** ✅ Criados e deployados

---

## ❌ PENDENTE (15%)

### 1. Step Functions Payload Chain 🔴 CRÍTICO

**Problema:**
```
KeyError: 'body' ao passar dados entre estados
```

**Causa Raiz:**
Step Functions `lambda:invoke` retorna:
```json
{
  "Payload": {
    "statusCode": 200,
    "body": {...}
  }
}
```

Mas handlers estão tentando acessar:
```python
event['ias_result']['body']  # ❌ ERRADO
```

Deveria ser:
```python
event['ias_result']['Payload']['body']  # ✅ CORRETO
```

**Arquivos a Corrigir:**
1. ❌ `/home/ial/lambdas/phase_builder_handler.py` - linha 34
   - Atual: `ias_result = event['ias_result']['body']`
   - Corrigir: `ias_result = event['ias_result']['Payload']['body']`

2. ❌ `/home/ial/lambdas/git_commit_pr_handler.py` - linha 33
   - Atual: `phase_result = event['phase_result']['body']`
   - Corrigir: `phase_result = event['phase_result']['Payload']['body']`

3. ❌ `/home/ial/lambdas/deploy_cloudformation_handler.py`
   - Verificar extração de `phase_result`

4. ❌ `/home/ial/lambdas/proof_of_creation_handler.py`
   - Verificar extração de `deployment_result`

5. ❌ `/home/ial/lambdas/post_deploy_analysis_handler.py`
   - Verificar extração de `deployment_result`

6. ❌ `/home/ial/lambdas/drift_detection_handler.py`
   - Verificar extração de `deployment_result`

**Solução:**
```python
# Pattern para todos handlers:
def handler(event, context):
    # Extrair Payload corretamente
    previous_result = event['previous_step']['Payload']
    data = previous_result.get('body', previous_result)
    
    # Processar...
    
    return {
        "statusCode": 200,
        "body": {...}
    }
```

**Teste Após Correção:**
```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:221082174220:stateMachine:ial-nl-intent-pipeline \
  --input '{"nl_intent":"quero bucket S3 privado","monthly_budget":500}'

# Monitorar execução
aws stepfunctions describe-execution --execution-arn <ARN>
```

**Prioridade:** 🔴 CRÍTICA - Bloqueia pipeline E2E

---

### 2. Teste E2E Pipeline 🟡 ALTA

**Objetivo:**
Validar fluxo completo de ponta a ponta

**Cenários de Teste:**

**Teste 1: S3 Bucket Privado (Happy Path)**
```bash
Input: "quero um bucket S3 privado com versionamento"
Expected:
  ✅ IAS: safe=true
  ✅ Cost: ~$5/mês (within budget)
  ✅ Phase Builder: gera 50-storage-s3.yaml
  ✅ Git: commit + push
  ✅ Wait: aguarda aprovação
  ✅ Deploy: cria stack
  ✅ Proof: salva audit
  ✅ Analysis: WA score + cost
  ✅ Drift: no drift detected
```

**Teste 2: S3 Público (Security Block)**
```bash
Input: "quero um bucket S3 público"
Expected:
  ❌ IAS: safe=false (CRITICAL risk)
  ❌ Pipeline: FAILED at SecurityRiskDetected
```

**Teste 3: RDS Large (Budget Exceeded)**
```bash
Input: "quero RDS m5.large com 10 réplicas"
Expected:
  ✅ IAS: safe=true
  ❌ Cost: ~$1400/mês (exceeds $500 budget)
  ❌ Pipeline: FAILED at BudgetExceeded
```

**Validação:**
```bash
# Ver histórico de execução
aws stepfunctions get-execution-history \
  --execution-arn <ARN> \
  --query 'events[?type==`TaskSucceeded` || type==`TaskFailed`]'

# Ver output final
aws stepfunctions describe-execution \
  --execution-arn <ARN> \
  --query 'output'
```

**Prioridade:** 🟡 ALTA - Validação essencial

---

### 3. Fix FAISS Binary 🟡 MÉDIA

**Problema:**
```
RAG retrieve retorna 0 resultados
Arquivo .faiss não foi gerado (só JSON)
```

**Causa:**
`FaissStore.build()` não está salvando arquivo binário FAISS

**Localização:** `/home/ial/services/rag/vector.py`

**Investigação Necessária:**
```python
# Verificar implementação de FaissStore
cat /home/ial/services/rag/vector.py

# Verificar se FAISS está instalado
python3 -c "import faiss; print(faiss.__version__)"

# Verificar se arquivo .faiss existe
ls -la /home/ial/.rag/
```

**Solução Esperada:**
```python
# FaissStore.build() deve:
1. Criar índice FAISS em memória
2. Adicionar vetores ao índice
3. Salvar índice binário: faiss.write_index(index, path)
4. Salvar metadados JSON separadamente
```

**Teste Após Correção:**
```python
from services.rag.retriever import retrieve

results = retrieve('S3 bucket encryption', k=3, threshold=0.5)
print(f'Found {len(results)} results')  # Deve retornar > 0
```

**Prioridade:** 🟡 MÉDIA - RAG funciona sem FAISS (fallback)

---

### 4. Integrar Trigger no IAL Prompt 🟢 BAIXA

**Objetivo:**
Detectar intenções de criação e chamar Step Functions automaticamente

**Localização:** `/home/ial/core/ial_master_engine_integrated.py`

**Implementação:**
```python
async def process_user_input(self, user_input: str) -> str:
    # Detectar intenções de criação
    creation_keywords = ['quero', 'criar', 'provisionar', 'deploy', 'preciso']
    
    if any(kw in user_input.lower() for kw in creation_keywords):
        # Trigger Step Functions
        result = await self.trigger_nl_intent_pipeline_sfn(
            nl_intent=user_input,
            monthly_budget=500.0
        )
        
        if result['status'] == 'started':
            return f"✅ Pipeline iniciado!\n\nExecution ARN: {result['execution_arn']}\n\nAcompanhe em: AWS Console → Step Functions"
    
    # Continuar com fluxo normal...
```

**Teste:**
```bash
ialctl

IAL> quero um bucket S3 privado
→ Deve trigger Step Functions automaticamente
→ Retornar execution ARN
```

**Prioridade:** 🟢 BAIXA - Nice to have

---

### 5. Reverse Sync Pipeline 🟢 BAIXA

**Objetivo:**
Detectar mudanças no console AWS e sincronizar com Git

**Arquitetura:**
```
EventBridge Rule (CloudTrail events)
  ↓
Lambda: Detect Console Change
  ↓
Lambda: Discover Resources
  ↓
Lambda: Generate YAML
  ↓
Lambda: Create PR
```

**Recursos Existentes:**
- ✅ `/home/ial/lambda/drift-detector/index.py`
- ✅ `/home/ial/lambda/reconciliation-engine/index.py`
- ✅ `/home/ial/phases/00-foundation/13-ial-drift-detection.yaml` (placeholder)

**Implementação Necessária:**

1. **EventBridge Rule:**
```yaml
# /home/ial/phases/00-foundation/18-reverse-sync-pipeline.yaml
Resources:
  ConsoleChangeRule:
    Type: AWS::Events::Rule
    Properties:
      EventPattern:
        source: [aws.ec2, aws.s3, aws.rds]
        detail-type: [AWS API Call via CloudTrail]
        detail:
          eventName:
            - CreateBucket
            - RunInstances
            - CreateDBInstance
      Targets:
        - Arn: !GetAtt DetectChangeFunction.Arn
```

2. **Lambda: Detect Change**
```python
# Detecta mudança relevante
# Filtra eventos de criação/modificação
# Trigger discovery
```

3. **Lambda: Discover Resources**
```python
# Usa boto3 para descrever recurso
# Extrai configuração completa
# Gera estrutura para YAML
```

4. **Lambda: Generate YAML**
```python
# Usa LLM para gerar CloudFormation
# Baseado na configuração descoberta
# Aplica best practices
```

5. **Lambda: Create PR**
```python
# Commit YAML para Git
# Abre PR com descrição
# Tag: reverse-sync
```

**Prioridade:** 🟢 BAIXA - Feature adicional

---

## 🎯 PLANO DE AÇÃO (Próxima Sessão)

### Fase 1: Corrigir Step Functions (1-2h)

**Passo 1.1:** Corrigir todos Lambda handlers
```bash
cd /home/ial/lambdas

# Corrigir cada handler com pattern:
# event['previous']['Payload'].get('body', event['previous']['Payload'])
```

**Passo 1.2:** Rezipar e fazer upload
```bash
for handler in phase_builder git_commit_pr deploy_cloudformation proof_of_creation post_deploy_analysis drift_detection; do
  zip -q ${handler}_handler.zip ${handler}_handler.py
  aws s3 cp ${handler}_handler.zip s3://ial-artifacts-221082174220/lambdas/
  aws lambda update-function-code \
    --function-name ial-nl-${handler//_/-} \
    --s3-bucket ial-artifacts-221082174220 \
    --s3-key lambdas/${handler}_handler.zip
done
```

**Passo 1.3:** Testar pipeline
```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:221082174220:stateMachine:ial-nl-intent-pipeline \
  --input '{"nl_intent":"quero bucket S3 privado","monthly_budget":500}'
```

---

### Fase 2: Validar E2E (30min)

**Passo 2.1:** Teste Happy Path
```bash
# S3 privado - deve funcionar completo
```

**Passo 2.2:** Teste Security Block
```bash
# S3 público - deve falhar no IAS
```

**Passo 2.3:** Teste Budget Exceeded
```bash
# RDS large - deve falhar no Cost
```

---

### Fase 3: Fix FAISS (30min)

**Passo 3.1:** Investigar FaissStore
```bash
cat /home/ial/services/rag/vector.py
```

**Passo 3.2:** Corrigir build()
```python
# Adicionar faiss.write_index()
```

**Passo 3.3:** Rebuild index
```bash
python3 -c "from services.rag.index_builder import build_index; build_index({})"
```

---

### Fase 4: Integrar Trigger (30min)

**Passo 4.1:** Adicionar detecção de intenção

**Passo 4.2:** Testar via ialctl
```bash
ialctl
IAL> quero bucket S3 privado
```

---

## 📊 Métricas de Sucesso

### Pipeline Funcional:
- ✅ Execução E2E sem erros
- ✅ IAS bloqueia riscos críticos
- ✅ Cost bloqueia budget exceeded
- ✅ Phase Builder gera YAML válido
- ✅ Proof-of-Creation salvo no DynamoDB

### RAG Funcional:
- ✅ Retrieval retorna > 0 resultados
- ✅ Contexto relevante enriquece prompts
- ✅ LLM usa docs reais (não inventa)

### Integração IAL:
- ✅ `ialctl` detecta intenções
- ✅ Trigger Step Functions automático
- ✅ Feedback ao usuário com execution ARN

---

## 🔗 Links Úteis

**AWS Console:**
- Step Functions: https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines
- Lambda: https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions
- S3 Artifacts: https://s3.console.aws.amazon.com/s3/buckets/ial-artifacts-221082174220

**GitHub:**
- Repo: https://github.com/Diego-Nardoni/ial-infrastructure
- Último commit: 303ec17 (feat: Integrar RAG ao IAL Master Engine)

**Comandos Úteis:**
```bash
# Ver status do stack
aws cloudformation describe-stacks --stack-name ial-nl-intent-pipeline

# Listar Lambdas
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `ial-nl-`)].FunctionName'

# Ver execuções Step Functions
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:221082174220:stateMachine:ial-nl-intent-pipeline

# Rebuild ialctl
cd /home/ial
python3 -m PyInstaller --onefile --name ialctl --clean ialctl
```

---

## 📝 Notas Importantes

1. **Idempotência:** Foundation deployer tem bug de duplicação de stacks (conhecido, não crítico)

2. **Bedrock:** Phase Builder usa Claude 3 Sonnet - verificar quotas se muitos testes

3. **S3 Artifacts:** Bucket `ial-artifacts-221082174220` contém todos Lambdas zipados

4. **Git:** Sempre commit antes de testar mudanças críticas

5. **Logs:** CloudWatch Logs para cada Lambda: `/aws/lambda/ial-nl-*`

---

**Última Atualização:** 2025-11-13 21:05 UTC  
**Próxima Revisão:** Após completar Fase 1 (Fix Step Functions)
