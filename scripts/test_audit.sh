#!/bin/bash
# Script de teste para Audit Validator

set -e

echo "🔍 Testando Audit Validator..."
echo "================================"

# Navegar para diretório do IAL
cd "$(dirname "$0")/.."

# Verificar se desired_spec existe
if [ ! -f "reports/desired_spec.json" ]; then
    echo "⚠️ desired_spec.json não encontrado, gerando..."
    python3 core/desired_state.py
fi

# Executar Audit Validator
echo "🔍 Executando Audit Validator..."
python3 core/audit_validator.py

audit_exit_code=$?

if [ $audit_exit_code -eq 0 ]; then
    echo "✅ Audit Validator executado com sucesso"
    
    # Verificar se relatório foi gerado
    if [ -f "reports/creation_audit.json" ]; then
        echo "✅ creation_audit.json gerado com sucesso"
        
        # Mostrar estatísticas básicas
        echo "📊 Estatísticas da auditoria:"
        python3 -c "
import json
with open('reports/creation_audit.json', 'r') as f:
    audit = json.load(f)
print(f'  🎯 Completeness: {audit.get(\"completeness\", 0)}%')
print(f'  📋 Recursos desejados: {audit.get(\"desired_total\", 0)}')
print(f'  ✅ Recursos encontrados: {audit.get(\"summary\", {}).get(\"total_found\", 0)}')
print(f'  ❌ Recursos ausentes: {audit.get(\"summary\", {}).get(\"total_missing\", 0)}')
print(f'  ➕ Recursos extras: {audit.get(\"summary\", {}).get(\"total_extra\", 0)}')
print(f'  🚨 Auditoria passou: {audit.get(\"audit_passed\", False)}')
"
    else
        echo "❌ creation_audit.json não foi gerado"
        exit 1
    fi
    
else
    echo "❌ Audit Validator falhou - Pipeline gate não passou"
    echo "📄 Verifique creation_audit.json para detalhes dos recursos ausentes"
    exit $audit_exit_code
fi

echo ""
echo "🎉 Teste do Audit Validator concluído!"
