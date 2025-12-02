# Estratégia de Testes IAL - Control Plane Cognitivo

## 1. Categorias de Testes

### 1.1 Testes de Unidade (Unit Tests)
**Objetivo:** Testar componentes isolados
**Cobertura:** 90%+ de code coverage

```bash
# Estrutura de testes
tests/
├── unit/
│   ├── cognitive_engine/
│   │   ├── test_intent_validation.py
│   │   ├── test_cost_guardrails.py
│   │   └── test_phase_builder.py
│   ├── memory/
│   │   ├── test_memory_manager.py
│   │   └── test_context_engine.py
│   ├── mcp/
│   │   ├── test_mcp_router.py
│   │   └── test_mcp_orchestrator.py
│   └── drift/
│       ├── test_drift_detection.py
│       └── test_auto_healer.py
```

### 1.2 Testes de Integração (Integration Tests)
**Objetivo:** Testar interação entre componentes

```python
# Exemplo: test_nlp_to_yaml_pipeline.py
def test_complete_nlp_to_yaml_flow():
    """Testa fluxo completo: NL → IAS → Cost → YAML"""
    intent = "Quero um ECS privado com Redis"
    
    # 1. Intent Validation
    ias_result = ias.validate_intent(intent)
    assert ias_result['safe'] == True
    
    # 2. Cost Guardrails
    cost = cost_guardrails.estimate_cost(intent)
    assert cost < 1000  # Budget limit
    
    # 3. Phase Builder
    phases = phase_builder.generate_phases(intent)
    assert len(phases) >= 3  # VPC, ECS, Redis
    
    # 4. YAML Generation
    yaml_content = yaml_generator.build_yaml(phases)
    assert 'AWS::ECS::Cluster' in yaml_content
```

### 1.3 Testes End-to-End (E2E Tests)
**Objetivo:** Testar fluxo completo em ambiente real

```python
# test_e2e_ecs_deployment.py
@pytest.mark.e2e
def test_complete_ecs_deployment():
    """Testa deploy completo: NL → PR → Apply → Audit"""
    
    # 1. Natural Language Input
    response = ialctl.process("Deploy ECS with Redis for API")
    
    # 2. Verify PR Creation
    pr = github.get_latest_pr()
    assert pr.title.contains("ECS")
    
    # 3. Simulate PR Approval & Merge
    github.approve_and_merge(pr.number)
    
    # 4. Wait for CloudFormation
    stack = wait_for_stack_completion("ial-ecs-stack")
    assert stack.status == "CREATE_COMPLETE"
    
    # 5. Audit Validation
    audit_result = audit_validator.validate_stack(stack.name)
    assert audit_result['completeness'] == 100
    
    # 6. Cleanup
    cleanup_stack(stack.name)
```

## 2. Testes por Funcionalidade

### 2.1 Pipeline Cognitivo
```python
# test_cognitive_pipeline.py
class TestCognitivePipeline:
    
    def test_intent_validation_sandbox(self):
        """Testa IAS - Intent Validation Sandbox"""
        risky_intent = "Create public Redis with no password"
        result = ias.validate_intent(risky_intent)
        assert result['safe'] == False
        assert 'security_risk' in result['issues']
    
    def test_cost_guardrails(self):
        """Testa Pre-YAML Cost Guardrails"""
        expensive_intent = "Deploy 100 r5.24xlarge instances"
        result = cost_guardrails.validate_cost(expensive_intent)
        assert result['approved'] == False
        assert result['estimated_cost'] > 50000
    
    def test_phase_builder_dag(self):
        """Testa geração de DAG de dependências"""
        intent = "ECS cluster with ALB and RDS"
        phases = phase_builder.generate_phases(intent)
        dag = phase_builder.build_dag(phases)
        
        # VPC deve vir antes de ECS
        assert dag.get_order('vpc') < dag.get_order('ecs')
        # RDS deve vir depois de VPC
        assert dag.get_order('vpc') < dag.get_order('rds')
```

### 2.2 GitOps e CI/CD
```python
# test_gitops_flow.py
class TestGitOpsFlow:
    
    def test_pr_creation(self):
        """Testa criação automática de PR"""
        intent = "Simple S3 bucket for logs"
        result = gitops.create_pr(intent)
        
        assert result['pr_url'] is not None
        assert 'S3' in result['pr_title']
        assert result['files_changed'] > 0
    
    def test_ci_cd_pipeline(self):
        """Testa pipeline CI/CD completo"""
        pr_number = create_test_pr()
        
        # Trigger CI/CD
        ci_result = github_actions.trigger_pipeline(pr_number)
        
        # Verify stages
        assert ci_result['lint'] == 'passed'
        assert ci_result['policy_check'] == 'passed'
        assert ci_result['plan'] == 'success'
        assert ci_result['cost_estimate'] < 100
```

### 2.3 Drift Detection e Auto-Healing
```python
# test_drift_management.py
class TestDriftManagement:
    
    def test_drift_detection(self):
        """Testa detecção de drift"""
        # Simula mudança manual no AWS
        modify_resource_manually()
        
        # Executa drift detection
        drift_result = drift_engine.detect_drift()
        
        assert len(drift_result['drifts']) > 0
        assert drift_result['classification'] in ['safe', 'risky']
    
    def test_auto_healing_safe(self):
        """Testa auto-healing para drift seguro"""
        # Simula drift seguro (tags)
        create_safe_drift()
        
        # Auto-heal deve corrigir
        heal_result = auto_healer.heal_safe_drift()
        assert heal_result['healed'] == True
        assert heal_result['time'] < 600  # < 10 min
    
    def test_reverse_sync_risky(self):
        """Testa reverse sync para drift arriscado"""
        # Simula drift arriscado (nova instância)
        create_risky_drift()
        
        # Deve abrir PR para reverse sync
        sync_result = reverse_sync.handle_risky_drift()
        assert sync_result['pr_created'] == True
        assert 'DRIFT' in sync_result['pr_title']
```

