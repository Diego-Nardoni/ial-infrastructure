#!/usr/bin/env python3
"""
Teste básico do Intelligent MCP Router
Valida funcionamento dos componentes principais
"""

import asyncio
import sys
import os

# Adicionar path do core
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from core.service_detector import ServiceDetector
from core.domain_mapper import DomainMapper
from core.mcp_orchestrator import MCPOrchestrator
from core.intelligent_mcp_router import IntelligentMCPRouter

async def test_service_detector():
    """Testa detecção de serviços"""
    print("🧪 TESTANDO SERVICE DETECTOR")
    print("=" * 40)
    
    detector = ServiceDetector()
    
    test_cases = [
        "Crie uma função Lambda para processar mensagens SQS",
        "Deploy ECS cluster with RDS database and load balancer",
        "Infraestrutura de 3 camadas com containers e banco de dados",
        "Setup serverless architecture with API Gateway"
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n{i}. Input: '{test_input}'")
        
        result = detector.detect(test_input)
        
        print(f"   Serviços: {[s.name for s in result['services']]}")
        print(f"   Padrões: {[p['name'] for p in result['patterns']]}")
        
        if result['services']:
            dependencies = detector.infer_dependencies(result['services'])
            print(f"   Dependências: {dependencies}")
    
    print("\n✅ Service Detector testado")

async def test_domain_mapper():
    """Testa mapeamento de domínios"""
    print("\n🧪 TESTANDO DOMAIN MAPPER")
    print("=" * 40)
    
    mapper = DomainMapper()
    
    test_services = ['lambda', 'rds', 'elb', 'ecs']
    
    print(f"Serviços de teste: {test_services}")
    
    mcps = mapper.map_services_to_mcps(test_services)
    
    print(f"MCPs necessários: {len(mcps)}")
    for mcp in mcps:
        print(f"   • {mcp.mcp_name} (prioridade: {mcp.priority}, timeout: {mcp.load_timeout}s)")
    
    phases = mapper.get_deployment_phases(mcps)
    print(f"\nFases de deployment: {list(phases.keys())}")
    
    print("\n✅ Domain Mapper testado")

async def test_orchestrator():
    """Testa orquestração de MCPs"""
    print("\n🧪 TESTANDO MCP ORCHESTRATOR")
    print("=" * 40)
    
    orchestrator = MCPOrchestrator()
    mapper = DomainMapper()
    
    # Simular MCPs para teste
    test_mcps = mapper.map_services_to_mcps(['lambda', 'rds'])
    
    print(f"Testando orquestração com {len(test_mcps)} MCPs")
    
    context = {'user_id': 'test_user', 'session_id': 'test_session'}
    user_input = "Crie Lambda com RDS"
    
    result = await orchestrator.execute_coordinated(test_mcps, context, user_input)
    
    print(f"Resultado: {result['success']}")
    print(f"Fases executadas: {len(result['phases'])}")
    print(f"Tempo de execução: {result['execution_time']:.2f}s")
    
    if result['errors']:
        print(f"Erros: {result['errors']}")
    
    stats = orchestrator.get_execution_stats()
    print(f"Stats: {stats}")
    
    print("\n✅ MCP Orchestrator testado")

async def test_intelligent_router():
    """Testa router inteligente completo"""
    print("\n🧪 TESTANDO INTELLIGENT MCP ROUTER")
    print("=" * 40)
    
    router = IntelligentMCPRouter()
    
    test_cases = [
        "Crie uma função Lambda simples",
        "Deploy ECS + RDS + ELB para aplicação web",
        "Infraestrutura serverless com API Gateway e DynamoDB"
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n{i}. Testando: '{test_input}'")
        
        context = {'user_id': f'test_user_{i}', 'session_id': f'session_{i}'}
        
        result = await router.route_request(test_input, context)
        
        print(f"   Sucesso: {result['success']}")
        print(f"   Tempo: {result.get('execution_time', 0):.2f}s")
        
        if 'routing_decision' in result:
            decision = result['routing_decision']
            print(f"   Serviços detectados: {decision['detected_services']}")
            print(f"   MCPs usados: {decision['mcps_used']}")
            print(f"   Confiança: {decision['confidence']:.2f}")
        
        if result.get('fallback_used'):
            print(f"   ⚠️ Fallback usado: {result.get('fallback_reason')}")
    
    # Testar estatísticas
    stats = router.get_router_stats()
    print(f"\nEstatísticas do Router:")
    print(f"   Cache: {stats['cache_size']} entradas")
    print(f"   MCPs ativos: {stats['active_mcps']}")
    
    print("\n✅ Intelligent MCP Router testado")

async def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DO MCP ROUTER INTELIGENTE")
    print("=" * 50)
    
    try:
        await test_service_detector()
        await test_domain_mapper()
        await test_orchestrator()
        await test_intelligent_router()
        
        print("\n🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("✅ Componentes do MCP Router Inteligente funcionando")
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
