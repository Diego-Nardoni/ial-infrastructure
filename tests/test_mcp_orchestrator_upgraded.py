#!/usr/bin/env python3
"""
Testes para MCPOrchestratorUpgraded
"""

import sys
import asyncio
sys.path.append('/home/ial')

async def test_mcp_orchestrator_basic():
    """Testa carregamento básico do MCPOrchestratorUpgraded"""
    try:
        from core.mcp_mesh_loader import MCPMeshLoader
        from core.mcp_orchestrator_upgraded import MCPOrchestratorUpgraded
        
        mesh_loader = MCPMeshLoader()
        orchestrator = MCPOrchestratorUpgraded(mesh_loader)
        
        print(f"✅ MCPOrchestratorUpgraded inicializado")
        print(f"✅ Cache settings: {orchestrator.cache_settings}")
        print(f"✅ Health settings: {orchestrator.health_settings}")
        
        return True
    except Exception as e:
        print(f"❌ MCPOrchestratorUpgraded falhou: {e}")
        return False

async def test_async_mcp_loading():
    """Testa carregamento async de MCPs"""
    try:
        from core.mcp_mesh_loader import MCPMeshLoader
        from core.mcp_orchestrator_upgraded import MCPOrchestratorUpgraded
        
        mesh_loader = MCPMeshLoader()
        orchestrator = MCPOrchestratorUpgraded(mesh_loader)
        
        # Test MCPs to load
        test_mcps = [
            {
                'name': 'aws-ecs-mcp',
                'priority': 1,
                'load_timeout': 2.0,
                'type': 'domain',
                'capabilities': ['create_cluster', 'create_service']
            },
            {
                'name': 'aws-rds-mcp',
                'priority': 1,
                'load_timeout': 3.0,
                'type': 'domain',
                'capabilities': ['create_database']
            }
        ]
        
        # Load MCPs async
        loaded = await orchestrator.lazy_load_mcps_async(test_mcps)
        
        print(f"✅ MCPs carregados: {list(loaded.keys())}")
        print(f"✅ Total carregados: {len(loaded)}")
        
        # Test metrics
        metrics = orchestrator.get_metrics()
        print(f"✅ Metrics: loaded={metrics['loaded_mcps']}, cached={metrics['cached_mcps']}")
        
        # Cleanup
        await orchestrator.cleanup()
        
        return len(loaded) > 0
    except Exception as e:
        print(f"❌ Async MCP loading falhou: {e}")
        return False

async def test_health_checks():
    """Testa health checks async"""
    try:
        from core.mcp_mesh_loader import MCPMeshLoader
        from core.mcp_orchestrator_upgraded import MCPOrchestratorUpgraded
        
        mesh_loader = MCPMeshLoader()
        orchestrator = MCPOrchestratorUpgraded(mesh_loader)
        
        # Load some MCPs first
        test_mcps = [
            {
                'name': 'test-mcp-1',
                'priority': 1,
                'load_timeout': 1.0,
                'type': 'test'
            }
        ]
        
        loaded = await orchestrator.lazy_load_mcps_async(test_mcps)
        
        if loaded:
            # Run health checks
            await orchestrator.health_check_mcps_async()
            
            print(f"✅ Health checks executados")
            print(f"✅ Health status: {orchestrator.health_status}")
            
        await orchestrator.cleanup()
        return True
    except Exception as e:
        print(f"❌ Health checks falharam: {e}")
        return False

async def main():
    print("🧪 TESTANDO MCPOrchestratorUpgraded...")
    
    tests = [
        test_mcp_orchestrator_basic,
        test_async_mcp_loading,
        test_health_checks
    ]
    
    passed = 0
    for test in tests:
        if await test():
            passed += 1
        print()  # Separator
    
    print(f"📊 RESULTADO: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("✅ MCPOrchestratorUpgraded VALIDADO - FASE 3.4 COMPLETA")
    else:
        print("❌ MCPOrchestratorUpgraded COM PROBLEMAS")

if __name__ == "__main__":
    asyncio.run(main())
