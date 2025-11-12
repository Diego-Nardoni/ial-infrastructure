#!/usr/bin/env python3
"""
Cost Analysis Script - Via MCP AWS Cost Explorer + Pricing
"""

import os
import sys
import json
from pathlib import Path

def analyze_costs_via_mcp(phases_dir):
    """Analisa custos via MCP Cost Explorer + Pricing"""
    
    cost_output = []
    cost_output.append("💰 Cost Analysis via MCP Cost Explorer")
    cost_output.append("=" * 40)
    
    try:
        # Usar MCP Cost Explorer + Pricing
        sys.path.append('/home/ial')
        from core.mcp_orchestrator import MCPOrchestrator
        
        mcp = MCPOrchestrator()
        
        # Executar análise de custo via MCP
        cost_result = mcp.execute_cost_analysis(phases_dir)
        
        if cost_result and cost_result.get('success'):
            cost_output.append("✅ MCP Cost Explorer + Pricing ativo")
            
            # Extrair dados de custo
            estimated_cost = cost_result.get('estimated_monthly_cost', 0)
            cost_breakdown = cost_result.get('cost_breakdown', {})
            
            cost_output.append(f"💵 Custo Mensal Estimado: ~${estimated_cost:.2f}")
            
            if cost_breakdown:
                cost_output.append("📊 Breakdown por Serviço:")
                for service, cost in cost_breakdown.items():
                    cost_output.append(f"  • {service}: ${cost:.2f}/mês")
            
            # Análise de budget
            if estimated_cost > 200:
                cost_output.append("⚠️ HIGH COST: Considere otimização")
            elif estimated_cost > 100:
                cost_output.append("⚠️ MEDIUM COST: Monitore uso")
            else:
                cost_output.append("✅ LOW COST: Dentro do orçamento")
                
            # Recomendações de otimização via MCP
            optimizations = cost_result.get('optimization_recommendations', [])
            if optimizations:
                cost_output.append("💡 Otimizações Sugeridas:")
                for opt in optimizations[:3]:
                    cost_output.append(f"  • {opt}")
        else:
            raise Exception("MCP Cost Explorer não retornou dados válidos")
            
    except Exception as e:
        cost_output.append(f"⚠️ MCP Cost Explorer erro: {str(e)[:50]}")
        cost_output.append("🔄 Usando estimativa básica como fallback...")
        
        # Fallback básico
        phases_path = Path(phases_dir)
        if phases_path.exists():
            yaml_count = len(list(phases_path.rglob("*.yaml")))
            estimated_cost = yaml_count * 15.0  # $15 por arquivo YAML (estimativa)
            
            cost_output.append(f"📁 {yaml_count} arquivos YAML encontrados")
            cost_output.append(f"💵 Estimativa básica: ~${estimated_cost:.2f}/mês")
            cost_output.append("✅ Estimativa conservadora aplicada")
        else:
            cost_output.append("❌ Diretório phases não encontrado")
    
    return cost_output

def main():
    if len(sys.argv) < 2:
        print("Usage: python cost_analysis.py <phases_directory>")
        sys.exit(1)
    
    phases_dir = sys.argv[1]
    cost_results = analyze_costs_via_mcp(phases_dir)
    
    with open('cost_output.txt', 'w') as f:
        f.write('\n'.join(cost_results))
    
    for line in cost_results:
        print(line)

if __name__ == "__main__":
    main()
