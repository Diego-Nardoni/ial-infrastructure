# ARQUIVOS A MODIFICAR - IAL CONTROL PLANE

## ARQUIVOS CRÍTICOS (OBRIGATÓRIOS)

### 1. `/home/ial/natural_language_processor.py`
**Modificação:** Implementar roteamento inteligente
```python
# ADICIONAR após linha ~513
def _detect_intent_type(self, user_input):
    """Detecta se é consulta ou criação"""
    create_keywords = ['create', 'deploy', 'provision', 'setup', 'configure', 'quero', 'preciso']
    query_keywords = ['quantas', 'quantos', 'liste', 'listar', 'show', 'ver']
    
    if any(keyword in user_input.lower() for keyword in create_keywords):
        return 'create'
    elif any(keyword in user_input.lower() for keyword in query_keywords):
        return 'query'
    else:
        return 'query'  # default

# MODIFICAR método process_command
if intent_type == 'create':
    return self._process_creation_intent(user_input, user_id, session_id)
else:
    # Usar Intelligent Router (atual)
    return self._process_query_intent(user_input, user_id, session_id)
```

### 2. `/home/ial/core/cognitive_engine.py`
**Modificação:** Implementar pipeline linear completo
```python
# ADICIONAR método
def process_creation_intent(self, intent):
    """Pipeline completo: IAS → Cost → Phase → GitHub"""
    
    # 1. IAS Validation
    if self.ias:
        ias_result = self.ias.validate_intent(intent)
        if not ias_result.get('safe', False):
            return f"🚫 IAS: {ias_result.get('error', 'Intent não aprovado')}"
    
    # 2. Cost Guardrails
    if self.cost_guardrails:
        cost_result = self.cost_guardrails.validate_cost(intent)
        if not cost_result.get('approved', False):
            return f"💸 Cost: {cost_result.get('error', 'Custo excede limite')}"
    
    # 3. Phase Builder
    if self.phase_builder:
        phases = self.phase_builder.generate_phases(intent)
        if not phases:
            return "⚠️ Phase Builder: Falha ao gerar phases"
    
    # 4. GitHub PR
    if self.github_integration:
        pr_result = self.github_integration.create_pr(phases, intent)
        return f"✅ PR criado: {pr_result.get('pr_url', 'N/A')}"
    
    return "⚠️ Pipeline incompleto - alguns componentes não disponíveis"
```

### 3. `/home/ial/core/github_integration.py`
**Modificação:** Implementar criação de PR
```python
# ADICIONAR método
def create_pr(self, phases, intent):
    """Cria PR no GitHub com phases geradas"""
    try:
        # Criar branch
        branch_name = f"ial-deploy-{int(time.time())}"
        
        # Commit phases
        for phase_name, phase_content in phases.items():
            file_path = f"phases/{phase_name}.yaml"
            # Commit file to branch
        
        # Criar PR
        pr_data = {
            'title': f'IAL Deploy: {intent[:50]}...',
            'body': self._generate_pr_body(phases, intent),
            'head': branch_name,
            'base': 'main'
        }
        
        # GitHub API call
        pr_response = self._github_api_call('POST', '/pulls', pr_data)
        
        return {
            'success': True,
            'pr_url': pr_response.get('html_url'),
            'pr_number': pr_response.get('number')
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

## ARQUIVOS SECUNDÁRIOS (VERIFICAÇÃO)

### 4. `/home/ial/ial/core/brain/ias.py`
**Verificar:** Método `validate_intent()` funcional
```python
def validate_intent(self, intent):
    """Valida se intent é seguro para execução"""
    # Verificar se método existe e retorna formato correto
    return {'safe': True/False, 'error': 'mensagem'}
```

### 5. `/home/ial/core/intent_cost_guardrails.py`
**Completar:** Método `validate_cost()` com limites
```python
def validate_cost(self, intent):
    """Valida se custo está dentro do limite"""
    estimated_cost = self.estimate_intent_cost(intent)
    budget_limit = self.get_budget_limit()
    
    return {
        'approved': estimated_cost <= budget_limit,
        'estimated_cost': estimated_cost,
        'budget_limit': budget_limit,
        'error': f'Custo ${estimated_cost} excede limite ${budget_limit}' if estimated_cost > budget_limit else None
    }
