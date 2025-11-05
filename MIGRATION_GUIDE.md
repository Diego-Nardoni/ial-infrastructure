# Guia de Migração - Separação Control Plane vs Workloads

## Visão Geral da Migração

Esta migração introduz separação operacional entre Control Plane e Workloads no IAL, mantendo **100% de compatibilidade** com o processo atual.

## Antes vs Depois

### ANTES (Processo Atual)
```bash
# Um único deployment com 44 componentes
python3 setup.py
python3 core/desired_state.py
```

### DEPOIS (Novo Processo)
```bash
# Opção 1: Separado (recomendado)
python3 setup_enhanced.py --deployment-type control_plane  # 16 componentes
python3 setup_enhanced.py --deployment-type workloads      # 28 componentes

# Opção 2: Compatibilidade total (funciona igual ao antes)
python3 setup_enhanced.py --deployment-type full           # 44 componentes
python3 core/desired_state_compatible.py                   # Modo legacy
```

## Plano de Migração

### Fase 1: Validação (Sem Risco)
```bash
# 1. Verificar se novos arquivos existem
python3 setup_enhanced.py --status

# 2. Testar dry-run dos novos modos
python3 setup_enhanced.py --deployment-type control_plane --dry-run
python3 setup_enhanced.py --deployment-type workloads --dry-run

# 3. Comparar com modo full
python3 setup_enhanced.py --deployment-type full --dry-run
```

**Resultado esperado**: Todos os comandos devem funcionar sem erros.

### Fase 2: Teste Paralelo (Sem Impacto)
```bash
# 1. Gerar specs separados (não afeta deployment atual)
python3 core/desired_state_enhanced.py \
  --deployment-file phases/deployment-control-plane.yaml \
  --deployment-type control_plane

python3 core/desired_state_enhanced.py \
  --deployment-file phases/deployment-workloads.yaml \
  --deployment-type workloads

# 2. Comparar com spec atual
python3 core/desired_state_compatible.py

# 3. Verificar arquivos gerados em reports/
ls -la reports/desired_spec*.json
```

**Resultado esperado**: Specs gerados com contagens corretas (16 + 28 = 44 total).

### Fase 3: Migração Gradual (Baixo Risco)
```bash
# Opção A: Continuar com processo atual
python3 setup_enhanced.py --deployment-type full

# Opção B: Migrar para separação
python3 setup_enhanced.py --deployment-type control_plane
python3 setup_enhanced.py --deployment-type workloads
```

**Resultado esperado**: Ambas as opções devem produzir o mesmo resultado final.

### Fase 4: Adoção Completa (Quando Confortável)
```bash
# Usar separação como padrão
python3 setup_enhanced.py --deployment-type control_plane
python3 setup_enhanced.py --deployment-type workloads
```

## Cenários de Migração

### Cenário 1: Ambiente de Desenvolvimento
```bash
# Migração imediata - baixo risco
python3 setup_enhanced.py --deployment-type control_plane --dry-run
python3 setup_enhanced.py --deployment-type workloads --dry-run

# Se tudo OK, executar
python3 setup_enhanced.py --deployment-type control_plane
python3 setup_enhanced.py --deployment-type workloads
```

### Cenário 2: Ambiente de Produção
```bash
# Manter processo atual durante transição
python3 setup_enhanced.py --deployment-type full

# Testar separação em paralelo
python3 setup_enhanced.py --deployment-type control_plane --dry-run
python3 setup_enhanced.py --deployment-type workloads --dry-run

# Migrar quando validado
python3 setup_enhanced.py --deployment-type control_plane
python3 setup_enhanced.py --deployment-type workloads
```

### Cenário 3: CI/CD Pipeline
```yaml
# Manter compatibilidade
- name: Deploy IAL (Compatível)
  run: python3 setup_enhanced.py --deployment-type full

# Ou migrar para separação
- name: Deploy Control Plane
  run: python3 setup_enhanced.py --deployment-type control_plane
  
- name: Deploy Workloads  
  run: python3 setup_enhanced.py --deployment-type workloads
```

## Validação da Migração

### Checklist de Validação
- [ ] `python3 setup_enhanced.py --status` mostra 16 + 28 + 44 phases
- [ ] Dry-runs funcionam sem erro para todos os tipos
- [ ] Specs gerados têm contagens corretas de recursos
- [ ] Modo legacy continua funcionando
- [ ] Arquivos de deployment existem e são válidos

### Comandos de Validação
```bash
# 1. Status geral
python3 setup_enhanced.py --status

# 2. Contagem de fases
echo "Control Plane:" && grep -c "00-foundation" phases/deployment-control-plane.yaml
echo "Workloads:" && grep -c "^  -" phases/deployment-workloads.yaml  
echo "Full:" && grep -c "^-" phases/deployment-order.yaml

# 3. Teste completo
python3 test_deployment_separation.py
```

## Rollback (Se Necessário)

### Rollback Simples
```bash
# Usar modo full (idêntico ao processo original)
python3 setup_enhanced.py --deployment-type full
python3 core/desired_state_compatible.py
```

### Rollback Completo
```bash
# Usar ferramentas originais (se ainda existirem)
python3 setup.py
python3 core/desired_state.py
```

## Troubleshooting

### Problema: "Deployment file not found"
```bash
# Verificar se arquivos foram criados
ls -la phases/deployment-*.yaml

# Recriar se necessário (baseado no plano original)
```

### Problema: "Contagem de fases incorreta"
```bash
# Verificar deployment-order.yaml original
grep -c "^-" phases/deployment-order.yaml  # Deve ser 44

# Verificar separação
grep -c "^  -" phases/deployment-control-plane.yaml  # Deve ser 16
grep -c "^  -" phases/deployment-workloads.yaml     # Deve ser 28
```

### Problema: "Specs diferentes entre modos"
```bash
# Comparar recursos totais
python3 core/desired_state_compatible.py | grep "Resources:"
python3 core/desired_state_enhanced.py --deployment-type control_plane | grep "Resources:"
python3 core/desired_state_enhanced.py --deployment-type workloads | grep "Resources:"
```

## Suporte

### Logs e Debugging
```bash
# Executar com verbose (se disponível)
python3 setup_enhanced.py --deployment-type control_plane --verbose

# Verificar logs de deployment
tail -f /var/log/ial-deployment.log
```

### Contato
- **Documentação**: `README_DEPLOYMENT_SEPARATION.md`
- **Testes**: `python3 test_deployment_separation.py`
- **Issues**: Reportar problemas com logs completos

## Cronograma Sugerido

### Semana 1: Validação
- Executar testes em ambiente de desenvolvimento
- Validar contagens e specs gerados
- Documentar qualquer discrepância

### Semana 2: Teste Paralelo
- Executar ambos os processos em paralelo
- Comparar resultados e performance
- Ajustar se necessário

### Semana 3: Migração Gradual
- Migrar ambiente de desenvolvimento
- Manter produção no modo full
- Monitorar comportamento

### Semana 4: Adoção Completa
- Migrar produção se tudo estável
- Atualizar documentação e processos
- Treinar equipe nos novos comandos
