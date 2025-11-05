#!/bin/bash

echo "🧠 DeepSeek Fallback Setup"
echo "=========================="
echo ""
echo "DeepSeek será usado como fallback inteligente quando Bedrock não estiver disponível."
echo "API gratuita disponível em: https://platform.deepseek.com"
echo ""
echo "Configurar DeepSeek agora? (y/n)"

read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "📝 Passos:"
    echo "1. Visite: https://platform.deepseek.com/api_keys"
    echo "2. Crie conta gratuita (se necessário)"
    echo "3. Gere API key"
    echo "4. Cole abaixo:"
    echo ""
    read -r -p "DeepSeek API Key: " api_key
    
    if [ -n "$api_key" ]; then
        # Adiciona ao parameters.env
        if [ -f "parameters.env" ]; then
            # Remove linha existente se houver
            sed -i '/DEEPSEEK_API_KEY/d' parameters.env
            echo "DEEPSEEK_API_KEY=$api_key" >> parameters.env
            echo "✅ DeepSeek configurado em parameters.env"
        else
            echo "DEEPSEEK_API_KEY=$api_key" > parameters.env
            echo "✅ Arquivo parameters.env criado com DeepSeek"
        fi
        
        # Testa a configuração
        echo ""
        echo "🧪 Testando DeepSeek..."
        export DEEPSEEK_API_KEY=$api_key
        
        python3 -c "
import sys, os
sys.path.append('core/providers')
try:
    from deepseek_provider import chat
    response, latency = chat('Hello, this is a test')
    print(f'✅ DeepSeek funcionando! Latência: {latency:.2f}s')
    print(f'📝 Resposta: {response[:100]}...')
except Exception as e:
    print(f'❌ Erro no teste: {e}')
"
        
        echo ""
        echo "🎉 DeepSeek configurado como fallback inteligente!"
        echo "💡 Agora o IAL usará DeepSeek quando Bedrock não estiver disponível"
        
    else
        echo "❌ API key vazia. Configuração cancelada."
    fi
else
    echo "⏭️ Configuração DeepSeek pulada."
    echo "💡 Para configurar depois: ./scripts/setup_deepseek.sh"
fi

echo ""
echo "📚 Benefícios do DeepSeek Fallback:"
echo "  • Fallback inteligente gratuito"
echo "  • Entende linguagem natural complexa"
echo "  • Mantém experiência conversacional"
echo "  • Zero impacto no modo principal (Bedrock)"
