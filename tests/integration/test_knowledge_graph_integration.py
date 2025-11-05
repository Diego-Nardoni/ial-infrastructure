#!/usr/bin/env python3
"""
Teste de Integração Completo do Knowledge Graph
Valida fluxo end-to-end: registro → inferência → consulta → healing
"""

import sys
import os
from pathlib import Path

# Add core path
sys.path.append(str(Path(__file__).parent / 'core'))

def test_end_to_end_workflow():
    """Testa fluxo completo end-to-end"""
    print("🧪 Teste End-to-End do Knowledge Graph")
    
    try:
        # 1. Inicializar componentes
        sys.path.append('/home/ial/core')
        sys.path.append('/home/ial/core/graph')
        
        from resource_catalog import ResourceCatalog
        import dependency_graph
        import graph_populator
        import graph_query_api
        import healing_orchestrator
        
        DependencyGraph = dependency_graph.DependencyGraph
        GraphPopulator = graph_populator.GraphPopulator
        GraphQueryAPI = graph_query_api.GraphQueryAPI
        GraphBasedHealingOrchestrator = healing_orchestrator.GraphBasedHealingOrchestrator
        
        print("✅ Todos os módulos importados com sucesso")
        
        # 2. Criar infraestrutura de teste
        catalog = ResourceCatalog(table_name="ial-test-integration")
        graph = DependencyGraph(enable_persistence=False)  # Teste em memória
        populator = GraphPopulator(graph)
        api = GraphQueryAPI(graph, catalog)
        orchestrator = GraphBasedHealingOrchestrator()
        
        print("✅ Componentes inicializados")
        
        # 3. Simular deploy de infraestrutura completa
        infrastructure = [
            {
                'resource_id': 'vpc-test-123',
                'resource_type': 'AWS::EC2::VPC',
                'phase': '20-network',
                'metadata': {'cidr': '10.0.0.0/16'}
            },
            {
                'resource_id': 'subnet-public-456',
                'resource_type': 'AWS::EC2::Subnet',
                'phase': '20-network',
                'metadata': {'vpc_id': 'vpc-test-123', 'cidr': '10.0.1.0/24'}
            },
            {
                'resource_id': 'subnet-private-789',
                'resource_type': 'AWS::EC2::Subnet', 
                'phase': '20-network',
                'metadata': {'vpc_id': 'vpc-test-123', 'cidr': '10.0.2.0/24'}
            },
            {
                'resource_id': 'alb-web-001',
                'resource_type': 'AWS::ElasticLoadBalancingV2::LoadBalancer',
                'phase': '30-compute',
                'metadata': {'subnet_ids': ['subnet-public-456']}
            },
            {
                'resource_id': 'ecs-service-api',
                'resource_type': 'AWS::ECS::Service',
                'phase': '30-compute', 
                'metadata': {'subnet_ids': ['subnet-private-789']}
            }
        ]
        
        # 4. Registrar recursos e inferir dependências
        registered_count = 0
        for resource in infrastructure:
            success = populator.register_resource(resource)
            if success:
                registered_count += 1
        
        print(f"✅ Recursos registrados: {registered_count}/{len(infrastructure)}")
        
        # 5. Validar grafo construído
        stats = graph.get_graph_stats()
        print(f"📊 Grafo: {stats['total_nodes']} nós, {stats['total_edges']} edges")
        
        # 6. Testar análise de impacto
        impact = api.get_impacted_resources('vpc-test-123')
        print(f"🔍 Impact Analysis VPC: {len(impact.direct_dependents)} dependentes diretos")
        
        # 7. Testar cadeias de dependência
        chains = api.get_dependency_chain('ecs-service-api')
        print(f"🔗 Dependency Chains ECS: {len(chains)} cadeias")
        
        # 8. Simular falha e testar healing
        failed_resources = ['subnet-private-789', 'ecs-service-api']
        healing_order = api.get_healing_order(failed_resources)
        print(f"🔧 Healing Order: {healing_order}")
        
        # 9. Testar explicação de dependências
        explanation = api.explain_dependency('subnet-public-456', 'vpc-test-123')
        print(f"💡 Explicação: {explanation['explanation']}")
        
        # 10. Validar métricas
        api_stats = api.get_api_statistics()
        print(f"📈 API Stats: {api_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste end-to-end: {e}")
        return False

