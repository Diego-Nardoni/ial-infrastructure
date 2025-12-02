# PLANO DE IMPLEMENTAÇÃO - IAL CONTROL PLANE COGNITIVO COMPLETO

## OBJETIVO
Implementar o fluxo completo do IAL Control Plane:
```
Intenção (NL) → IAS → Cost Guardrails → Phase Builder → GitHub PR → CI/CD → Audit Validator → Drift Engine → Operação Viva
```

## ANÁLISE ATUAL
- ✅ **90% do código já existe** nos componentes isolados
- ❌ **Fluxo não orquestrado** - sistema usa apenas Intelligent Router
- ❌ **CognitiveEngine bypassed** - onde estão todas as funcionalidades avançadas

## FASES DE IMPLEMENTAÇÃO

### FASE 1: ORQUESTRAÇÃO DO FLUXO PRINCIPAL (2 dias)
**Objetivo:** Conectar componentes existentes no fluxo linear

#### 1.1 Modificar Natural Language Processor
- **Arquivo:** `/home/ial/natural_language_processor.py`
- **Ação:** Implementar roteamento inteligente:
  - **Consultas (query):** → Intelligent Router (atual)
  - **Criação (create):** → CognitiveEngine Pipeline Completo
- **Detecção:** Palavras-chave create, deploy, provision, setup, configure

#### 1.2 Ativar CognitiveEngine Pipeline
- **Arquivo:** `/home/ial/core/cognitive_engine.py`
- **Ação:** Garantir que todos os componentes sejam carregados:
  - IAS (Intent Validation Sandbox)
  - Cost Guardrails
  - Phase Builder
  - GitHub Integration
  - Audit Validator

#### 1.3 Implementar Fluxo Linear
- **Arquivo:** `/home/ial/core/cognitive_engine.py`
- **Método:** `process_creation_intent(intent)`
- **Fluxo:**
  ```python
  def process_creation_intent(self, intent):
      # 1. IAS Validation
      ias_result = self.ias.validate_intent(intent)
      if not ias_result['safe']:
          return ias_result['error_message']
      
      # 2. Cost Guardrails
      cost_result = self.cost_guardrails.validate_cost(intent)
      if not cost_result['approved']:
          return cost_result['error_message']
      
      # 3. Phase Builder
      phases = self.phase_builder.generate_phases(intent)
      
      # 4. GitHub PR
      pr_result = self.github_integration.create_pr(phases)
      
      return pr_result
  ```

### FASE 2: ATIVAÇÃO DOS COMPONENTES CORE (1 dia)
**Objetivo:** Garantir que todos os componentes funcionem

#### 2.1 IAS - Intent Validation Sandbox
- **Arquivo:** `/home/ial/ial/core/brain/ias.py`
- **Status:** Código existe, precisa testar
- **Ação:** Verificar método `validate_intent()` funcional

#### 2.2 Cost Guardrails
- **Arquivo:** `/home/ial/core/intent_cost_guardrails.py`
- **Status:** Parcialmente funcional
- **Ação:** Completar método `validate_cost()` com limites

#### 2.3 Phase Builder
- **Arquivo:** `/home/ial/core/phase_builder.py`
- **Status:** Código existe
- **Ação:** Testar geração de phases + DAG

### FASE 3: INTEGRAÇÃO GITHUB + CI/CD (2 dias)
**Objetivo:** Implementar GitOps-first workflow

#### 3.1 GitHub Integration
- **Arquivo:** `/home/ial/core/github_integration.py`
- **Ação:** 
  - Configurar GitHub API token
  - Implementar criação de PR automática
  - Adicionar templates de PR com rationale

#### 3.2 CI/CD Pipeline
- **Arquivo:** `/home/ial/.github/workflows/ial-pipeline.yml`
- **Ação:** Criar workflow:
  ```yaml
  name: IAL Pipeline
  on:
    pull_request:
      paths: ['phases/**']
  
  jobs:
    validate:
      - Policy Check (cfn-guard)
      - Cost Estimation
      - Security Scan
    
    plan:
      - CloudFormation Plan
      - Drift Detection
    
    apply:
      - CloudFormation Deploy
      - Audit Validation
  ```

### FASE 4: AUDIT VALIDATOR + DRIFT ENGINE (1 dia)
**Objetivo:** Garantir auditoria 100% e operação viva

