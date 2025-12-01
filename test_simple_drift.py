#!/usr/bin/env python3
"""
Teste simples da função drift
"""

import sys
sys.path.insert(0, '/home/ial')

def test_drift_simple():
    try:
        from natural_language_processor import IaLNaturalProcessor
        processor = IaLNaturalProcessor()
        
        # Verificar se a função existe
        if hasattr(processor, '_detect_drift_commands'):
            print("✅ Função _detect_drift_commands encontrada")
            
            # Testar a função
            result = processor._detect_drift_commands('mostrar drift')
            if result:
                print("✅ Função retornou resultado:", result[:100] + "...")
            else:
                print("⚠️ Função retornou None (esperado se não há drift)")
            
            return True
        else:
            print("❌ Função _detect_drift_commands NÃO encontrada")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    test_drift_simple()
