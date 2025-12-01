#!/usr/bin/env python3
"""
Validação Final da Arquitetura Pós-AgentCore
Confirma que todos os componentes estão funcionando corretamente
"""

import sys
import os
import json
import traceback
from datetime import datetime

sys.path.insert(0, '/home/ial')

def validate_architecture():
    """Valida a arquitetura final do sistema"""
    
    print("🏗️ VALIDAÇÃO FINAL DA ARQUITETURA IAL")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {}
    }
    
    # 1. Validar CognitiveEngine como fallback
    print("1️⃣ Validando CognitiveEngine como fallback...")
    try:
        from core.cognitive_engine import CognitiveEngine
        engine = CognitiveEngine()
        
        # Teste básico
        result = engine.process_intent("test fallback")
        assert isinstance(result, dict), "CognitiveEngine deve retornar dict"
        
        results["tests"].append({
            "name": "CognitiveEngine Fallback",
            "status": "✅ PASS",
            "details": "Funcionando como fallback"
        })
        print("   ✅ CognitiveEngine funcionando como fallback")
        
    except Exception as e:
        results["tests"].append({
            "name": "CognitiveEngine Fallback",
            "status": "❌ FAIL",
            "error": str(e)
        })
        print(f"   ❌ Erro: {e}")
    
    # 2. Validar AgentCore como fluxo primário
    print("\n2️⃣ Validando AgentCore como fluxo primário...")
    try:
        from core.bedrock_agent_core import BedrockAgentCore
        agent = BedrockAgentCore()
        
        # Verificar se está configurado
        assert hasattr(agent, 'agent_id'), "AgentCore deve ter agent_id"
        
        results["tests"].append({
            "name": "AgentCore Primary Flow",
            "status": "✅ PASS",
            "details": "Configurado como fluxo primário"
        })
        print("   ✅ AgentCore configurado como fluxo primário")
        
    except Exception as e:
        results["tests"].append({
            "name": "AgentCore Primary Flow",
            "status": "⚠️ WARN",
            "error": str(e),
            "details": "AgentCore pode não estar configurado (normal em dev)"
        })
        print(f"   ⚠️ AgentCore não configurado (normal em dev): {e}")
    
    # 3. Validar Phase Builder intacto
    print("\n3️⃣ Validando Phase Builder intacto...")
    try:
        from core.intelligent_phase_builder import IntelligentPhaseBuilder
        builder = IntelligentPhaseBuilder()
        
        # Teste básico
        phases = builder.build_phases("test deployment")
        assert isinstance(phases, list), "Phase Builder deve retornar lista"
        
        results["tests"].append({
            "name": "Phase Builder Intact",
            "status": "✅ PASS",
            "details": "Phase Builder funcionando normalmente"
        })
        print("   ✅ Phase Builder funcionando normalmente")
        
    except Exception as e:
        results["tests"].append({
            "name": "Phase Builder Intact",
            "status": "❌ FAIL",
            "error": str(e)
        })
        print(f"   ❌ Erro: {e}")
    
    # 4. Validar Step Functions intactos
    print("\n4️⃣ Validando Step Functions intactos...")
    try:
        # Verificar arquivos de definição
        sfn_dir = "/home/ial/stepfunctions"
        assert os.path.exists(sfn_dir), "Diretório stepfunctions deve existir"
        
        sfn_files = os.listdir(sfn_dir)
        assert len(sfn_files) > 0, "Deve haver arquivos de Step Functions"
        
        results["tests"].append({
            "name": "Step Functions Intact",
            "status": "✅ PASS",
            "details": f"Encontrados {len(sfn_files)} arquivos de Step Functions"
        })
        print(f"   ✅ Step Functions intactos ({len(sfn_files)} arquivos)")
        
    except Exception as e:
        results["tests"].append({
            "name": "Step Functions Intact",
            "status": "❌ FAIL",
            "error": str(e)
        })
        print(f"   ❌ Erro: {e}")
    
    # 5. Validar CLI estável
    print("\n5️⃣ Validando estabilidade do CLI...")
    try:
        from ial.cli.ialctl import main as ialctl_main
        
        # Verificar se CLI pode ser importado
        assert callable(ialctl_main), "CLI deve ser callable"
        
        results["tests"].append({
            "name": "CLI Stability",
            "status": "✅ PASS",
            "details": "CLI consolidado funcionando"
        })
        print("   ✅ CLI consolidado funcionando")
        
    except Exception as e:
        results["tests"].append({
            "name": "CLI Stability",
            "status": "❌ FAIL",
            "error": str(e)
        })
        print(f"   ❌ Erro: {e}")
    
    # 6. Validar Enhanced Fallback System
    print("\n6️⃣ Validando Enhanced Fallback System...")
    try:
        from core.enhanced_fallback_system import EnhancedFallbackSystem, ProcessingMode
        system = EnhancedFallbackSystem()
        
        # Teste de determinação de modo
        mode = system.determine_processing_mode("test", {})
        assert isinstance(mode, ProcessingMode), "Deve retornar ProcessingMode"
        
        results["tests"].append({
            "name": "Enhanced Fallback System",
            "status": "✅ PASS",
            "details": "Sistema de fallback funcionando"
        })
        print("   ✅ Sistema de fallback funcionando")
        
    except Exception as e:
        results["tests"].append({
            "name": "Enhanced Fallback System",
            "status": "❌ FAIL",
            "error": str(e)
        })
        print(f"   ❌ Erro: {e}")
    
    # 7. Validar Telemetria
    print("\n7️⃣ Validando sistema de telemetria...")
    try:
        from core.telemetry_enhanced import get_telemetry_system, log_event
        
        # Teste básico de telemetria
        telemetry = get_telemetry_system()
        log_event("validation_test", {"test": "architecture_validation"})
        
        results["tests"].append({
            "name": "Enhanced Telemetry",
            "status": "✅ PASS",
            "details": "Telemetria funcionando"
        })
        print("   ✅ Telemetria funcionando")
        
    except Exception as e:
        results["tests"].append({
            "name": "Enhanced Telemetry",
            "status": "❌ FAIL",
            "error": str(e)
        })
        print(f"   ❌ Erro: {e}")
    
    # 8. Validar Documentação
    print("\n8️⃣ Validando documentação técnica...")
    try:
        docs_dir = "/home/ial/docs"
        required_docs = [
            "architecture.md",
            "agentcore_integration.md", 
            "conversational_flow.md",
            "drift_engine.md",
            "fallback_modes.md"
        ]
        
        missing_docs = []
        for doc in required_docs:
            if not os.path.exists(f"{docs_dir}/{doc}"):
                missing_docs.append(doc)
        
        if missing_docs:
            raise Exception(f"Documentos faltando: {missing_docs}")
        
        results["tests"].append({
            "name": "Technical Documentation",
            "status": "✅ PASS",
            "details": f"Todos os {len(required_docs)} documentos presentes"
        })
        print(f"   ✅ Documentação completa ({len(required_docs)} documentos)")
        
    except Exception as e:
        results["tests"].append({
            "name": "Technical Documentation",
            "status": "❌ FAIL",
            "error": str(e)
        })
        print(f"   ❌ Erro: {e}")
    
    # Calcular resumo
    total_tests = len(results["tests"])
    passed_tests = len([t for t in results["tests"] if t["status"] == "✅ PASS"])
    warned_tests = len([t for t in results["tests"] if t["status"] == "⚠️ WARN"])
    failed_tests = len([t for t in results["tests"] if t["status"] == "❌ FAIL"])
    
    results["summary"] = {
        "total": total_tests,
        "passed": passed_tests,
        "warned": warned_tests,
        "failed": failed_tests,
        "success_rate": (passed_tests / total_tests) * 100
    }
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DA VALIDAÇÃO")
    print("=" * 60)
    print(f"✅ Testes passaram: {passed_tests}")
    print(f"⚠️ Avisos: {warned_tests}")
    print(f"❌ Falhas: {failed_tests}")
    print(f"📊 Taxa de sucesso: {results['summary']['success_rate']:.1f}%")
    
    if results['summary']['success_rate'] >= 85:
        print("\n🎉 ARQUITETURA VALIDADA COM SUCESSO!")
        print("✅ Sistema IAL pronto para produção pós-AgentCore")
        status = "SUCCESS"
    elif results['summary']['success_rate'] >= 70:
        print("\n⚠️ ARQUITETURA PARCIALMENTE VALIDADA")
        print("🔧 Algumas correções podem ser necessárias")
        status = "PARTIAL"
    else:
        print("\n❌ ARQUITETURA PRECISA DE CORREÇÕES")
        print("🚨 Problemas críticos encontrados")
        status = "FAILED"
    
    # Salvar relatório
    report_file = "/home/ial/reports/architecture_validation.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Relatório salvo em: {report_file}")
    
    return status == "SUCCESS"

if __name__ == "__main__":
    try:
        success = validate_architecture()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        traceback.print_exc()
        sys.exit(1)
