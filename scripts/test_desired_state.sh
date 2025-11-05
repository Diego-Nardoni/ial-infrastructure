#!/bin/bash
# Script de teste para Desired State Builder

set -e

echo "🧪 Testando Desired State Builder..."
echo "=================================="

# Navegar para diretório do IAL
cd "$(dirname "$0")/.."

# Executar Desired State Builder
echo "📋 Executando Desired State Builder..."
python3 core/desired_state.py

if [ $? -eq 0 ]; then
    echo "✅ Desired State Builder executado com sucesso"
    
    # Verificar se arquivo foi gerado
    if [ -f "reports/desired_spec.json" ]; then
        echo "✅ desired_spec.json gerado com sucesso"
        
        # Mostrar estatísticas básicas
        echo "📊 Estatísticas do desired_spec.json:"
        python3 -c "
import json
with open('reports/desired_spec.json', 'r') as f:
    spec = json.load(f)
print(f'  🏗️ Domínios: {len(spec.get(\"domains\", {}))}')
print(f'  📦 Recursos: {len(spec.get(\"resources\", []))}')
print(f'  🔗 Dependências: {len(spec.get(\"dependencies\", {}))}')
print(f'  🔑 Hash: {spec.get(\"metadata\", {}).get(\"spec_hash\", \"N/A\")}')
"
    else
        echo "❌ desired_spec.json não foi gerado"
        exit 1
    fi
    
    # Verificar se relatório resumido foi gerado
    if [ -f "reports/desired_spec_summary.json" ]; then
        echo "✅ Relatório resumido gerado com sucesso"
    else
        echo "⚠️ Relatório resumido não foi gerado"
    fi
    
else
    echo "❌ Erro ao executar Desired State Builder"
    exit 1
fi

echo ""
echo "🎉 Teste do Desired State Builder concluído com sucesso!"
