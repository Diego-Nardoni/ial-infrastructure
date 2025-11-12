#!/usr/bin/env python3
"""
CloudFormation Plan Script - Via MCP AWS CloudFormation
"""

import os
import sys
import json
from pathlib import Path

def analyze_phases_via_mcp(phases_dir):
    """Analisa phases via MCP AWS CloudFormation"""
    
    plan_output = []
    plan_output.append("📋 CloudFormation Plan via MCP")
    plan_output.append("=" * 35)
    
    try:
        # Usar MCP AWS CloudFormation
        sys.path.append('/home/ial')
        from core.mcp_orchestrator import MCPOrchestrator
        
        mcp = MCPOrchestrator()
        
        # Executar análise CloudFormation via MCP
        cf_result = mcp.execute_cloudformation_plan(phases_dir)
        
        if cf_result and cf_result.get('success'):
            plan_output.append("✅ MCP AWS CloudFormation ativo")
            
            # Extrair plano de execução
            change_sets = cf_result.get('change_sets', [])
            if change_sets:
                plan_output.append(f"📊 {len(change_sets)} change sets identificados")
                
                for cs in change_sets[:5]:  # Top 5
                    stack_name = cs.get('stack_name', 'Unknown')
                    changes = cs.get('changes', [])
                    plan_output.append(f"📦 {stack_name}: {len(changes)} mudanças")
                    
                    for change in changes[:3]:  # Top 3 changes
                        action = change.get('action', 'Unknown')
                        resource = change.get('resource_type', 'Unknown')
                        plan_output.append(f"  • {action}: {resource}")
            
            # Validação de templates
            validation_results = cf_result.get('template_validation', {})
            if validation_results:
                valid_templates = validation_results.get('valid_count', 0)
                total_templates = validation_results.get('total_count', 0)
                plan_output.append(f"✅ Templates válidos: {valid_templates}/{total_templates}")
                
                errors = validation_results.get('errors', [])
                if errors:
                    plan_output.append("❌ Erros de validação:")
                    for error in errors[:3]:
                        plan_output.append(f"  • {error}")
            
            # Estimativa de tempo
            estimated_time = cf_result.get('estimated_deployment_time', 0)
            plan_output.append(f"⏱️ Tempo estimado: {estimated_time} minutos")
            
        else:
            raise Exception("MCP CloudFormation não retornou dados válidos")
            
    except Exception as e:
        plan_output.append(f"⚠️ MCP CloudFormation erro: {str(e)[:50]}")
        plan_output.append("🔄 Usando análise básica como fallback...")
        
        # Fallback básico
        phases_path = Path(phases_dir)
        if phases_path.exists():
            yaml_files = list(phases_path.rglob("*.yaml"))
            plan_output.append(f"📁 {len(yaml_files)} arquivos YAML encontrados")
            
            valid_files = 0
            for yaml_file in yaml_files[:10]:
                try:
                    import yaml
                    with open(yaml_file, 'r') as f:
                        content = yaml.safe_load(f)
                    if content and 'Resources' in content:
                        valid_files += 1
                        resources = len(content['Resources'])
                        plan_output.append(f"✅ {yaml_file.name}: {resources} recursos")
                except:
                    plan_output.append(f"❌ {yaml_file.name}: Erro de parsing")
            
            plan_output.append(f"📊 Templates válidos: {valid_files}/{len(yaml_files)}")
            plan_output.append("✅ Análise básica concluída")
        else:
            plan_output.append("❌ Diretório phases não encontrado")
    
    return plan_output

def main():
    if len(sys.argv) < 2:
        print("Usage: python cf_plan.py <phases_directory>")
        sys.exit(1)
    
    phases_dir = sys.argv[1]
    plan_results = analyze_phases_via_mcp(phases_dir)
    
    with open('plan_output.txt', 'w') as f:
        f.write('\n'.join(plan_results))
    
    for line in plan_results:
        print(line)

if __name__ == "__main__":
    main()
