#!/usr/bin/env python3
"""
Teste completo do Intelligent MCP Router Sophisticated
"""

import sys
import asyncio
import json
sys.path.append('/home/ial')

async def test_sophisticated_router_basic():
    """Testa inicialização do router sophisticated"""
    try:
        from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
        
        router = IntelligentMCPRouterSophisticated()
        print("✅ Router sophisticated inicializado")
        
        # Test health check
        health = await router.health_check()
        print(f"✅ Health check: {health['overall_status']}")
        
        await router.cleanup()
        return True
    except Exception as e:
        print(f"❌ Router sophisticated falhou: {e}")
        return False

async def test_end_to_end_async():
    """Testa fluxo completo end-to-end async"""
    try:
        from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
        
        router = IntelligentMCPRouterSophisticated()
        
        # Test request
        request = "Create ECS cluster with RDS database and Application Load Balancer"
        
        # Execute async routing
        result = await router.route_request_async(request)
        
        print(f"✅ Status: {result['status']}")
        print(f"✅ LLM Provider: {result['llm_result']['provider']}")
        print(f"✅ Detected Pattern: {result['detection_result']['pattern']}")
        print(f"✅ Domains: {result['detection_result']['domains']}")
        print(f"✅ MCPs Loaded: {len(result['mapping_result']['loaded_mcps'])}")
        print(f"✅ Total Time: {result['performance_metrics']['total_time']}ms")
        
        # Performance validation
        total_time = result['performance_metrics']['total_time']
        if total_time < 1000:  # < 1 second
            print(f"✅ Performance target met: {total_time}ms < 1000ms")
        else:
            print(f"⚠️ Performance target missed: {total_time}ms > 1000ms")
            
        await router.cleanup()
        return result['status'] == 'success'
    except Exception as e:
        print(f"❌ End-to-end async falhou: {e}")
        return False

async def test_sync_compatibility():
    """Testa compatibilidade com interface sync"""
    try:
        from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
        
        router = IntelligentMCPRouterSophisticated()
        
        # Test sync wrapper
        request = "Deploy serverless Lambda function with DynamoDB"
        result = router.route_request(request)  # Sync method
        
        print(f"✅ Sync wrapper funcionando")
        print(f"✅ Status: {result['status']}")
        
        if 'performance_metrics' in result:
            print(f"✅ Sync time: {result['performance_metrics']['total_time']}ms")
            
        await router.cleanup()
        return result['status'] in ['success', 'fallback']
    except Exception as e:
        print(f"❌ Sync compatibility falhou: {e}")
        return False

async def test_circuit_breaker_behavior():
    """Testa comportamento dos circuit breakers"""
    try:
        from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
        
        router = IntelligentMCPRouterSophisticated()
        
        # Execute request to get circuit breaker metrics
        result = await router.route_request_async("Test circuit breakers")
        
        if 'circuit_breaker_metrics' in result:
            cb_metrics = result['circuit_breaker_metrics']
            print(f"✅ Circuit breakers ativos:")
            print(f"  - Routing: {cb_metrics['routing_circuit']['state']}")
            print(f"  - LLM circuits: {len(cb_metrics['llm_circuits'])}")
            print(f"  - MCP circuits: {len(cb_metrics['mcp_circuits'])}")
            
        await router.cleanup()
        return True
    except Exception as e:
        print(f"❌ Circuit breaker test falhou: {e}")
        return False

async def test_performance_scenarios():
    """Testa diferentes cenários de performance"""
    scenarios = [
        ("Simple EC2", "Launch EC2 instance"),
        ("3-tier App", "Create web application with EC2, RDS and load balancer"),
        ("Serverless", "Deploy Lambda function with API Gateway and DynamoDB"),
        ("Microservices", "Setup ECS cluster with multiple services and monitoring"),
        ("Data Pipeline", "Create data pipeline with S3, Glue and Athena")
    ]
    
    try:
        from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
        
        router = IntelligentMCPRouterSophisticated()
        
        performance_results = []
        
        for scenario_name, request in scenarios:
            result = await router.route_request_async(request)
            
            if result['status'] == 'success':
                perf = result['performance_metrics']
                performance_results.append({
                    'scenario': scenario_name,
                    'total_time': perf['total_time'],
                    'pattern': result['detection_result']['pattern'],
                    'mcps_loaded': len(result['mapping_result']['loaded_mcps'])
                })
                
        print("✅ Performance Results:")
        for perf in performance_results:
            print(f"  {perf['scenario']}: {perf['total_time']}ms ({perf['pattern']}, {perf['mcps_loaded']} MCPs)")
            
        # Calculate average
        avg_time = sum(p['total_time'] for p in performance_results) / len(performance_results)
        print(f"✅ Average time: {avg_time:.2f}ms")
        
        await router.cleanup()
        return len(performance_results) == len(scenarios)
    except Exception as e:
        print(f"❌ Performance scenarios falharam: {e}")
        return False

async def main():
    print("🧪 TESTANDO INTELLIGENT MCP ROUTER SOPHISTICATED COMPLETO...")
    print("=" * 60)
    
    tests = [
        ("Basic Initialization", test_sophisticated_router_basic),
        ("End-to-End Async", test_end_to_end_async),
        ("Sync Compatibility", test_sync_compatibility),
        ("Circuit Breakers", test_circuit_breaker_behavior),
        ("Performance Scenarios", test_performance_scenarios)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}:")
        if await test_func():
            passed += 1
            print(f"✅ {test_name} PASSOU")
        else:
            print(f"❌ {test_name} FALHOU")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADO FINAL: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("🎉 INTELLIGENT MCP ROUTER SOPHISTICATED TOTALMENTE FUNCIONAL!")
        print("✅ Pronto para integração no sistema principal")
    else:
        print("❌ Alguns testes falharam - revisar implementação")

if __name__ == "__main__":
    asyncio.run(main())
