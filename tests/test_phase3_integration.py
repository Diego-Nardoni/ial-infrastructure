#!/usr/bin/env python3
"""
Testes de integração para Fase 3
"""

import sys
sys.path.append('/home/ial')

def test_service_detector_enhanced():
    """Testa ServiceDetectorEnhanced"""
    try:
        from core.mcp_mesh_loader import MCPMeshLoader
        from core.service_detector_enhanced import ServiceDetectorEnhanced
        
        mesh_loader = MCPMeshLoader()
        detector = ServiceDetectorEnhanced(mesh_loader)
        
        # Test service detection
        result = detector.detect_services("Create ECS cluster with RDS database and load balancer")
        
        print(f"✅ Domains detectados: {result['detected_domains']}")
        print(f"✅ Services detectados: {result['detected_services']}")
        print(f"✅ Architecture pattern: {result['architecture_pattern']}")
        print(f"✅ Total confidence: {result['total_confidence']:.2f}")
        
        return len(result['detected_domains']) > 0
    except Exception as e:
        print(f"❌ ServiceDetectorEnhanced falhou: {e}")
        return False

def test_domain_mapper_sophisticated():
    """Testa DomainMapperSophisticated"""
    try:
        from core.mcp_mesh_loader import MCPMeshLoader
        from core.domain_mapper_sophisticated import DomainMapperSophisticated
        
        mesh_loader = MCPMeshLoader()
        mapper = DomainMapperSophisticated(mesh_loader)
        
        # Test domain mapping
        services = ['ecs', 'rds', 'elb']
        domains = mapper.map_to_domains(services)
        
        print(f"✅ Services: {services}")
        print(f"✅ Mapped domains: {domains}")
        
        # Test MCP requirements
        required_mcps = mapper.get_required_mcps(domains)
        print(f"✅ Required MCPs: {len(required_mcps)}")
        
        # Test load strategy
        strategy = mapper.get_load_strategy(required_mcps)
        print(f"✅ Load strategy: {strategy['strategy']}")
        
        return len(domains) > 0 and len(required_mcps) > 0
    except Exception as e:
        print(f"❌ DomainMapperSophisticated falhou: {e}")
        return False

def test_end_to_end_flow():
    """Testa fluxo completo de detecção → mapeamento"""
    try:
        from core.mcp_mesh_loader import MCPMeshLoader
        from core.service_detector_enhanced import ServiceDetectorEnhanced
        from core.domain_mapper_sophisticated import DomainMapperSophisticated
        
        # Initialize components
        mesh_loader = MCPMeshLoader()
        detector = ServiceDetectorEnhanced(mesh_loader)
        mapper = DomainMapperSophisticated(mesh_loader)
        
        # Test input
        user_request = "Deploy serverless application with Lambda, API Gateway and DynamoDB"
        
        # Step 1: Detect services
        detection_result = detector.detect_services(user_request)
        
        # Step 2: Map to domains
        domains = mapper.map_to_domains(detection_result['detected_services'])
        
        # Step 3: Get required MCPs
        required_mcps = mapper.get_required_mcps(domains)
        
        # Step 4: Apply optimizations
        pattern = detection_result['architecture_pattern']
        if pattern:
            optimized_mcps = mapper.apply_optimizations(pattern, required_mcps)
        else:
            optimized_mcps = required_mcps
            
        print(f"✅ Input: {user_request}")
        print(f"✅ Detected pattern: {pattern}")
        print(f"✅ Domains: {domains}")
        print(f"✅ MCPs needed: {len(optimized_mcps)}")
        print(f"✅ Top priority MCPs: {[mcp['name'] for mcp in optimized_mcps[:3]]}")
        
        return len(optimized_mcps) > 0
    except Exception as e:
        print(f"❌ End-to-end flow falhou: {e}")
        return False

def main():
    print("🧪 TESTANDO FASE 3 INTEGRATION...")
    
    tests = [
        test_service_detector_enhanced,
        test_domain_mapper_sophisticated,
        test_end_to_end_flow
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()  # Separator
    
    print(f"📊 RESULTADO: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("✅ FASE 3 INTEGRATION VALIDADA - MCP MESH FUNCIONANDO")
    else:
        print("❌ FASE 3 COM PROBLEMAS")

if __name__ == "__main__":
    main()
