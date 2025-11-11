#!/usr/bin/env python3
"""
Audit Validator - Proof-of-Creation
Compara desired_spec vs CloudFormation vs AWS real para auditoria determinística
"""

import json
import boto3
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from botocore.exceptions import ClientError

# Add core components
sys.path.append(str(Path(__file__).parent))

try:
    from core.resource_catalog import ResourceCatalog
    RESOURCE_CATALOG_AVAILABLE = True
except ImportError:
    try:
        from resource_catalog import ResourceCatalog
        RESOURCE_CATALOG_AVAILABLE = True
    except ImportError:
        # Fallback básico
        class ResourceCatalog:
            def __init__(self):
                self.resources = {}
            def validate_resource(self, resource_id):
                return True
        RESOURCE_CATALOG_AVAILABLE = False
try:
    from .observability_engine import ObservabilityEngine
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
try:
    from .graph.dependency_graph import DependencyGraph
    from .graph.graph_populator import GraphPopulator
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False

class AuditValidator:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        
        # AWS clients
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        
        # IAL components
        if RESOURCE_CATALOG_AVAILABLE:
            try:
                self.resource_catalog = ResourceCatalog(region=region)
            except TypeError:
                # Fallback if ResourceCatalog doesn't accept region parameter
                self.resource_catalog = ResourceCatalog()
        else:
            self.resource_catalog = ResourceCatalog()  # Use fallback class
        
        # Knowledge Graph components
        if GRAPH_AVAILABLE:
            try:
                self.dependency_graph = DependencyGraph(region=region)
                self.graph_populator = GraphPopulator(self.dependency_graph)
                self.graph_enabled = True
            except Exception as e:
                print(f"⚠️ Knowledge Graph desabilitado: {e}")
                self.dependency_graph = None
                self.graph_populator = None
                self.graph_enabled = False
        else:
            self.dependency_graph = None
            self.graph_populator = None
            self.graph_enabled = False
    def validate_completeness_with_enforcement(self, desired_spec_path: str = "reports/desired_spec.json") -> Dict:
        """Validate completeness with enforcement - FAIL if < 100%"""
        
        print("🔍 Running audit validation with enforcement...")
        
        # Run standard validation
        result = self.validate_completeness(desired_spec_path)
        
        completeness = result.get('completeness_percentage', 0)
        
        # Publish CloudWatch metric
        self.publish_completeness_metric(completeness)
        
        # Check enforcement threshold
        if self.enforcement_enabled and completeness < self.completeness_threshold:
            error_msg = f"AUDIT ENFORCEMENT FAILED: Completeness {completeness:.1f}% < {self.completeness_threshold}%"
            print(f"❌ {error_msg}")
            
            # Send alert if configured
            if self.alert_topic_arn:
                self.send_completeness_alert(completeness, error_msg)
            
            # Add enforcement result
            result['enforcement'] = {
                'enabled': True,
                'threshold': self.completeness_threshold,
                'passed': False,
                'error': error_msg
            }
            
            # Raise exception to fail pipeline
            raise Exception(error_msg)
        else:
            print(f"✅ Audit enforcement passed: {completeness:.1f}% >= {self.completeness_threshold}%")
            result['enforcement'] = {
                'enabled': self.enforcement_enabled,
                'threshold': self.completeness_threshold,
                'passed': True
            }
        
        return result
    
    def publish_completeness_metric(self, completeness: float):
        """Publish completeness metric to CloudWatch"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='IAL/Creation',
                MetricData=[
                    {
                        'MetricName': 'Completeness',
                        'Value': completeness,
                        'Unit': 'Percent',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
            print(f"📊 Published completeness metric: {completeness:.1f}%")
        except Exception as e:
            print(f"⚠️ Failed to publish metric: {e}")
    
    def send_completeness_alert(self, completeness: float, error_msg: str):
        """Send SNS alert for completeness failure"""
        try:
            message = {
                'alert_type': 'COMPLETENESS_FAILURE',
                'completeness_percentage': completeness,
                'threshold': self.completeness_threshold,
                'error_message': error_msg,
                'timestamp': datetime.utcnow().isoformat(),
                'region': self.region
            }
            
            self.sns.publish(
                TopicArn=self.alert_topic_arn,
                Subject=f'IAL Audit Enforcement Failed - {completeness:.1f}%',
                Message=json.dumps(message, indent=2)
            )
            print(f"📧 Sent completeness alert to SNS")
        except Exception as e:
            print(f"⚠️ Failed to send alert: {e}")
    
    def configure_enforcement(self, enabled: bool = True, threshold: float = 100.0, alert_topic: str = None):
        """Configure enforcement settings"""
        self.enforcement_enabled = enabled
        self.completeness_threshold = threshold
        self.alert_topic_arn = alert_topic
        
        print(f"⚙️ Audit enforcement configured:")
        print(f"   Enabled: {enabled}")
        print(f"   Threshold: {threshold}%")
        print(f"   Alert Topic: {alert_topic or 'None'}")
        
        # Enforcement settings
        self.enforcement_enabled = True
        self.completeness_threshold = 100.0
        self.alert_topic_arn = None
        # Initialize observability engine if available
        if OBSERVABILITY_AVAILABLE:
            self.observability = ObservabilityEngine(region=region)
        else:
            self.observability = None
        
    
    def load_desired_spec(self, path: str = "./reports/desired_spec.json") -> Dict:
        """Carrega especificação desejada"""
        try:
            spec_path = Path(path)
            if not spec_path.exists():
                raise FileNotFoundError(f"Desired spec não encontrado: {path}")
            
            with open(spec_path, 'r') as f:
                spec = json.load(f)
            
            return spec
            
        except Exception as e:
            print(f"❌ Erro ao carregar desired spec: {e}")
            raise
    
    def inspect_cloudformation(self) -> Dict:
        """Inspeciona stacks do CloudFormation"""
        try:
            print("☁️ Inspecionando CloudFormation stacks...")
            
            stacks_info = {
                'stacks': [],
                'total_stacks': 0,
                'stack_resources': {}
            }
            
            # Listar todas as stacks
            paginator = self.cloudformation.get_paginator('describe_stacks')
            
            for page in paginator.paginate():
                for stack in page.get('Stacks', []):
                    stack_name = stack['StackName']
                    stack_status = stack['StackStatus']
                    
                    stack_info = {
                        'name': stack_name,
                        'status': stack_status,
                        'creation_time': stack.get('CreationTime', '').isoformat() if stack.get('CreationTime') else None,
                        'resources': []
                    }
                    
                    # Listar recursos da stack se estiver ativa
                    if 'COMPLETE' in stack_status:
                        try:
                            resources_paginator = self.cloudformation.get_paginator('describe_stack_resources')
                            
                            for resource_page in resources_paginator.paginate(StackName=stack_name):
                                for resource in resource_page.get('StackResources', []):
                                    resource_info = {
                                        'logical_id': resource.get('LogicalResourceId'),
                                        'physical_id': resource.get('PhysicalResourceId'),
                                        'type': resource.get('ResourceType'),
                                        'status': resource.get('ResourceStatus')
                                    }
                                    stack_info['resources'].append(resource_info)
                        
                        except ClientError as e:
                            print(f"⚠️ Erro ao listar recursos da stack {stack_name}: {e}")
                    
                    stacks_info['stacks'].append(stack_info)
                    stacks_info['stack_resources'][stack_name] = stack_info['resources']
            
            stacks_info['total_stacks'] = len(stacks_info['stacks'])
            
            print(f"☁️ CloudFormation: {stacks_info['total_stacks']} stacks encontradas")
            return stacks_info
            
        except Exception as e:
            print(f"❌ Erro ao inspecionar CloudFormation: {e}")
            return {'stacks': [], 'total_stacks': 0, 'stack_resources': {}}
    
    def inspect_real_resources(self) -> List[Dict]:
        """Consulta recursos reais via Resource Catalog"""
        try:
            print("🗄️ Consultando Resource Catalog...")
            
            # Buscar todos os recursos do catálogo
            all_resources = self.resource_catalog.list_resources(limit=1000)
            
            print(f"🗄️ Resource Catalog: {len(all_resources)} recursos encontrados")
            return all_resources
            
        except Exception as e:
            print(f"❌ Erro ao consultar Resource Catalog: {e}")
    
    def has_configuration_drift(self, desired: Dict, current: Dict) -> bool:
        """Check if there's configuration drift between desired and current"""
        
        # Simple drift detection - compare key properties
        drift_properties = ['type', 'status', 'tags']
        
        for prop in drift_properties:
            if desired.get(prop) != current.get(prop):
                return True
        
        return False
    
    def compare_state(self, desired_spec: Dict, cfn_state: Dict, catalog_resources: List[Dict]) -> Dict:
        """Compara estados: desired vs CloudFormation vs Resource Catalog"""
        print("🔍 Comparando estados...")
        
        # Extrair IDs dos recursos desejados
        desired_resources = desired_spec.get('resources', [])
        desired_ids = {r['id'] for r in desired_resources}
        
        # Extrair IDs do Resource Catalog
        catalog_ids = {r['resource_id'] for r in catalog_resources}
        
        # Extrair recursos do CloudFormation (mapeamento mais complexo)
        cfn_resources = set()
        for stack_name, resources in cfn_state.get('stack_resources', {}).items():
            for resource in resources:
                # Criar ID baseado no padrão IAL
                resource_id = f"cfn/{stack_name}/{resource['logical_id']}"
                cfn_resources.add(resource_id)
        
        # Análise de completude
        missing_in_catalog = desired_ids - catalog_ids
        extra_in_catalog = catalog_ids - desired_ids
        
        # Calcular completeness
        if desired_ids:
            found_in_catalog = len(desired_ids & catalog_ids)
            completeness = int((found_in_catalog / len(desired_ids)) * 100)
        else:
            completeness = 100
        
        # Análise por tipo de recurso
        resource_types_analysis = {}
        for resource in desired_resources:
            resource_type = resource.get('type', 'Unknown')
            if resource_type not in resource_types_analysis:
                resource_types_analysis[resource_type] = {
                    'desired': 0,
                    'found': 0,
                    'missing': []
                }
            
            resource_types_analysis[resource_type]['desired'] += 1
            
            if resource['id'] in catalog_ids:
                resource_types_analysis[resource_type]['found'] += 1
            else:
                resource_types_analysis[resource_type]['missing'].append(resource['id'])
        
        audit_result = {
            'timestamp': datetime.utcnow().isoformat(),
            'audit_version': '3.1',
            'desired_total': len(desired_ids),
            'catalog_total': len(catalog_ids),
            'cfn_total': len(cfn_resources),
            'completeness': completeness,
            'audit_passed': completeness == 100,
            'missing_resources': list(missing_in_catalog),
            'extra_resources': list(extra_in_catalog),
            'resource_types_analysis': resource_types_analysis,
            'cfn_stacks_count': cfn_state.get('total_stacks', 0),
            'summary': {
                'total_desired': len(desired_ids),
                'total_found': len(desired_ids & catalog_ids),
                'total_missing': len(missing_in_catalog),
                'total_extra': len(extra_in_catalog),
                'completeness_percentage': completeness
            }
        }
        
        print(f"📊 Completeness: {completeness}% ({len(desired_ids & catalog_ids)}/{len(desired_ids)})")
        
        # Processar recursos para Knowledge Graph
        if self.graph_enabled and catalog_resources:
            self._process_catalog_resources_for_graph(catalog_resources)
        
        return audit_result
    
    def _register_resource_in_graph(self, resource_info: Dict) -> bool:
        """Registra recurso no Knowledge Graph"""
        if not self.graph_enabled or not self.graph_populator:
            return False
        
        try:
            # Preparar informações do recurso para o grafo
            graph_resource_info = {
                'resource_id': resource_info.get('resource_id', resource_info.get('id')),
                'resource_type': resource_info.get('resource_type', resource_info.get('type')),
                'phase': resource_info.get('phase', 'unknown'),
                'metadata': resource_info.get('metadata', {}),
                'cloudformation_outputs': resource_info.get('cloudformation_outputs', {})
            }
            
            # Registrar no grafo
            success = self.graph_populator.register_resource(graph_resource_info)
            
            if success:
                print(f"📊 Recurso {graph_resource_info['resource_id']} registrado no Knowledge Graph")
            
            return success
            
        except Exception as e:
            print(f"⚠️ Erro registrando recurso no grafo: {e}")
            return False
    
    def _process_catalog_resources_for_graph(self, catalog_resources: List[Dict]) -> int:
        """Processa recursos do catálogo para o Knowledge Graph"""
        if not self.graph_enabled:
            return 0
        
        registered_count = 0
        
        try:
            print("📊 Processando recursos para Knowledge Graph...")
            
            for resource in catalog_resources:
                success = self._register_resource_in_graph(resource)
                if success:
                    registered_count += 1
            
            print(f"📊 Knowledge Graph: {registered_count}/{len(catalog_resources)} recursos processados")
            
        except Exception as e:
            print(f"⚠️ Erro processando recursos para grafo: {e}")
        
        return registered_count
    
    def generate_audit_report(self, audit_result: Dict, output_path: str = "./reports/creation_audit.json") -> str:
        """Gera relatório de auditoria"""
        try:
            # Garantir que diretório existe
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Salvar relatório
            with open(output_file, 'w') as f:
                json.dump(audit_result, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Relatório de auditoria salvo: {output_file}")
            
            # Também salvar versão timestamped
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            timestamped_file = output_file.parent / f"creation_audit_{timestamp}.json"
            
            with open(timestamped_file, 'w') as f:
                json.dump(audit_result, f, indent=2, ensure_ascii=False)
            
            return str(output_file)
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {e}")
            raise
    
    def run_full_audit(self) -> Dict:
        """Executa auditoria completa"""
        print("\n🔍 INICIANDO AUDITORIA COMPLETA")
        print("=" * 50)
        
        audit_start_time = datetime.utcnow()
        
        try:
            # 1. Carregar desired spec
            desired_spec = self.load_desired_spec()
            
            # 2. Inspecionar CloudFormation
            cfn_state = self.inspect_cloudformation()
            
            # 3. Consultar Resource Catalog
            catalog_resources = self.inspect_real_resources()
            
            # 4. Comparar estados
            audit_result = self.compare_state(desired_spec, cfn_state, catalog_resources)
            
            # 5. Gerar relatório
            report_path = self.generate_audit_report(audit_result)
            
            # 6. Registrar métricas
            self.observability.publish_metric('AuditCompleteness', audit_result['completeness'], 'Percent')
            self.observability.publish_metric('MissingResources', len(audit_result['missing_resources']))
            self.observability.publish_metric('ExtraResources', len(audit_result['extra_resources']))
            
            # 7. Log de auditoria
            self.observability.log_audit_event('audit_completed', {
                'completeness': audit_result['completeness'],
                'audit_passed': audit_result['audit_passed'],
                'total_desired': audit_result['desired_total'],
                'total_found': audit_result['summary']['total_found'],
                'missing_count': len(audit_result['missing_resources']),
                'extra_count': len(audit_result['extra_resources'])
            }, level='INFO' if audit_result['audit_passed'] else 'WARN')
            
            # 8. Exibir resultado
            self._display_audit_summary(audit_result)
            
            audit_result['execution_time'] = (datetime.utcnow() - audit_start_time).total_seconds()
            audit_result['report_path'] = report_path
            
            return audit_result
            
        except Exception as e:
            error_msg = f"Erro durante auditoria: {e}"
            print(f"❌ {error_msg}")
            
            # Log de erro
            self.observability.log_audit_event('audit_failed', {
                'error': str(e)
            }, level='ERROR')
            
            raise
    
    def _display_audit_summary(self, audit_result: Dict):
        """Exibe resumo da auditoria"""
        print(f"\n📊 RESUMO DA AUDITORIA")
        print("=" * 30)
        
        completeness = audit_result['completeness']
        
        if audit_result['audit_passed']:
            print(f"✅ AUDITORIA PASSOU - Completeness: {completeness}%")
        else:
            print(f"❌ AUDITORIA FALHOU - Completeness: {completeness}%")
        
        print(f"📋 Recursos desejados: {audit_result['desired_total']}")
        print(f"✅ Recursos encontrados: {audit_result['summary']['total_found']}")
        print(f"❌ Recursos ausentes: {audit_result['summary']['total_missing']}")
        print(f"➕ Recursos extras: {audit_result['summary']['total_extra']}")
        
        if audit_result['missing_resources']:
            print(f"\n❌ RECURSOS AUSENTES:")
            for resource_id in audit_result['missing_resources'][:10]:  # Mostrar apenas os primeiros 10
                print(f"  • {resource_id}")
            
            if len(audit_result['missing_resources']) > 10:
                print(f"  ... e mais {len(audit_result['missing_resources']) - 10} recursos")
        
        if audit_result['extra_resources']:
            print(f"\n➕ RECURSOS EXTRAS:")
            for resource_id in audit_result['extra_resources'][:5]:  # Mostrar apenas os primeiros 5
                print(f"  • {resource_id}")
            
            if len(audit_result['extra_resources']) > 5:
                print(f"  ... e mais {len(audit_result['extra_resources']) - 5} recursos")
        
        print(f"\n☁️ CloudFormation stacks: {audit_result['cfn_stacks_count']}")
        print(f"📄 Relatório salvo: {audit_result.get('report_path', 'N/A')}")
    
    def validate_completeness_gate(self, audit_result: Dict) -> bool:
        """Valida gate de completeness para pipeline"""
        completeness = audit_result.get('completeness', 0)
        
        if completeness < 100:
            print(f"\n🚨 PIPELINE GATE FAILED")
            print(f"❌ Infra incompleta — recursos ausentes. Completeness: {completeness}%")
            print(f"📄 Verifique creation_audit.json para detalhes")
            return False
        
        print(f"\n✅ PIPELINE GATE PASSED")
        print(f"✅ Infraestrutura 100% completa")
        return True

def main():
    """Função principal para execução standalone"""
    print("🔍 IAL Audit Validator v3.1")
    print("=" * 50)
    
    try:
        validator = AuditValidator()
        
        # Executar auditoria completa
        audit_result = validator.run_full_audit()
        
        # Validar gate de completeness
        gate_passed = validator.validate_completeness_gate(audit_result)
        
        # Código de saída baseado no gate
        return 0 if gate_passed else 1
        
    except Exception as e:
        print(f"💥 ERRO CRÍTICO: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
