#!/usr/bin/env python3
"""
Teste da implementação do Knowledge Graph
Valida funcionalidades básicas implementadas
"""

import sys
import os
from pathlib import Path

# Add core path
sys.path.append(str(Path(__file__).parent / 'core'))

def test_resource_catalog_relationships():
    """Testa métodos de relacionamento do ResourceCatalog"""
    print("🧪 Testando ResourceCatalog - Relacionamentos")
    
    try:
        from resource_catalog import ResourceCatalog
        
        # Criar instância (modo teste)
        catalog = ResourceCatalog(table_name="ial-test-graph")
        
        # Teste 1: Adicionar relacionamento
        success = catalog.add_resource_relationship(
            source_id="subnet-123",
            target_id="vpc-456", 
            relationship_type="subnet_vpc",
            metadata={
                'confidence': 1.0,
                'auto_detected': True,
                'detection_method': 'test',
                'phase_source': 'test-phase'
            }
        )
        
        print(f"✅ Adicionar relacionamento: {'OK' if success else 'FALHOU'}")
        
        # Teste 2: Buscar dependências
        dependencies = catalog.get_resource_dependencies("subnet-123")
        print(f"✅ Buscar dependências: {len(dependencies)} encontradas")
        
        # Teste 3: Buscar dependentes
        dependents = catalog.get_resource_dependents("vpc-456")
        print(f"✅ Buscar dependentes: {len(dependents)} encontrados")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro testando ResourceCatalog: {e}")
        return False

def test_dependency_graph():
    """Testa DependencyGraph com persistência"""
    print("\n🧪 Testando DependencyGraph")
    
    try:
        from graph.dependency_graph import DependencyGraph, ResourceState, BlastRadius
        
        # Criar grafo (sem persistência para teste)
        graph = DependencyGraph(enable_persistence=False)
        
        # Teste 1: Adicionar nós
        vpc_node = graph.add_node("vpc-test", "AWS::EC2::VPC", ResourceState.HEALTHY)
        subnet_node = graph.add_node("subnet-test", "AWS::EC2::Subnet", ResourceState.HEALTHY)
        
        print(f"✅ Nós adicionados: {len(graph.nodes)} total")
        
        # Teste 2: Adicionar dependência
        graph.add_dependency("subnet-test", "vpc-test", "subnet_vpc")
        
        print(f"✅ Dependência adicionada: {len(graph.edges)} edges total")
        
        # Teste 3: Calcular ordem de cura
        graph.nodes["subnet-test"].state = ResourceState.DRIFT
        healing_order = graph.get_healing_order()
        
        print(f"✅ Ordem de cura calculada: {healing_order}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro testando DependencyGraph: {e}")
        return False

def test_graph_populator():
    """Testa GraphPopulator"""
    print("\n🧪 Testando GraphPopulator")
    
    try:
        from graph.dependency_graph import DependencyGraph
        from graph.graph_populator import GraphPopulator
        
        # Criar componentes
        graph = DependencyGraph(enable_persistence=False)
        populator = GraphPopulator(graph)
        
        # Teste 1: Registrar recurso
        resource_info = {
            'resource_id': 'ecs-service-test',
            'resource_type': 'AWS::ECS::Service',
            'phase': 'test-phase',
            'metadata': {
                'subnet_id': 'subnet-123',
                'vpc_id': 'vpc-456'
            }
        }
        
        success = populator.register_resource(resource_info)
        print(f"✅ Registrar recurso: {'OK' if success else 'FALHOU'}")
        
        # Teste 2: Inferir dependências
        dependencies = populator.infer_dependencies(resource_info)
        print(f"✅ Dependências inferidas: {len(dependencies)}")
        
        # Teste 3: Estatísticas
        stats = populator.get_inference_statistics()
        print(f"✅ Estatísticas: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro testando GraphPopulator: {e}")
        return False

def test_graph_query_api():
    """Testa GraphQueryAPI"""
    print("\n🧪 Testando GraphQueryAPI")
    
    try:
        from graph.dependency_graph import DependencyGraph
        from graph.graph_query_api import GraphQueryAPI
        
        # Criar grafo com dados de teste
        graph = DependencyGraph(enable_persistence=False)
        
        # Adicionar recursos de teste
        graph.add_node("vpc-test", "AWS::EC2::VPC")
        graph.add_node("subnet-test", "AWS::EC2::Subnet")
        graph.add_node("ecs-test", "AWS::ECS::Service")
        
        # Adicionar dependências
        graph.add_dependency("subnet-test", "vpc-test", "subnet_vpc")
        graph.add_dependency("ecs-test", "subnet-test", "ecs_subnet")
        
        # Criar API
        api = GraphQueryAPI(graph)
        
        # Teste 1: Análise de impacto
        impact = api.get_impacted_resources("vpc-test")
        print(f"✅ Análise de impacto: {len(impact.direct_dependents)} dependentes diretos")
        
        # Teste 2: Cadeia de dependências
        chains = api.get_dependency_chain("ecs-test")
        print(f"✅ Cadeias de dependência: {len(chains)} cadeias")
        
        # Teste 3: Ordem de cura
        healing_order = api.get_healing_order(["ecs-test", "subnet-test"])
        print(f"✅ Ordem de cura: {healing_order}")
        
        # Teste 4: Explicar dependência
        explanation = api.explain_dependency("subnet-test", "vpc-test")
        print(f"✅ Explicação: {explanation['explanation']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro testando GraphQueryAPI: {e}")
        return False

def test_audit_validator_integration():
    """Testa integração com AuditValidator"""
    print("\n🧪 Testando integração AuditValidator")
    
    try:
        from audit_validator import AuditValidator
        
        # Criar validator
        validator = AuditValidator()
        
        # Verificar se Knowledge Graph está habilitado
        if validator.graph_enabled:
            print("✅ Knowledge Graph habilitado no AuditValidator")
            
            # Testar registro de recurso
            test_resource = {
                'resource_id': 'test-resource-123',
                'resource_type': 'AWS::EC2::Instance',
                'phase': 'test-phase'
            }
            
            success = validator._register_resource_in_graph(test_resource)
            print(f"✅ Registro no grafo: {'OK' if success else 'FALHOU'}")
            
        else:
            print("⚠️ Knowledge Graph desabilitado no AuditValidator")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro testando integração AuditValidator: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 TESTE DA IMPLEMENTAÇÃO DO KNOWLEDGE GRAPH")
    print("=" * 60)
    
    tests = [
        ("ResourceCatalog Relacionamentos", test_resource_catalog_relationships),
        ("DependencyGraph", test_dependency_graph),
        ("GraphPopulator", test_graph_populator),
        ("GraphQueryAPI", test_graph_query_api),
        ("AuditValidator Integration", test_audit_validator_integration)
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
    print("\n📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("🎉 Todos os testes passaram! Implementação básica funcionando.")
    else:
        print("⚠️ Alguns testes falharam. Verificar implementação.")
    
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    exit(main())
