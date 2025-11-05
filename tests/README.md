# IAL Test Suite

Estrutura de testes para o sistema IAL (Intelligent Architecture Layer).

## 📁 Estrutura Atual

### 🛠️ Legacy Scripts
Scripts de teste funcionais:
- `test-amazon-q-integration.sh` - Integração Amazon Q
- `test-drift-detection.sh` - Detecção de drift
- `test-idempotency.sh` - Testes de idempotência

## 🚀 Execução

### Scripts legados:
```bash
cd /home/ial/tests
./test-amazon-q-integration.sh
./test-drift-detection.sh
./test-idempotency.sh
```

## 📝 Nota

Os testes Python experimentais foram removidos por não estarem integrados ao pipeline de CI/CD e apresentarem problemas de dependências. Apenas os scripts shell funcionais foram mantidos.
