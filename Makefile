# Makefile para testes do IAL

.PHONY: test test-unit test-integration test-e2e test-quick test-coverage install-deps

# Instalar dependências de teste
install-deps:
	@echo "📦 Instalando dependências de teste..."
	pip install pytest pytest-cov pytest-mock pytest-asyncio

# Executar todos os testes
test:
	@echo "🧪 Executando todos os testes..."
	python3 run_tests.py all

# Testes unitários
test-unit:
	@echo "🔬 Executando testes unitários..."
	python3 run_tests.py unit

# Testes de integração
test-integration:
	@echo "🔗 Executando testes de integração..."
	python3 run_tests.py integration

# Testes end-to-end
test-e2e:
	@echo "🎯 Executando testes end-to-end..."
	python3 run_tests.py e2e

# Testes rápidos (apenas unit)
test-quick:
	@echo "⚡ Executando testes rápidos..."
	python3 run_tests.py quick

# Testes com cobertura
test-coverage:
	@echo "📊 Executando testes com cobertura..."
	python3 run_tests.py all --coverage

# Executar teste específico
test-file:
	@echo "🎯 Executando teste específico: $(FILE)"
	python3 -m pytest $(FILE) -v

# Limpar cache de testes
clean:
	@echo "🧹 Limpando cache de testes..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

# Help
help:
	@echo "Comandos disponíveis:"
	@echo "  make install-deps    - Instalar dependências de teste"
	@echo "  make test           - Executar todos os testes"
	@echo "  make test-unit      - Executar testes unitários"
	@echo "  make test-integration - Executar testes de integração"
	@echo "  make test-e2e       - Executar testes end-to-end"
	@echo "  make test-quick     - Executar testes rápidos"
	@echo "  make test-coverage  - Executar testes com cobertura"
	@echo "  make test-file FILE=path/to/test.py - Executar teste específico"
	@echo "  make clean          - Limpar cache de testes"
