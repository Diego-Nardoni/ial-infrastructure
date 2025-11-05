# IAL Deployment Separation - Control Plane vs Workloads

## Overview

O IAL agora suporta separação operacional entre **Control Plane** (plataforma IAL) e **Workloads** (infraestrutura do usuário), permitindo deployments independentes e governança diferenciada.

## Arquitetura

### Control Plane (16 componentes)
- **Localização**: `00-foundation/`
- **Propósito**: Gerencia a plataforma IAL
- **Componentes**: DynamoDB state, logging, reconciliação, Step Functions, etc.
- **Deploy**: Uma vez durante setup inicial, mudanças raras
- **Governança**: Políticas rígidas de drift protection

### Workload Plane (28 componentes)  
- **Localização**: `10-security/`, `20-network/`, `30-compute/`, etc.
- **Propósito**: Entrega valor de negócio aos usuários
- **Componentes**: VPC, ECS, RDS, Lambda functions de aplicação
- **Deploy**: Frequente conforme necessidades dos usuários
- **Governança**: Flexibilidade para modificações

## Arquivos de Deployment

### deployment-control-plane.yaml
```yaml
metadata:
  deployment_type: "control_plane"
  total_phases: 16
execution_order:
  - 00-foundation/01-dynamodb-state
  - 00-foundation/02-logging-infrastructure
  # ... 14 mais componentes
```

### deployment-workloads.yaml
```yaml
metadata:
  deployment_type: "workloads" 
  total_phases: 28
execution_order:
  - 10-security/01-kms-security
  - 20-network/01-networking
  # ... 26 mais componentes
```

### deployment-order.yaml (compatibilidade)
- Mantém todos os 44 componentes
- Garante compatibilidade com processo atual

## Ferramentas

### setup_enhanced.py
```bash
# Status dos deployments
python3 setup_enhanced.py --status

# Deploy apenas Control Plane
python3 setup_enhanced.py --deployment-type control_plane

# Deploy apenas Workloads  
python3 setup_enhanced.py --deployment-type workloads

# Deploy completo (padrão)
python3 setup_enhanced.py --deployment-type full

# Dry run (visualizar sem executar)
python3 setup_enhanced.py --deployment-type control_plane --dry-run
```

### desired_state_enhanced.py
```bash
# Gerar spec para Control Plane
python3 core/desired_state_enhanced.py \
  --deployment-file phases/deployment-control-plane.yaml \
  --deployment-type control_plane

# Gerar spec para Workloads
python3 core/desired_state_enhanced.py \
  --deployment-file phases/deployment-workloads.yaml \
  --deployment-type workloads
```

### desired_state_compatible.py
```bash
# Modo compatível com deployment específico
python3 core/desired_state_compatible.py \
  --deployment-file phases/deployment-control-plane.yaml

# Modo legacy (scan de diretórios)
python3 core/desired_state_compatible.py
```

## Casos de Uso

### 1. Setup Inicial do IAL
```bash
# 1. Deploy Control Plane primeiro
python3 setup_enhanced.py --deployment-type control_plane

# 2. Deploy Workloads depois
python3 setup_enhanced.py --deployment-type workloads
```

### 2. Modificação de Workloads
```bash
# Re-deploy apenas workloads sem afetar Control Plane
python3 setup_enhanced.py --deployment-type workloads
```

### 3. Troubleshooting
```bash
# Verificar status
python3 setup_enhanced.py --status

# Dry run para validar mudanças
python3 setup_enhanced.py --deployment-type workloads --dry-run
```

### 4. Multi-tenancy (futuro)
```bash
# Control Plane compartilhado
python3 setup_enhanced.py --deployment-type control_plane

# Workloads por tenant
python3 setup_enhanced.py --deployment-type workloads --tenant tenant-a
```

## Benefícios

### Operacionais
- **Segurança**: Control Plane estável, workloads flexíveis
- **Troubleshooting**: Problemas isolados por plano
- **Performance**: Deployments mais rápidos e focados

### Estratégicos  
- **Multi-tenancy**: Um Control Plane para múltiplos workloads
- **Governança**: Políticas diferenciadas por plano
- **Escalabilidade**: Facilita crescimento do IAL

## Compatibilidade

- ✅ **Mantém compatibilidade total** com processo atual
- ✅ **deployment-order.yaml** continua funcionando
- ✅ **desired_state.py** original não é afetado
- ✅ **Migração gradual** sem disrupção

## Testes

Execute a suíte de testes completa:
```bash
python3 test_deployment_separation.py
```

## Migração

### Passo 1: Validação
```bash
# Verificar se arquivos foram criados
python3 setup_enhanced.py --status
```

### Passo 2: Teste
```bash
# Testar Control Plane
python3 setup_enhanced.py --deployment-type control_plane --dry-run

# Testar Workloads
python3 setup_enhanced.py --deployment-type workloads --dry-run
```

### Passo 3: Implementação Gradual
```bash
# Continuar usando modo full durante transição
python3 setup_enhanced.py --deployment-type full

# Migrar para separação quando pronto
python3 setup_enhanced.py --deployment-type control_plane
python3 setup_enhanced.py --deployment-type workloads
```

## Próximos Passos

1. **Validação em ambiente de desenvolvimento**
2. **Integração com CI/CD pipelines**
3. **Implementação de multi-tenancy**
4. **Políticas de governança diferenciadas**
5. **Monitoramento separado por plano**
