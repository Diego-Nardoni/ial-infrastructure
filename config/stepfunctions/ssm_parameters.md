# SSM Parameters para Circuit Breaker

## Parâmetros Obrigatórios

### /ial/circuit_breaker/state
- **Tipo**: String
- **Valores**: `open` | `half_open` | `closed`
- **Default**: `closed`
- **Descrição**: Estado atual do circuit breaker

### /ial/circuit_breaker/max_inflight
- **Tipo**: String (número)
- **Default**: `3`
- **Descrição**: Máximo de execuções simultâneas permitidas

### /ial/circuit_breaker/retry_after_sec
- **Tipo**: String (número)
- **Default**: `120`
- **Descrição**: Tempo em segundos para retry quando circuit está open

## Comandos AWS CLI para Criação

```bash
# Estado do circuit breaker
aws ssm put-parameter \
  --name "/ial/circuit_breaker/state" \
  --value "closed" \
  --type "String" \
  --description "Circuit breaker state"

# Máximo de execuções simultâneas
aws ssm put-parameter \
  --name "/ial/circuit_breaker/max_inflight" \
  --value "3" \
  --type "String" \
  --description "Maximum concurrent executions"

# Tempo de retry
aws ssm put-parameter \
  --name "/ial/circuit_breaker/retry_after_sec" \
  --value "120" \
  --type "String" \
  --description "Retry after seconds when circuit is open"
```

## Operação Manual

### Abrir Circuit Breaker (Emergência)
```bash
aws ssm put-parameter \
  --name "/ial/circuit_breaker/state" \
  --value "open" \
  --overwrite
```

### Fechar Circuit Breaker
```bash
aws ssm put-parameter \
  --name "/ial/circuit_breaker/state" \
  --value "closed" \
  --overwrite
```
