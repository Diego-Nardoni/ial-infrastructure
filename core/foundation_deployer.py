"""
Foundation Deployer - Deploy automatizado de todas as fases IAL Foundation
"""

import os
from typing import Dict, List, Any
from core.phase_parser import PhaseParser, deploy_phase_resources

class FoundationDeployer:
    def __init__(self, phases_dir: str = "/home/ial/phases"):
        self.phases_dir = phases_dir
        self.parser = PhaseParser(phases_dir)
        
        # Ordem de deployment das fases
        self.phase_order = [
            "00-foundation",
            "10-security", 
            "20-network",
            "30-compute",
            "40-data",
            "50-application",
            "60-observability",
            "70-ai-ml",
            "90-governance"
        ]
    
    def list_all_phases(self) -> List[str]:
        """Lista todas as fases disponíveis"""
        phases = []
        for item in os.listdir(self.phases_dir):
            if os.path.isdir(os.path.join(self.phases_dir, item)) and item.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                phases.append(item)
        return sorted(phases)
    
    def deploy_phase(self, phase: str) -> Dict[str, Any]:
        """Deploy uma fase específica"""
        print(f"\n🚀 Deploying Phase: {phase}")
        
        result = deploy_phase_resources(phase)
        
        # Resumo dos resultados
        successful = result['successful']
        total = result['total_resources']
        
        print(f"   ✅ {successful}/{total} resources deployed successfully")
        
        if result['results']:
            for r in result['results']:
                status = "✅" if r.get('success', False) else "❌"
                name = r.get('name', 'unknown')
                resource_type = r.get('type', 'unknown')
                print(f"   {status} {name} ({resource_type})")
        
        return result
    
    def deploy_all_phases(self) -> Dict[str, Any]:
        """Deploy todas as fases em ordem"""
        print("🎯 Starting IAL Foundation Complete Deployment")
        print("=" * 50)
        
        all_results = {}
        total_successful = 0
        total_resources = 0
        
        available_phases = self.list_all_phases()
        
        for phase in self.phase_order:
            if phase in available_phases:
                try:
                    result = self.deploy_phase(phase)
                    all_results[phase] = result
                    total_successful += result['successful']
                    total_resources += result['total_resources']
                except Exception as e:
                    print(f"   ❌ Phase {phase} failed: {str(e)}")
                    all_results[phase] = {
                        'error': str(e),
                        'successful': 0,
                        'total_resources': 0
                    }
            else:
                print(f"   ⚠️  Phase {phase} not found, skipping")
        
        print("\n" + "=" * 50)
        print(f"🎉 IAL Foundation Deployment Complete!")
        print(f"   📊 Total: {total_successful}/{total_resources} resources deployed")
        print(f"   📋 Phases processed: {len([p for p in all_results if 'error' not in all_results[p]])}")
        
        return {
            'total_successful': total_successful,
            'total_resources': total_resources,
            'phases_results': all_results,
            'deployment_complete': True
        }
    
    def deploy_foundation_core(self) -> Dict[str, Any]:
        """Deploy TODOS os recursos da Foundation (fase 00)"""
        print("🎯 Deploying IAL Foundation Core Resources")
        print("=" * 40)
        
        phase_path = os.path.join(self.phases_dir, '00-foundation')
        
        # Listar TODOS os arquivos YAML (exceto domain-metadata)
        all_files = sorted([
            f for f in os.listdir(phase_path) 
            if f.endswith('.yaml') and not f.startswith('domain-metadata')
        ])
        
        print(f"📦 Found {len(all_files)} templates to deploy\n")
        
        results = []
        successful = 0
        
        for file_name in all_files:
            file_path = os.path.join(phase_path, file_name)
            
            try:
                print(f"🔄 {file_name}...", end=" ")
                result = self.parser.deploy_cloudformation_stack(file_path, "ial-fork")
                
                if result['success']:
                    print("✅")
                    successful += 1
                else:
                    print("⚠️")
                
                results.append({'file': file_name, 'result': result})
                    
            except Exception as e:
                print(f"❌ {str(e)[:50]}")
                results.append({'file': file_name, 'error': str(e)})
        
        print(f"\n🎉 Foundation Core Deployment Complete!")
        print(f"   📊 {successful}/{len(all_files)} templates deployed")
        
        return {
            'core_resources': results,
            'successful_deployments': successful,
            'total_resource_groups': len(all_files)
        }

def deploy_complete_foundation() -> Dict[str, Any]:
    """Função principal para deployment completo"""
    deployer = FoundationDeployer()
    return deployer.deploy_all_phases()

def deploy_foundation_core_only() -> Dict[str, Any]:
    """Função para deployment apenas do core"""
    deployer = FoundationDeployer()
    return deployer.deploy_foundation_core()
