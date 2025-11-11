#!/usr/bin/env python3
"""
Testes de validação do sistema atual v6.27
Para garantir que nada quebre durante a implementação
"""

import sys
import os
sys.path.append('/home/ial')

def test_current_mcp_router():
    """Testa se o MCP Router atual funciona"""
    try:
        from core.intelligent_mcp_router import IntelligentMCPRouter
        router = IntelligentMCPRouter()
        print("✅ IntelligentMCPRouter carrega OK")
        return True
    except Exception as e:
        print(f"❌ IntelligentMCPRouter falhou: {e}")
        return False

def test_current_service_detector():
    """Testa se o Service Detector atual funciona"""
    try:
        from core.service_detector import ServiceDetector
        detector = ServiceDetector()
        result = detector.detect("create ecs cluster")  # Método correto é 'detect'
        print(f"✅ ServiceDetector OK: {result}")
        return True
    except Exception as e:
        print(f"❌ ServiceDetector falhou: {e}")
        return False

def test_current_mcp_registry():
    """Testa se o MCP Registry atual funciona"""
    try:
        from mcp_registry import MCPRegistry
        registry = MCPRegistry()
        servers = list(registry.servers.keys())
        print(f"✅ MCPRegistry OK: {len(servers)} servidores")
        return True
    except Exception as e:
        print(f"❌ MCPRegistry falhou: {e}")
        return False

def test_config_files_exist():
    """Testa se arquivos de configuração existem"""
    configs = [
        "/home/ial/config/llm_providers.yaml",
        "/home/ial/config/mcp-mesh.yaml"
    ]
    
    for config in configs:
        if os.path.exists(config):
            print(f"✅ Config existe: {config}")
        else:
            print(f"❌ Config faltando: {config}")
            return False
    return True

if __name__ == "__main__":
    print("🧪 TESTANDO SISTEMA ATUAL v6.27...")
    
    tests = [
        test_current_mcp_router,
        test_current_service_detector, 
        test_current_mcp_registry,
        test_config_files_exist
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 RESULTADO: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("✅ SISTEMA ATUAL VALIDADO - PRONTO PARA ENHANCEMENT")
    else:
        print("❌ SISTEMA ATUAL COM PROBLEMAS - CORRIGIR ANTES DE CONTINUAR")
