#!/bin/bash

# IaL - Infrastructure as Language
# Script de Instalação Automática

echo "🚀 IaL - Infrastructure as Language"
echo "Instalação Automática"
echo "=" * 50

# Verificar se está no diretório correto
if [ ! -f "setup.py" ]; then
    echo "❌ Execute este script no diretório /home/ial"
    exit 1
fi

# Executar instalação
echo "🔧 Iniciando instalação..."
python3 setup.py << EOF
instalar tudo
EOF

# Ativar alias no shell atual
echo ""
echo "🔄 Ativando alias 'ial'..."
source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || source ~/.profile 2>/dev/null

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "📋 Próximos passos:"
echo "1. Execute: source ~/.bashrc"
echo "2. Digite: ial"
echo "3. Ou use: python3 natural_language_processor.py interactive"
echo ""
echo "💡 Exemplo de uso:"
echo "   ial"
echo "   👤 Você: Qual o status da minha infraestrutura?"
echo ""
