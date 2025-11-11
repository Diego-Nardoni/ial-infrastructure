#!/usr/bin/env python3
"""
State Integrator - Integração com Sistema IAL Existente
Conecta Desired State Builder e Resource Catalog com componentes existentes
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add paths for existing components
sys.path.append(str(Path(__file__).parent.parent / 'scripts'))
sys.path.append(str(Path(__file__).parent.parent / 'lib'))

from desired_state import DesiredStateBuilder
from resource_catalog import ResourceCatalog

# Import existing components
try:
    from phase_manager import PhaseManager
    PHASE_MANAGER_AVAILABLE = True
except ImportError:
    PHASE_MANAGER_AVAILABLE = False

try:
    from validate_completeness import CompletenessValidator
    COMPLETENESS_VALIDATOR_AVAILABLE = True
except ImportError:
    COMPLETENESS_VALIDATOR_AVAILABLE = False

try:
    from reconcile import ReconcileEngine
    RECONCILE_ENGINE_AVAILABLE = True
except ImportError:
    RECONCILE_ENGINE_AVAILABLE = False

class StateIntegrator:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        
        # Initialize new components
        self.desired_state_builder = DesiredStateBuilder()
        self.resource_catalog = ResourceCatalog(region=region)
        
        # Initialize existing components if available
        self.phase_manager = PhaseManager() if PHASE_MANAGER_AVAILABLE else None
        self.completeness_validator = CompletenessValidator() if COMPLETENESS_VALIDATOR_AVAILABLE else None
        self.reconcile_engine = ReconcileEngine() if RECONCILE_ENGINE_AVAILABLE else None
        
        print(f"  ✅ Desired State Builder: Ativo")
        print(f"  ✅ Resource Catalog: Ativo")
    
    def sync_desired_state_with_phases(self) -> Dict:
        """Sincroniza desired state com phase manager existente"""
        print("🔄 Sincronizando desired state com phase manager...")
        
        # Gerar desired state
        phases = self.desired_state_builder.load_phases()
        desired_spec = self.desired_state_builder.build_desired_spec(phases)
        spec_hash = self.desired_state_builder.save_desired_spec(desired_spec)
        
        # Integrar com phase manager se disponível
        if self.phase_manager:
            try:
                # Atualizar deployment order baseado no desired state
                self._update_deployment_order(desired_spec)
                #print("✅ Deployment order atualizado")
            except Exception as e:
                print(f"⚠️ Erro ao atualizar deployment order: {e}")
        
        # Registrar recursos no catálogo
        registered_count = self._register_resources_from_spec(desired_spec)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'spec_hash': spec_hash,
            'total_resources': len(desired_spec.get('resources', [])),
            'registered_resources': registered_count,
            'phase_manager_updated': PHASE_MANAGER_AVAILABLE,
            'success': True
        }
    
    def _update_deployment_order(self, desired_spec: Dict):
        """Atualiza ordem de deployment baseada no desired state"""
        if not self.phase_manager:
            return
        
        # Extrair fases do desired state
        phases_info = []
        for domain, domain_info in desired_spec.get('domains', {}).items():
            for phase in domain_info.get('phases', []):
                phase_key = f"{domain}/{phase['name']}"
                phases_info.append({
                    'key': phase_key,
                    'domain': domain,
                    'phase': phase['name'],
                    'file_path': phase['file_path']
                })
        
        # Atualizar deployment-order.yaml se necessário
        deployment_order_file = Path("./phases/deployment-order.yaml")
        if deployment_order_file.exists():
            try:
                with open(deployment_order_file, 'r') as f:
                    current_order = yaml.safe_load(f)
                
                # Adicionar novas fases se não existirem
                current_phases = set(current_order.get('execution_order', []))
                new_phases = [p['key'] for p in phases_info if p['key'] not in current_phases]
                
                if new_phases:
                    current_order['execution_order'].extend(new_phases)
                    current_order['metadata']['total_phases'] = len(current_order['execution_order'])
                    current_order['metadata']['updated_at'] = datetime.utcnow().isoformat()
                    
                    with open(deployment_order_file, 'w') as f:
                        yaml.dump(current_order, f, default_flow_style=False)
                    
                    print(f"📝 Adicionadas {len(new_phases)} novas fases ao deployment order")
                
            except Exception as e:
                print(f"⚠️ Erro ao atualizar deployment order: {e}")
    
    def _register_resources_from_spec(self, desired_spec: Dict) -> int:
        """Registra recursos do desired state no catálogo"""
        resources_to_register = []
        
        for resource in desired_spec.get('resources', []):
            resource_data = {
                'resource_id': resource['id'],
                'resource_type': resource['type'],
                'phase': f"{resource['domain']}/{resource['phase']}",
                'metadata': {
                    'name': resource['name'],
                    'properties': resource.get('properties', {}),
                    'domain': resource['domain'],
                    'phase': resource['phase'],
                    'file_path': resource['file_path'],
                    'depends_on': resource.get('depends_on', []),
                    'desired_spec_hash': desired_spec['metadata']['spec_hash'],
                    'registered_at': datetime.utcnow().isoformat()
                },
                'status': 'desired'
            }
            resources_to_register.append(resource_data)
        
        # Registrar em lote
        if resources_to_register:
            results = self.resource_catalog.batch_register_resources(resources_to_register)
            success_count = sum(1 for success in results.values() if success)
            print(f"📝 Registrados {success_count}/{len(resources_to_register)} recursos no catálogo")
            return success_count
        
        return 0
    
    def enhanced_completeness_validation(self) -> Dict:
        """Validação de completude aprimorada usando catálogo"""
        print("🔍 Executando validação de completude aprimorada...")
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'validation_method': 'enhanced_with_catalog',
            'success': False
        }
        
        try:
            # Usar validador existente se disponível
            if self.completeness_validator:
                # Executar validação padrão
                expected_resources = self.completeness_validator.discover_expected_resources()
                actual_resources = {}  # Seria preenchido pela validação real
                
                # Enriquecer com dados do catálogo
                catalog_resources = self.resource_catalog.list_resources()
                catalog_by_id = {r['resource_id']: r for r in catalog_resources}
                
                # Comparar expected vs catalog vs actual
                enhanced_results = []
                for resource_id, resource_info in expected_resources.items():
                    catalog_entry = catalog_by_id.get(resource_id)
                    
                    enhanced_result = {
                        'resource_id': resource_id,
                        'expected': resource_info,
                        'in_catalog': catalog_entry is not None,
                        'catalog_status': catalog_entry.get('status') if catalog_entry else None,
                        'catalog_metadata': catalog_entry.get('metadata') if catalog_entry else None
                    }
                    enhanced_results.append(enhanced_result)
                
                result.update({
                    'total_expected': len(expected_resources),
                    'total_in_catalog': len([r for r in enhanced_results if r['in_catalog']]),
                    'enhanced_results': enhanced_results,
                    'success': True
                })
                
            else:
                # Validação básica usando apenas catálogo
                catalog_resources = self.resource_catalog.list_resources()
                desired_resources = self.resource_catalog.list_resources(status='desired')
                actual_resources = self.resource_catalog.list_resources(status='deployed')
                
                result.update({
                    'total_resources': len(catalog_resources),
                    'desired_resources': len(desired_resources),
                    'deployed_resources': len(actual_resources),
                    'completeness_percentage': (len(actual_resources) / len(desired_resources) * 100) if desired_resources else 0,
                    'success': True
                })
        
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Erro na validação de completude: {e}")
        
        return result
    
    def enhanced_reconciliation(self) -> Dict:
        """Reconciliação aprimorada usando catálogo de estado"""
        print("🔄 Executando reconciliação aprimorada...")
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'reconciliation_method': 'enhanced_with_catalog',
            'success': False
        }
        
        try:
            # Recuperar recursos do catálogo
            desired_resources = self.resource_catalog.list_resources(status='desired')
            deployed_resources = self.resource_catalog.list_resources(status='deployed')
            
            # Criar mapas para comparação
            desired_by_id = {r['resource_id']: r for r in desired_resources}
            deployed_by_id = {r['resource_id']: r for r in deployed_resources}
            
            # Análise de drift
            drift_analysis = []
            
            for resource_id, desired in desired_by_id.items():
                deployed = deployed_by_id.get(resource_id)
                
                if not deployed:
                    # Recurso desejado mas não deployado
                    drift_analysis.append({
                        'resource_id': resource_id,
                        'drift_type': 'missing',
                        'action': 'deploy',
                        'confidence': 1.0,
                        'reasoning': 'Recurso definido no desired state mas não encontrado no ambiente'
                    })
                else:
                    # Comparar metadados para detectar drift
                    if desired.get('metadata_hash') != deployed.get('metadata_hash'):
                        drift_analysis.append({
                            'resource_id': resource_id,
                            'drift_type': 'configuration_drift',
                            'action': 'update',
                            'confidence': 0.8,
                            'reasoning': 'Configuração do recurso difere do desired state'
                        })
            
            # Recursos órfãos (deployados mas não no desired state)
            for resource_id, deployed in deployed_by_id.items():
                if resource_id not in desired_by_id:
                    drift_analysis.append({
                        'resource_id': resource_id,
                        'drift_type': 'orphaned',
                        'action': 'review',
                        'confidence': 0.6,
                        'reasoning': 'Recurso deployado mas não definido no desired state atual'
                    })
            
            # Usar reconcile engine existente se disponível
            if self.reconcile_engine and hasattr(self.reconcile_engine, 'post_pr_comment'):
                try:
                    # Formatar para o formato esperado pelo reconcile engine
                    reconcile_results = []
                    for analysis in drift_analysis:
                        reconcile_results.append({
                            'resource_name': analysis['resource_id'],
                            'action': analysis['action'],
                            'confidence': analysis['confidence'],
                            'reasoning': analysis['reasoning'],
                            'changes': [analysis['drift_type']]
                        })
                    
                    # Postar comentário no PR se configurado
                    comment_result = self.reconcile_engine.post_pr_comment(reconcile_results)
                    result['pr_comment_posted'] = comment_result
                    
                except Exception as e:
                    print(f"⚠️ Erro ao postar comentário no PR: {e}")
            
            result.update({
                'total_drift_items': len(drift_analysis),
                'drift_analysis': drift_analysis,
                'summary': {
                    'missing_resources': len([d for d in drift_analysis if d['drift_type'] == 'missing']),
                    'configuration_drifts': len([d for d in drift_analysis if d['drift_type'] == 'configuration_drift']),
                    'orphaned_resources': len([d for d in drift_analysis if d['drift_type'] == 'orphaned'])
                },
                'success': True
            })
            
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Erro na reconciliação: {e}")
        
        return result
    
    def generate_comprehensive_report(self) -> Dict:
        """Gera relatório abrangente do estado do sistema"""
        #print("📊 Gerando relatório abrangente...")
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'report_version': '3.1',
            'components': {}
        }
        
        try:
            # Estatísticas do catálogo
            catalog_stats = self.resource_catalog.get_catalog_statistics()
            report['components']['resource_catalog'] = catalog_stats
            
            # Estatísticas do desired state
            desired_spec_file = Path("./reports/desired_spec.json")
            if desired_spec_file.exists():
                with open(desired_spec_file, 'r') as f:
                    desired_spec = json.load(f)
                
                report['components']['desired_state'] = {
                    'spec_version': desired_spec.get('metadata', {}).get('version'),
                    'spec_hash': desired_spec.get('metadata', {}).get('spec_hash'),
                    'total_resources': len(desired_spec.get('resources', [])),
                    'total_domains': len(desired_spec.get('domains', {})),
                    'generated_at': desired_spec.get('metadata', {}).get('generated_at')
                }
            
            # Validação de completude
            completeness_result = self.enhanced_completeness_validation()
            report['components']['completeness_validation'] = completeness_result
            
            # Reconciliação
            reconciliation_result = self.enhanced_reconciliation()
            report['components']['reconciliation'] = reconciliation_result
            
            # Resumo geral
            report['summary'] = {
                'total_catalog_resources': catalog_stats.get('total_resources', 0),
                'total_desired_resources': report['components'].get('desired_state', {}).get('total_resources', 0),
                'completeness_percentage': completeness_result.get('completeness_percentage', 0),
                'drift_items': reconciliation_result.get('total_drift_items', 0),
                'system_health': 'healthy' if reconciliation_result.get('total_drift_items', 0) == 0 else 'needs_attention'
            }
            
            # Salvar relatório
            report_file = Path("./reports/comprehensive_state_report.json")
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Relatório salvo em: {report_file}")
            
        except Exception as e:
            report['error'] = str(e)
            print(f"❌ Erro ao gerar relatório: {e}")
        
        return report
    
    def full_sync_workflow(self) -> Dict:
        """Executa workflow completo de sincronização"""
        print("🚀 Executando workflow completo de sincronização...")
        
        workflow_result = {
            'timestamp': datetime.utcnow().isoformat(),
            'workflow_version': '3.1',
            'steps': {},
            'success': False
        }
        
        try:
            # Passo 1: Sincronizar desired state
            print("\n📋 Passo 1: Sincronizando desired state...")
            sync_result = self.sync_desired_state_with_phases()
            workflow_result['steps']['sync_desired_state'] = sync_result
            
            # Passo 2: Validação de completude
            print("\n🔍 Passo 2: Validação de completude...")
            completeness_result = self.enhanced_completeness_validation()
            workflow_result['steps']['completeness_validation'] = completeness_result
            
            # Passo 3: Reconciliação
            print("\n🔄 Passo 3: Reconciliação...")
            reconciliation_result = self.enhanced_reconciliation()
            workflow_result['steps']['reconciliation'] = reconciliation_result
            
            # Passo 4: Relatório abrangente
            print("\n📊 Passo 4: Relatório abrangente...")
            report_result = self.generate_comprehensive_report()
            workflow_result['steps']['comprehensive_report'] = report_result
            
            # Verificar sucesso geral
            all_successful = all(
                step.get('success', False) 
                for step in workflow_result['steps'].values()
            )
            
            workflow_result['success'] = all_successful
            
            if all_successful:
                print("\n✅ Workflow completo executado com sucesso!")
            else:
                print("\n⚠️ Workflow executado com alguns erros. Verifique os logs.")
            
        except Exception as e:
            workflow_result['error'] = str(e)
            print(f"\n❌ Erro no workflow: {e}")
        
        # Salvar resultado do workflow
        workflow_file = Path("./reports/sync_workflow_result.json")
        with open(workflow_file, 'w') as f:
            json.dump(workflow_result, f, indent=2, ensure_ascii=False)
        
        return workflow_result

def main():
    """Função principal para execução standalone"""
    print("🔗 IAL State Integrator v3.1")
    print("=" * 50)
    
    integrator = StateIntegrator()
    
    # Executar workflow completo
    result = integrator.full_sync_workflow()
    
    if result['success']:
        print("\n🎉 Integração completa executada com sucesso!")
        return 0
    else:
        print("\n❌ Integração executada com erros.")
        return 1

if __name__ == "__main__":
    exit(main())
