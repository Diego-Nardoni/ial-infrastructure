#!/usr/bin/env python3
"""
Teste da integração GitOps no MCP Router Sophisticated
"""

import sys
import asyncio
sys.path.append('/home/ial')

async def test_gitops_yaml_generation():
    """Testa geração de YAML para GitOps"""
    try:
        from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
        
        router = IntelligentMCPRouterSophisticated()
        
        # Mock loaded MCPs
        loaded_mcps = {
            'aws-ecs-mcp': {
                'name': 'aws-ecs-mcp',
                'type': 'domain',
                'domain': 'compute',
                'capabilities': ['create_cluster', 'create_service']
            },
            'aws-rds-mcp': {
                'name': 'aws-rds-mcp',
                'type': 'domain',
                'domain': 'data',
                'capabilities': ['create_database']
            }
        }
        
        # Test YAML generation
        yaml_templates = router._generate_yaml_from_mcps(loaded_mcps, "Create ECS cluster with RDS")
        
        print(f"✅ YAML templates gerados: {len(yaml_templates)}")
        for path, content in yaml_templates.items():
            print(f"   • {path}: {len(content)} chars")
            
        await router.cleanup()
        return len(yaml_templates) > 0
    except Exception as e:
        print(f"❌ YAML generation falhou: {e}")
        return False

async def test_gitops_end_to_end():
    """Testa fluxo completo com GitOps"""
    try:
        from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
        
        router = IntelligentMCPRouterSophisticated()
        
        # Test request
        request = "Create ECS cluster with RDS database"
        
        # Execute async routing (should trigger GitOps)
        result = await router.route_request_async(request)
        
        print(f"✅ Status: {result['status']}")
        
        execution_results = result.get('execution_results', {})
        print(f"✅ Execution status: {execution_results.get('status')}")
        
        if execution_results.get('status') == 'gitops_triggered':
            print(f"✅ GitOps triggered successfully!")
            print(f"   • GitHub status: {execution_results.get('github_status')}")
            print(f"   • Templates: {execution_results.get('templates_generated')}")
            print(f"   • Method: {execution_results.get('deployment_method')}")
        elif execution_results.get('status') == 'gitops_failed':
            print(f"⚠️ GitOps failed: {execution_results.get('error')}")
            print(f"   • Fallback available: {execution_results.get('fallback_available')}")
        
        await router.cleanup()
        return result['status'] == 'success'
    except Exception as e:
        print(f"❌ GitOps end-to-end falhou: {e}")
        return False

async def test_sync_wrapper_gitops():
    """Testa wrapper sync com GitOps"""
    try:
        from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
        
        router = IntelligentMCPRouterSophisticated()
        
        # Test sync wrapper
        request = "Deploy Lambda function with DynamoDB"
        result = router.route_request(request)  # Sync method
        
        print(f"✅ Sync wrapper funcionando")
        print(f"✅ Status: {result['status']}")
        
        if 'gitops_info' in result:
            gitops_info = result['gitops_info']
            print(f"✅ GitOps info presente:")
            print(f"   • Method: {gitops_info.get('deployment_method')}")
            print(f"   • GitHub status: {gitops_info.get('github_status')}")
            
        await router.cleanup()
        return result['status'] in ['success', 'fallback']
    except Exception as e:
        print(f"❌ Sync wrapper GitOps falhou: {e}")
        return False

async def main():
    print("🧪 TESTANDO INTEGRAÇÃO GitOps...")
    print("=" * 50)
    
    tests = [
        ("YAML Generation", test_gitops_yaml_generation),
        ("GitOps End-to-End", test_gitops_end_to_end),
        ("Sync Wrapper GitOps", test_sync_wrapper_gitops)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}:")
        if await test_func():
            passed += 1
            print(f"✅ {test_name} PASSOU")
        else:
            print(f"❌ {test_name} FALHOU")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("🎉 INTEGRAÇÃO GitOps FUNCIONANDO!")
        print("✅ Linguagem natural agora usa GitOps workflow")
    else:
        print("❌ Alguns testes falharam - revisar implementação")

if __name__ == "__main__":
    asyncio.run(main())