#### 4.1 Audit Validator
- **Arquivo:** `/home/ial/core/audit_validator.py`
- **Ação:** Implementar validação 100%:
  - Comparar desired_state vs AWS real
  - Gerar proof-of-creation
  - Falhar se completeness < 100%

#### 4.2 Drift Engine
- **Arquivo:** `/home/ial/core/drift_engine.py`
- **Status:** Funcional
- **Ação:** Ativar monitoramento contínuo

### FASE 5: TESTES E VALIDAÇÃO (1 dia)
**Objetivo:** Testar fluxo completo end-to-end

#### 5.1 Teste End-to-End
- **Comando:** `"Quero um ECS privado com Redis"`
- **Validação:** 
  - IAS aprova intent
  - Cost dentro do limite
  - Phases geradas corretamente
  - PR criado no GitHub
  - Pipeline CI/CD executado
  - Recursos criados no AWS
  - Audit 100% validado

#### 5.2 Teste de Drift
- **Ação:** Modificar recurso manualmente no AWS
- **Validação:** Drift detectado e auto-healing ativado

## ARQUIVOS PRINCIPAIS A MODIFICAR

### Críticos (obrigatórios)
1. `/home/ial/natural_language_processor.py` - Roteamento create vs query
2. `/home/ial/core/cognitive_engine.py` - Orquestração do pipeline
3. `/home/ial/core/github_integration.py` - Configuração GitHub API

### Secundários (verificação)
4. `/home/ial/ial/core/brain/ias.py` - IAS validation
5. `/home/ial/core/intent_cost_guardrails.py` - Cost limits
6. `/home/ial/core/phase_builder.py` - Phase generation
7. `/home/ial/core/audit_validator.py` - 100% validation

### Novos (criar)
8. `/home/ial/.github/workflows/ial-pipeline.yml` - CI/CD pipeline
9. `/home/ial/config/github_config.yaml` - GitHub settings

## CONFIGURAÇÕES NECESSÁRIAS

### GitHub
- Token de acesso com permissões de PR
- Repositório configurado para receber PRs
- Branch protection rules

### AWS
- Credenciais com permissões CloudFormation
- S3 bucket para states
- DynamoDB para catalog

### Variáveis de Ambiente
```bash
GITHUB_TOKEN=ghp_xxxx
GITHUB_REPO=owner/repo
AWS_REGION=us-east-1
IAL_MODE=production
```

## CRITÉRIOS DE SUCESSO

### Funcional
- ✅ Comando "create ECS" gera PR no GitHub
- ✅ Pipeline CI/CD executa automaticamente
- ✅ Recursos criados no AWS conforme especificado
- ✅ Audit Validator confirma 100% de completeness
- ✅ Drift Engine detecta e corrige mudanças

### Técnico
- ✅ Todos os testes passando
- ✅ Cobertura de código > 80%
- ✅ Documentação atualizada
- ✅ Logs estruturados e observabilidade

## RISCOS E MITIGAÇÕES

### Alto Risco
- **GitHub API limits** → Implementar rate limiting
- **AWS permissions** → Usar least privilege + test account
- **Pipeline failures** → Rollback automático

### Médio Risco
- **Component integration** → Testes unitários extensivos
- **Cost overruns** → Guardrails rigorosos + alerts

## CRONOGRAMA ESTIMADO

```
Dia 1-2: Fase 1 (Orquestração)
Dia 3:   Fase 2 (Componentes Core)
Dia 4-5: Fase 3 (GitHub + CI/CD)
Dia 6:   Fase 4 (Audit + Drift)
Dia 7:   Fase 5 (Testes)
```

**Total: 7 dias úteis (1.5 semanas)**

## ENTREGÁVEIS

1. **Sistema funcional** com fluxo completo
2. **Documentação** atualizada
3. **Testes** cobrindo todos os cenários
4. **Pipeline CI/CD** configurado
5. **Monitoramento** e alertas ativos

## PRÓXIMOS PASSOS

1. **Aprovação do plano**
2. **Setup do ambiente** (GitHub repo, AWS account)
3. **Início da Fase 1** - Orquestração do fluxo

---

**NOTA:** Este plano transforma o IAL de um "sistema de consultas AWS" para um "Control Plane Cognitivo completo" conforme a visão original.
