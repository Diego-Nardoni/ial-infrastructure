#!/usr/bin/env python3
"""
Script de Teste das Novas Funcionalidades Conversacionais do IAL
Valida integração MCP AWS Official, Preview Mode, Drift Integration e Memory System
"""

import sys
import os
sys.path.insert(0, '/home/ial')

def test_cognitive_engine_integration():
    """Testa integração do CognitiveEngine com MCP AWS Official"""
    print("🧠 Testando CognitiveEngine com MCP Integration...")
    
    try:
        from core.cognitive_engine import CognitiveEngine
        
        engine = CognitiveEngine()
        
        # Teste 1: Verificar se componentes foram inicializados
        assert hasattr(engine, 'mcp_orchestrator'), "MCP Orchestrator não inicializado"
        assert hasattr(engine, 'memory_manager'), "Memory Manager não inicializado"
        assert hasattr(engine, 'context_engine'), "Context Engine não inicializado"
        
        # Teste 2: Verificar função de completude
        incomplete_result = engine.is_intent_incomplete("criar uma aplicação")
        assert not incomplete_result['complete'], "Deveria detectar intenção incompleta"
        assert 'clarification_question' in incomplete_result, "Deveria ter pergunta de esclarecimento"
        
        complete_result = engine.is_intent_incomplete("criar uma aplicação web pública na região us-east-1 de tamanho médio com alta disponibilidade")
        assert complete_result['complete'], "Deveria detectar intenção completa"
        
        print("✅ CognitiveEngine: Todos os testes passaram")
        return True
        
    except Exception as e:
        print(f"❌ CognitiveEngine: {e}")
        return False

def test_master_engine_preview_mode():
    """Testa Preview Mode no MasterEngine"""
    print("🔍 Testando Preview Mode...")
    
    try:
        from core.master_engine_final import MasterEngineFinal
        
        engine = MasterEngineFinal()
        
        # Teste 1: Verificar se preview mode existe
        assert hasattr(engine, 'process_preview_mode'), "Preview mode não implementado"
        assert hasattr(engine, '_generate_predicted_phases'), "Geração de fases previstas não implementada"
        
        # Teste 2: Testar preview de aplicação web
        result = engine.process_preview_mode("criar uma aplicação web com banco de dados")
        
        assert result['status'] == 'preview_ready', f"Status incorreto: {result.get('status')}"
        assert 'predicted_phases' in result, "Fases previstas não retornadas"
        assert 'cost_estimate' in result, "Estimativa de custo não retornada"
        assert 'risk_assessment' in result, "Avaliação de risco não retornada"
        assert result['requires_confirmation'], "Deveria requerer confirmação"
        
        # Teste 3: Verificar se fases fazem sentido
        phases = result['predicted_phases']
        phase_names = [p['name'] for p in phases]
        
        assert '00-foundation' in phase_names, "Foundation deveria estar incluída"
        assert any('network' in name for name in phase_names), "Network deveria estar incluída para web app"
        assert any('compute' in name for name in phase_names), "Compute deveria estar incluída para web app"
        
        print("✅ Preview Mode: Todos os testes passaram")
        return True
        
    except Exception as e:
        print(f"❌ Preview Mode: {e}")
        return False

def test_drift_integration():
    """Testa integração do Drift Engine no chat"""
    print("🔄 Testando Drift Integration...")
    
    try:
        from natural_language_processor import IaLNaturalProcessor
        
        processor = IaLNaturalProcessor()
        
        # Teste 1: Verificar se função de detecção existe
        assert hasattr(processor, '_detect_drift_commands'), "Detecção de drift não implementada"
        
        # Teste 2: Testar detecção de comandos drift
        drift_commands = [
            "mostrar drift",
            "show drift", 
            "detectar drift",
            "diferenças detectadas",
            "reverse sync",
            "auto heal"
        ]
        
        for command in drift_commands:
            result = processor._detect_drift_commands(command)
            # Se não há drift real, deve retornar uma mensagem informativa
            if result:
                assert isinstance(result, str), f"Resultado deve ser string para: {command}"
                assert len(result) > 0, f"Resultado não pode ser vazio para: {command}"
        
        print("✅ Drift Integration: Todos os testes passaram")
        return True
        
    except Exception as e:
        print(f"❌ Drift Integration: {e}")
        return False

def test_mcp_configuration():
    """Testa configuração do MCP AWS Official"""
    print("⚙️ Testando MCP Configuration...")
    
    try:
        import yaml
        
        # Teste 1: Verificar se configuração foi atualizada
        with open('/home/ial/config/mcp-mesh.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        assert config['version'] == "1.1", "Versão da configuração não atualizada"
        
        # Teste 2: Verificar se MCP AWS Official está configurado
        core_mcps = config['core_mcps']['always_active']
        mcp_aws_official = None
        
        for mcp in core_mcps:
            if mcp['name'] == 'MCP_AWS_OFFICIAL':
                mcp_aws_official = mcp
                break
        
        assert mcp_aws_official is not None, "MCP AWS Official não encontrado na configuração"
        assert mcp_aws_official['priority'] == 0, "MCP AWS Official deveria ter prioridade máxima"
        assert 'command' in mcp_aws_official, "Comando não configurado para MCP AWS Official"
        
        print("✅ MCP Configuration: Todos os testes passaram")
        return True
        
    except Exception as e:
        print(f"❌ MCP Configuration: {e}")
        return False

def test_conversational_cli():
    """Testa CLI conversacional"""
    print("💬 Testando Conversational CLI...")
    
    try:
        # Verificar se função conversacional existe
        import ialctl_integrated
        
        assert hasattr(ialctl_integrated, 'conversational_mode'), "Modo conversacional não implementado"
        
        print("✅ Conversational CLI: Função implementada")
        return True
        
    except Exception as e:
        print(f"❌ Conversational CLI: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 TESTE DAS NOVAS FUNCIONALIDADES CONVERSACIONAIS IAL")
    print("=" * 60)
    
    tests = [
        ("CognitiveEngine Integration", test_cognitive_engine_integration),
        ("Master Engine Preview Mode", test_master_engine_preview_mode),
        ("Drift Integration", test_drift_integration),
        ("MCP Configuration", test_mcp_configuration),
        ("Conversational CLI", test_conversational_cli)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODAS AS FUNCIONALIDADES IMPLEMENTADAS COM SUCESSO!")
        print("\n🚀 O IAL agora é um assistente conversacional estilo Amazon Q com:")
        print("   ✅ Integração MCP AWS Official")
        print("   ✅ Preview Mode com estimativas")
        print("   ✅ Perguntas de esclarecimento")
        print("   ✅ Integração Drift Engine no chat")
        print("   ✅ Memória longa conversacional")
        print("   ✅ CLI conversacional interativo")
        
        print("\n💡 Para usar:")
        print("   • ialctl                    # Modo conversacional")
        print("   • ialctl chat               # Modo conversacional explícito")
        print("   • preview criar web app     # Preview mode")
        print("   • mostrar drift             # Comandos drift no chat")
        
        return 0
    else:
        print(f"⚠️ {total - passed} teste(s) falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