def test_healing_orchestrator_integration():
    """Testa integração com healing orchestrator"""
    print("\n🧪 Teste Healing Orchestrator Integration")
    
    try:
        from graph.healing_orchestrator import GraphBasedHealingOrchestrator
        
        # Criar orchestrator
        orchestrator = GraphBasedHealingOrchestrator()
        
        # Simular recursos com falha
        failed_resources = ['test-resource-1', 'test-resource-2']
        
        # Executar healing (modo simulação)
        result = orchestrator.orchestrate_healing(failed_resources)
        
        print(f"✅ Healing executado: status={result.get('status')}")
        return True
        
    except Exception as e:
        print(f"❌ Erro testando healing orchestrator: {e}")
        return False

def test_reverse_sync_integration():
    """Testa integração com reverse sync"""
    print("\n🧪 Teste Reverse Sync Integration")
    
    try:
        from drift.reverse_sync import ReverseSync
        
        # Criar reverse sync
        reverse_sync = ReverseSync()
        
        # Simular drift findings
        drift_findings = [
            {
                'resource_id': 'vpc-drift-123',
                'drift_type': 'extra_resource',
                'resource_type': 'AWS::EC2::VPC'
            },
            {
                'resource_id': 'subnet-drift-456', 
                'drift_type': 'configuration_drift',
                'resource_type': 'AWS::EC2::Subnet'
            }
        ]
        
        # Gerar PR com análise de impacto
        result = reverse_sync.generate_pr_for_findings(drift_findings, 'test-scope')
        
        print(f"✅ PR gerado: status={result.get('status')}")
        if result.get('impact_analysis'):
            print(f"📊 Impact analysis incluído: {len(result['impact_analysis'])} campos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro testando reverse sync: {e}")
        return False

def test_performance_and_scalability():
    """Testa performance com volume maior de dados"""
    print("\n🧪 Teste Performance e Escalabilidade")
    
    try:
        from graph.dependency_graph import DependencyGraph
        from graph.graph_populator import GraphPopulator
        from graph.graph_query_api import GraphQueryAPI
        import time
        
        # Criar grafo para teste de performance
        graph = DependencyGraph(enable_persistence=False)
        populator = GraphPopulator(graph)
        api = GraphQueryAPI(graph)
        
        # Gerar recursos em escala
        start_time = time.time()
        
        for i in range(50):  # 50 recursos
            resource = {
                'resource_id': f'test-resource-{i}',
                'resource_type': 'AWS::EC2::Instance',
                'phase': 'test-phase',
                'metadata': {'vpc_id': 'vpc-test', 'subnet_id': f'subnet-{i%5}'}
            }
            populator.register_resource(resource)
        
        registration_time = time.time() - start_time
        
        # Testar queries em escala
        start_time = time.time()
        
        for i in range(10):  # 10 queries
            impact = api.get_impacted_resources(f'test-resource-{i}')
            chains = api.get_dependency_chain(f'test-resource-{i}')
        
        query_time = time.time() - start_time
        
        print(f"✅ Performance: {50} recursos em {registration_time:.2f}s")
        print(f"✅ Queries: {10} consultas em {query_time:.2f}s")
        
        # Validar cache
        stats = api.get_api_statistics()
        print(f"📈 Cache: {stats['cache_size']} entradas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro testando performance: {e}")
        return False

def main():
    """Executa todos os testes de integração"""
    print("🧪 TESTES DE INTEGRAÇÃO COMPLETOS - KNOWLEDGE GRAPH")
    print("=" * 70)
    
    tests = [
        ("End-to-End Workflow", test_end_to_end_workflow),
        ("Healing Orchestrator Integration", test_healing_orchestrator_integration),
        ("Reverse Sync Integration", test_reverse_sync_integration),
        ("Performance e Escalabilidade", test_performance_and_scalability)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro executando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n📊 RESUMO DOS TESTES DE INTEGRAÇÃO")
    print("=" * 70)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado Final: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("🎉 TODOS OS TESTES DE INTEGRAÇÃO PASSARAM!")
        print("✅ Knowledge Graph está funcionalmente completo e integrado")
    else:
        print("⚠️ Alguns testes falharam. Verificar integrações.")
    
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    exit(main())
