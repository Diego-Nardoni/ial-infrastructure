# IAL Test Suite

Estrutura organizada de testes para o sistema IAL (Intelligent Architecture Layer).

## 📁 Estrutura

### 🔬 Unit Tests (`unit/`)
Testes de componentes individuais:
- `test_intelligent_router.py` - Testa MCP Router básico
- `test_knowledge_graph_implementation.py` - Testa Knowledge Graph
- `test_audit_validator.py` - Testa validador de auditoria
- `test_desired_state.py` - Testa gerenciamento de estado
- `test_resource_catalog.py` - Testa catálogo de recursos

### 🔗 Integration Tests (`integration/`)
Testes de integração entre componentes:
- `test_integration_phase2.py` - Integração MCP Router + IAL Core
- `test_knowledge_graph_integration.py` - Integração completa Knowledge Graph
- `test_rag_integration.py` - Integração sistema RAG
- `test_stepfunctions_integration.py` - Integração Step Functions

### 🎯 End-to-End Tests (`e2e/`)
Testes completos do sistema:
- `test_end_to_end_phase3.py` - Teste binário ialctl completo
- `test_stepfunctions_complete.py` - Teste completo Step Functions

### 🌍 Scenario Tests (`scenarios/`)
Testes de cenários reais:
- `test_real_scenarios_phase3.py` - Cenários de infraestrutura real

### 🛠️ Legacy Scripts
Scripts de teste legados:
- `test-amazon-q-integration.sh`
- `test-drift-detection.sh`
- `test-idempotency.sh`

## 🚀 Execução

### Executar todos os testes:
```bash
cd /home/ial
python -m pytest tests/ -v
```

### Por categoria:
```bash
# Testes unitários
python -m pytest tests/unit/ -v

# Testes de integração
python -m pytest tests/integration/ -v

# Testes end-to-end
python -m pytest tests/e2e/ -v

# Cenários reais
python -m pytest tests/scenarios/ -v
```

### Executar teste específico:
```bash
python tests/unit/test_intelligent_router.py
```

## 📊 Cobertura

- **Unit**: Componentes individuais
- **Integration**: Interação entre componentes
- **E2E**: Sistema completo
- **Scenarios**: Casos de uso reais

Total: ~1,790 linhas de código de teste