```

### 6. `/home/ial/core/phase_builder.py`
**Verificar:** Geração de phases + DAG
```python
def generate_phases(self, intent):
    """Gera phases baseado na intenção"""
    # Verificar se retorna dict com phases
    return {
        'phase_01_vpc': 'yaml_content',
        'phase_02_ecs': 'yaml_content',
        'phase_03_redis': 'yaml_content'
    }
```

### 7. `/home/ial/core/audit_validator.py`
**Implementar:** Validação 100%
```python
def validate_deployment(self, desired_state, actual_state):
    """Valida se deployment está 100% completo"""
    completeness = self.calculate_completeness(desired_state, actual_state)
    
    return {
        'completeness': completeness,
        'valid': completeness == 100,
        'missing_resources': self.find_missing_resources(desired_state, actual_state)
    }
```

## ARQUIVOS NOVOS (CRIAR)

### 8. `/home/ial/.github/workflows/ial-pipeline.yml`
**Criar:** Pipeline CI/CD completo
```yaml
name: IAL Control Plane Pipeline

on:
  pull_request:
    paths: ['phases/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Policy Check
        run: cfn-guard validate --rules policies/ --data phases/
      - name: Cost Estimation
        run: ialctl cost estimate phases/
      - name: Security Scan
        run: ialctl security scan phases/

  plan:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - name: CloudFormation Plan
        run: aws cloudformation create-change-set
      - name: Drift Detection
        run: ialctl drift detect

  apply:
    needs: plan
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - name: CloudFormation Deploy
        run: aws cloudformation execute-change-set
      - name: Audit Validation
        run: ialctl audit validate
```

### 9. `/home/ial/config/github_config.yaml`
**Criar:** Configurações GitHub
```yaml
github:
  token: ${GITHUB_TOKEN}
  repository: ${GITHUB_REPO}
  base_branch: main
  pr_template: |
    ## IAL Deployment Request
    
    **Intent:** {{ intent }}
    
    **Phases Generated:**
    {% for phase in phases %}
    - {{ phase.name }}: {{ phase.description }}
    {% endfor %}
    
    **Cost Estimate:** ${{ cost_estimate }}
    
    **Security Validation:** {{ security_status }}
```

## CONFIGURAÇÕES ADICIONAIS

### 10. `/home/ial/.env`
**Adicionar:** Variáveis de ambiente
```bash
# GitHub Integration
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_REPO=owner/ial-infrastructure
GITHUB_BASE_BRANCH=main

# Pipeline Configuration
IAL_MODE=production
ENABLE_GITHUB_INTEGRATION=true
ENABLE_AUDIT_VALIDATION=true
ENABLE_DRIFT_DETECTION=true

# Cost Guardrails
DEFAULT_BUDGET_LIMIT=1000
COST_ALERT_THRESHOLD=800
```

### 11. `/home/ial/config/pipeline_config.yaml`
**Criar:** Configuração do pipeline
```yaml
pipeline:
  stages:
    - name: ias_validation
      enabled: true
      timeout: 30
    - name: cost_guardrails
      enabled: true
      budget_limit: 1000
    - name: phase_builder
      enabled: true
      max_phases: 10
    - name: github_pr
      enabled: true
      auto_merge: false
    - name: audit_validator
      enabled: true
      completeness_threshold: 100
    - name: drift_engine
      enabled: true
      check_interval: 300
```

## ORDEM DE MODIFICAÇÃO

1. **Primeiro:** `natural_language_processor.py` (roteamento)
2. **Segundo:** `cognitive_engine.py` (pipeline)
3. **Terceiro:** `github_integration.py` (PR creation)
4. **Quarto:** Verificar componentes secundários
5. **Quinto:** Criar arquivos novos (CI/CD)
6. **Sexto:** Configurações e variáveis

## COMANDOS DE TESTE

```bash
# Testar cada modificação
python3 -c "from natural_language_processor import IaLNaturalProcessor; p=IaLNaturalProcessor(); print(p._detect_intent_type('create ECS'))"

# Testar pipeline
python3 -c "from core.cognitive_engine import CognitiveEngine; c=CognitiveEngine(); print(c.process_creation_intent('deploy ECS'))"

# Testar GitHub integration
python3 -c "from core.github_integration import GitHubIntegration; g=GitHubIntegration(); print(g.create_pr({}, 'test'))"
```
