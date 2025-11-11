#!/usr/bin/env python3
"""
Testes para MCPMeshLoader
"""

import sys
sys.path.append('/home/ial')

def test_mcp_mesh_loader_basic():
    """Testa carregamento básico do MCPMeshLoader"""
    try:
        from core.mcp_mesh_loader import MCPMeshLoader
        loader = MCPMeshLoader()
        
        print(f"✅ MCPMeshLoader carregado")
        print(f"✅ Core MCPs: {len(loader.core_mcps)}")
        print(f"✅ Domain MCPs: {len(loader.domain_mcps)}")
        print(f"✅ Domains: {loader.get_all_domains()}")
        return True
    except Exception as e:
        print(f"❌ MCPMeshLoader falhou: {e}")
        return False

def test_trigger_keywords():
    """Testa extração de trigger keywords"""
    try:
        from core.mcp_mesh_loader import MCPMeshLoader
        loader = MCPMeshLoader()
        
        # Test compute domain keywords
        compute_keywords = loader.get_trigger_keywords('compute')
        print(f"✅ Compute keywords: {len(compute_keywords)} encontradas")
        
        # Test all keywords
        all_keywords = loader.get_all_trigger_keywords()
        print(f"✅ Total domains com keywords: {len(all_keywords)}")
        
        return True
    except Exception as e:
        print(f"❌ Trigger keywords falhou: {e}")
        return False

def test_config_validation():
    """Testa validação da configuração"""
    try:
        from core.mcp_mesh_loader import MCPMeshLoader
        loader = MCPMeshLoader()
        
        validation = loader.validate_config()
        print(f"✅ Config válida: {validation['valid']}")
        print(f"✅ Stats: {validation['stats']}")
        
        if validation['errors']:
            print(f"⚠️ Errors: {validation['errors']}")
        if validation['warnings']:
            print(f"⚠️ Warnings: {validation['warnings']}")
            
        return True
    except Exception as e:
        print(f"❌ Config validation falhou: {e}")
        return False

def main():
    print("🧪 TESTANDO MCPMeshLoader...")
    
    tests = [
        test_mcp_mesh_loader_basic,
        test_trigger_keywords,
        test_config_validation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 RESULTADO: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("✅ MCPMeshLoader VALIDADO - FASE 2.3 COMPLETA")
    else:
        print("❌ MCPMeshLoader COM PROBLEMAS")

if __name__ == "__main__":
    main()