## 3. Testes de Performance

### 3.1 Benchmarks de Latência
```python
# test_performance.py
class TestPerformance:
    
    @pytest.mark.benchmark
    def test_nlp_processing_latency(self):
        """Testa latência do processamento NLP"""
        intent = "Deploy microservice with database"
        
        start_time = time.time()
        result = nlp_processor.process(intent)
        end_time = time.time()
        
        latency = end_time - start_time
        assert latency < 5.0  # < 5 segundos
        assert result['confidence'] > 0.8
    
    def test_mcp_router_performance(self):
        """Testa performance do MCP Router"""
        requests = generate_test_requests(100)
        
        start_time = time.time()
        results = [mcp_router.route(req) for req in requests]
        end_time = time.time()
        
        avg_latency = (end_time - start_time) / 100
        assert avg_latency < 0.5  # < 500ms por request
        assert all(r['success'] for r in results)
```

### 3.2 Testes de Carga
```python
# test_load.py
@pytest.mark.load
def test_concurrent_deployments():
    """Testa deployments concorrentes"""
    intents = [
        "Deploy web app with database",
        "Create S3 bucket with CloudFront",
        "Setup ECS cluster with Redis"
    ]
    
    # Executa concorrentemente
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(ialctl.process, intent) 
                  for intent in intents]
        results = [f.result() for f in futures]
    
    # Todos devem ter sucesso
    assert all(r['success'] for r in results)
    # Não deve haver conflitos de recursos
    assert no_resource_conflicts(results)
```

## 4. Testes de Segurança

### 4.1 Security Sentinel
```python
# test_security.py
class TestSecurity:
    
    def test_security_sentinel_detection(self):
        """Testa detecção de vulnerabilidades"""
        vulnerable_config = {
            'security_group': {
                'ingress': [{'port': 22, 'cidr': '0.0.0.0/0'}]
            }
        }
        
        result = security_sentinel.scan(vulnerable_config)
        assert result['vulnerabilities_found'] > 0
        assert 'ssh_open_to_world' in result['issues']
    
    def test_iam_policy_validation(self):
        """Testa validação de políticas IAM"""
        overprivileged_policy = {
            'Statement': [{
                'Effect': 'Allow',
                'Action': '*',
                'Resource': '*'
            }]
        }
        
        result = iam_validator.validate_policy(overprivileged_policy)
        assert result['compliant'] == False
        assert 'overprivileged' in result['issues']
```

## 5. Testes de Chaos Engineering

```python
# test_chaos.py
class TestChaosEngineering:
    
    def test_aws_api_failure_resilience(self):
        """Testa resiliência a falhas da API AWS"""
        with mock_aws_api_failure():
            result = ialctl.process("Deploy simple S3 bucket")
            
            # Deve usar circuit breaker
            assert result['circuit_breaker_triggered'] == True
            # Deve ter fallback
            assert result['fallback_used'] == True
    
    def test_github_api_failure(self):
        """Testa falha na API do GitHub"""
        with mock_github_api_failure():
            result = gitops.create_pr("Test deployment")
            
            # Deve retry com backoff
            assert result['retries'] > 0
            # Deve eventualmente ter sucesso ou falhar graciosamente
            assert result['status'] in ['success', 'failed_gracefully']
```

## 6. Automação de Testes

### 6.1 GitHub Actions Pipeline
```yaml
# .github/workflows/test.yml
name: IAL Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Unit Tests
        run: |
          pytest tests/unit/ -v --cov=ial --cov-report=xml
          
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - name: Run Integration Tests
        run: |
          pytest tests/integration/ -v
          
  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Run E2E Tests
        run: |
          pytest tests/e2e/ -v --aws-profile=test
```

### 6.2 Testes Contínuos
```python
# continuous_testing.py
def run_continuous_tests():
    """Executa testes contínuos em produção"""
    
    # Testes de saúde do sistema
    health_tests = [
        test_mcp_router_health,
        test_drift_detection_active,
        test_cost_guardrails_working,
        test_memory_system_responsive
    ]
    
    for test in health_tests:
        try:
            result = test()
            log_test_result(test.__name__, result)
        except Exception as e:
            alert_ops_team(test.__name__, str(e))
```

## 7. Métricas e Observabilidade

### 7.1 Test Metrics Dashboard
```python
# test_metrics.py
class TestMetrics:
    
    def collect_test_metrics(self):
        """Coleta métricas dos testes"""
        return {
            'unit_test_coverage': get_coverage_percentage(),
            'integration_test_pass_rate': get_integration_pass_rate(),
            'e2e_test_duration': get_avg_e2e_duration(),
            'flaky_test_count': count_flaky_tests(),
            'test_execution_frequency': get_test_frequency()
        }
    
    def publish_metrics(self, metrics):
        """Publica métricas no CloudWatch"""
        for metric_name, value in metrics.items():
            cloudwatch.put_metric_data(
                Namespace='IAL/Testing',
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': 'Count'
                }]
            )
```

## 8. Comandos de Teste

```bash
# Executar todos os testes
ialctl test all

# Testes por categoria
ialctl test unit
ialctl test integration  
ialctl test e2e
ialctl test performance
ialctl test security
ialctl test chaos

# Testes específicos
ialctl test cognitive-pipeline
ialctl test drift-detection
ialctl test cost-guardrails

# Testes com cobertura
ialctl test unit --coverage

# Testes em ambiente específico
ialctl test e2e --env staging
```

Esta estratégia garante cobertura completa de todas as funcionalidades do IAL, desde componentes individuais até fluxos end-to-end complexos.
