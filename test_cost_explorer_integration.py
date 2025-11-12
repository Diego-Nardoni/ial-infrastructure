#!/usr/bin/env python3
"""Teste de integração AWS Cost Explorer MCP"""

import asyncio
from core.mcp_servers_initializer import MCPServersInitializer

async def test_cost_explorer_integration():
    """Testa se Cost Explorer MCP está configurado"""
    
    print("🧪 Testando integração AWS Cost Explorer MCP\n")
    
    # 1. Inicializar MCP servers
    initializer = MCPServersInitializer()
    results = await initializer.initialize_all_servers()
    
    # 2. Verificar domínio finops
    finops_domain = results["domain_mcps"].get("finops", {})
    
    print(f"📊 Domínio FinOps:")
    print(f"   Descrição: {finops_domain.get('description', 'N/A')}")
    print(f"   Status: {finops_domain.get('status', 'N/A')}")
    print(f"   MCPs registrados: {len(finops_domain.get('mcps', []))}")
    
    # 3. Verificar Cost Explorer MCP
    cost_explorer_registered = 'aws-cost-explorer-mcp' in finops_domain.get('mcps', [])
    
    if cost_explorer_registered:
        print(f"\n✅ AWS Cost Explorer MCP registrado com sucesso!")
        print(f"   Trigger keywords: billing, cost, budget, pricing, expense")
        print(f"   Capabilities: analyze_costs, create_reports, get_recommendations")
    else:
        print(f"\n❌ AWS Cost Explorer MCP NÃO encontrado")
    
    # 4. Resumo
    print(f"\n📈 Resumo da integração:")
    print(f"   Core MCPs: {len(results['core_mcps'])}")
    print(f"   Domain MCPs: {len(results['domain_mcps'])} domínios")
    print(f"   Total inicializados: {results['total_initialized']}")
    print(f"   Total falhas: {results['total_failed']}")
    
    return cost_explorer_registered

if __name__ == "__main__":
    result = asyncio.run(test_cost_explorer_integration())
    exit(0 if result else 1)
