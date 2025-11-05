#!/usr/bin/env python3
"""
Advanced Validator - Validação Avançada de Estado
Schema validation, consistency checks, e detecção de recursos órfãos
"""

import json
import jsonschema
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import re

class AdvancedValidator:
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.aws_resource_types = self._load_aws_resource_types()
    
    def _load_validation_rules(self) -> Dict:
        """Carrega regras de validação"""
        return {
            'required_fields': {
                'spec': ['metadata', 'domains', 'resources'],
                'resource': ['id', 'name', 'type', 'domain', 'phase'],
                'metadata': ['version', 'generated_at', 'total_resources']
            },
            'naming_patterns': {
                'resource_id': r'^[a-zA-Z0-9\-_/]+$',
                'domain': r'^[0-9]{2}-[a-z\-]+$',
                'phase': r'^[0-9]{2}-[a-z\-]+$'
            },
            'dependency_rules': {
                'max_depth': 10,
                'circular_dependency_check': True
            }
        }
    
    def _load_aws_resource_types(self) -> Set[str]:
        """Carrega tipos de recursos AWS válidos"""
        # Lista básica de tipos AWS comuns
        return {
            'AWS::EC2::VPC', 'AWS::EC2::Subnet', 'AWS::EC2::SecurityGroup',
            'AWS::EC2::Instance', 'AWS::EC2::InternetGateway', 'AWS::EC2::RouteTable',
            'AWS::S3::Bucket', 'AWS::S3::BucketPolicy',
            'AWS::IAM::Role', 'AWS::IAM::Policy', 'AWS::IAM::User', 'AWS::IAM::Group',
            'AWS::KMS::Key', 'AWS::KMS::Alias',
            'AWS::DynamoDB::Table',
            'AWS::RDS::DBInstance', 'AWS::RDS::DBCluster', 'AWS::RDS::DBSubnetGroup',
            'AWS::Lambda::Function', 'AWS::Lambda::Permission',
            'AWS::CloudFormation::Stack',
            'AWS::CloudWatch::Alarm', 'AWS::CloudWatch::Dashboard',
            'AWS::SNS::Topic', 'AWS::SNS::Subscription',
            'AWS::SQS::Queue',
            'AWS::ECS::Cluster', 'AWS::ECS::Service', 'AWS::ECS::TaskDefinition',
            'AWS::ElasticLoadBalancingV2::LoadBalancer',
            'AWS::ElasticLoadBalancingV2::TargetGroup',
            'AWS::Route53::RecordSet', 'AWS::Route53::HostedZone',
            'AWS::CloudFront::Distribution',
            'AWS::WAF::WebACL'
        }
    
    def validate_spec_schema(self, spec: Dict) -> List[str]:
        """Valida schema básico da especificação"""
        errors = []
        
        # Verificar campos obrigatórios do spec
        for field in self.validation_rules['required_fields']['spec']:
            if field not in spec:
                errors.append(f"Campo obrigatório ausente no spec: {field}")
        
        # Verificar metadados
        metadata = spec.get('metadata', {})
        for field in self.validation_rules['required_fields']['metadata']:
            if field not in metadata:
                errors.append(f"Campo obrigatório ausente nos metadados: {field}")
        
        # Validar versão
        version = metadata.get('version')
        if version and not re.match(r'^\d+\.\d+$', str(version)):
            errors.append(f"Formato de versão inválido: {version}")
        
        return errors
    
    def validate_resources(self, resources: List[Dict]) -> List[str]:
        """Valida recursos individuais"""
        errors = []
        resource_ids = set()
        
        for i, resource in enumerate(resources):
            resource_prefix = f"Recurso {i+1}"
            
            # Verificar campos obrigatórios
            for field in self.validation_rules['required_fields']['resource']:
                if field not in resource:
                    errors.append(f"{resource_prefix}: Campo obrigatório ausente: {field}")
                    continue
            
            # Validar ID único
            resource_id = resource.get('id')
            if resource_id:
                if resource_id in resource_ids:
                    errors.append(f"{resource_prefix}: ID duplicado: {resource_id}")
                else:
                    resource_ids.add(resource_id)
                
                # Validar padrão do ID
                if not re.match(self.validation_rules['naming_patterns']['resource_id'], resource_id):
                    errors.append(f"{resource_prefix}: Padrão de ID inválido: {resource_id}")
            
            # Validar tipo de recurso AWS
            resource_type = resource.get('type')
            if resource_type and not resource.get('custom_ial_resource', False):
                if resource_type not in self.aws_resource_types:
                    errors.append(f"{resource_prefix}: Tipo de recurso AWS desconhecido: {resource_type}")
            
            # Validar domínio
            domain = resource.get('domain')
            if domain and not re.match(self.validation_rules['naming_patterns']['domain'], domain):
                errors.append(f"{resource_prefix}: Padrão de domínio inválido: {domain}")
            
            # Validar fase
            phase = resource.get('phase')
            if phase and not re.match(self.validation_rules['naming_patterns']['phase'], phase):
                errors.append(f"{resource_prefix}: Padrão de fase inválido: {phase}")
            
            # Validar propriedades se for recurso CloudFormation
            if resource_type and resource_type.startswith('AWS::'):
                properties = resource.get('properties', {})
                if not isinstance(properties, dict):
                    errors.append(f"{resource_prefix}: Propriedades devem ser um objeto")
        
        return errors
    
    def validate_dependencies(self, spec: Dict) -> List[str]:
        """Valida dependências entre recursos"""
        errors = []
        
        resources = spec.get('resources', [])
        dependencies = spec.get('dependencies', {})
        
        # Criar mapa de recursos
        resource_ids = {r['id'] for r in resources}
        
        # Validar dependências
        for resource_id, deps in dependencies.items():
            if resource_id not in resource_ids:
                errors.append(f"Dependência definida para recurso inexistente: {resource_id}")
                continue
            
            for dep in deps:
                if dep not in resource_ids:
                    errors.append(f"Dependência inexistente: {dep} para recurso {resource_id}")
        
        # Detectar dependências circulares
        circular_deps = self._detect_circular_dependencies(dependencies)
        for cycle in circular_deps:
            errors.append(f"Dependência circular detectada: {' -> '.join(cycle)}")
        
        return errors
    
    def _detect_circular_dependencies(self, dependencies: Dict) -> List[List[str]]:
        """Detecta dependências circulares usando DFS"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Encontrou ciclo
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for dep in dependencies.get(node, []):
                if dfs(dep, path + [dep]):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for resource_id in dependencies:
            if resource_id not in visited:
                dfs(resource_id, [resource_id])
        
        return cycles
    
    def validate_consistency(self, spec: Dict) -> List[str]:
        """Valida consistência interna da especificação"""
        errors = []
        
        # Verificar consistência entre metadados e conteúdo
        metadata = spec.get('metadata', {})
        resources = spec.get('resources', [])
        domains = spec.get('domains', {})
        
        # Total de recursos
        expected_resources = metadata.get('total_resources', 0)
        actual_resources = len(resources)
        if expected_resources != actual_resources:
            errors.append(f"Inconsistência no total de recursos: esperado {expected_resources}, encontrado {actual_resources}")
        
        # Total de domínios
        expected_domains = metadata.get('total_domains', 0)
        actual_domains = len(domains)
        if expected_domains != actual_domains:
            errors.append(f"Inconsistência no total de domínios: esperado {expected_domains}, encontrado {actual_domains}")
        
        # Verificar se todos os recursos pertencem a domínios existentes
        for resource in resources:
            resource_domain = resource.get('domain')
            if resource_domain and resource_domain not in domains:
                errors.append(f"Recurso {resource.get('id')} pertence a domínio inexistente: {resource_domain}")
        
        # Verificar contagem de recursos por domínio
        for domain_name, domain_info in domains.items():
            expected_count = domain_info.get('resource_count', 0)
            actual_count = len([r for r in resources if r.get('domain') == domain_name])
            
            if expected_count != actual_count:
                errors.append(f"Inconsistência no domínio {domain_name}: esperado {expected_count} recursos, encontrado {actual_count}")
        
        return errors
    
    def validate_aws_best_practices(self, spec: Dict) -> List[str]:
        """Valida melhores práticas da AWS"""
        warnings = []
        resources = spec.get('resources', [])
        
        # Verificar recursos de segurança
        has_kms = any(r.get('type') == 'AWS::KMS::Key' for r in resources)
        has_iam_roles = any(r.get('type') == 'AWS::IAM::Role' for r in resources)
        
        if not has_kms:
            warnings.append("Recomendação: Considere adicionar chaves KMS para criptografia")
        
        if not has_iam_roles:
            warnings.append("Recomendação: Considere usar roles IAM em vez de usuários para serviços")
        
        # Verificar VPC e segurança de rede
        vpcs = [r for r in resources if r.get('type') == 'AWS::EC2::VPC']
        security_groups = [r for r in resources if r.get('type') == 'AWS::EC2::SecurityGroup']
        
        if vpcs and not security_groups:
            warnings.append("Recomendação: VPCs devem ter Security Groups definidos")
        
        # Verificar backup e monitoramento
        has_cloudwatch = any('CloudWatch' in r.get('type', '') for r in resources)
        if not has_cloudwatch:
            warnings.append("Recomendação: Considere adicionar monitoramento CloudWatch")
        
        return warnings
    
    def detect_orphaned_resources(self, spec: Dict, deployed_resources: List[Dict]) -> List[Dict]:
        """Detecta recursos órfãos (deployados mas não no desired state)"""
        desired_ids = {r['id'] for r in spec.get('resources', [])}
        deployed_ids = {r.get('resource_id', r.get('id')) for r in deployed_resources}
        
        orphaned_ids = deployed_ids - desired_ids
        
        orphaned_resources = []
        for resource in deployed_resources:
            resource_id = resource.get('resource_id', resource.get('id'))
            if resource_id in orphaned_ids:
                orphaned_resources.append({
                    'resource_id': resource_id,
                    'resource_type': resource.get('resource_type', resource.get('type')),
                    'phase': resource.get('phase'),
                    'status': resource.get('status'),
                    'reason': 'Recurso deployado mas não definido no desired state atual'
                })
        
        return orphaned_resources
    
    def comprehensive_validation(self, spec: Dict, deployed_resources: Optional[List[Dict]] = None) -> Dict:
        """Executa validação abrangente"""
        validation_result = {
            'timestamp': json.dumps(None, default=str),  # Will be replaced
            'validation_version': '3.1',
            'spec_version': spec.get('metadata', {}).get('version'),
            'total_resources': len(spec.get('resources', [])),
            'validation_passed': True,
            'errors': [],
            'warnings': [],
            'orphaned_resources': []
        }
        
        # Executar todas as validações
        try:
            # Schema validation
            schema_errors = self.validate_spec_schema(spec)
            validation_result['errors'].extend(schema_errors)
            
            # Resource validation
            resource_errors = self.validate_resources(spec.get('resources', []))
            validation_result['errors'].extend(resource_errors)
            
            # Dependency validation
            dependency_errors = self.validate_dependencies(spec)
            validation_result['errors'].extend(dependency_errors)
            
            # Consistency validation
            consistency_errors = self.validate_consistency(spec)
            validation_result['errors'].extend(consistency_errors)
            
            # Best practices validation
            best_practice_warnings = self.validate_aws_best_practices(spec)
            validation_result['warnings'].extend(best_practice_warnings)
            
            # Orphaned resources detection
            if deployed_resources:
                orphaned = self.detect_orphaned_resources(spec, deployed_resources)
                validation_result['orphaned_resources'] = orphaned
            
            # Determinar se validação passou
            validation_result['validation_passed'] = len(validation_result['errors']) == 0
            
            # Estatísticas
            validation_result['statistics'] = {
                'total_errors': len(validation_result['errors']),
                'total_warnings': len(validation_result['warnings']),
                'total_orphaned': len(validation_result['orphaned_resources']),
                'validation_score': self._calculate_validation_score(validation_result)
            }
            
        except Exception as e:
            validation_result['errors'].append(f"Erro durante validação: {str(e)}")
            validation_result['validation_passed'] = False
        
        # Fix timestamp
        from datetime import datetime
        validation_result['timestamp'] = datetime.utcnow().isoformat()
        
        return validation_result
    
    def _calculate_validation_score(self, validation_result: Dict) -> float:
        """Calcula score de validação (0-100)"""
        errors = len(validation_result['errors'])
        warnings = len(validation_result['warnings'])
        orphaned = len(validation_result['orphaned_resources'])
        
        # Penalidades
        error_penalty = errors * 20  # 20 pontos por erro
        warning_penalty = warnings * 5  # 5 pontos por warning
        orphaned_penalty = orphaned * 10  # 10 pontos por recurso órfão
        
        total_penalty = error_penalty + warning_penalty + orphaned_penalty
        score = max(0, 100 - total_penalty)
        
        return round(score, 2)
    
    def generate_validation_report(self, validation_result: Dict, output_file: Optional[str] = None) -> str:
        """Gera relatório de validação"""
        if not output_file:
            from datetime import datetime
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"validation_report_{timestamp}.json"
        
        output_path = Path(output_file)
        
        try:
            with open(output_path, 'w') as f:
                json.dump(validation_result, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Relatório de validação salvo em: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Erro ao salvar relatório: {e}")
            return None

def main():
    """Função principal para testes"""
    print("🔍 IAL Advanced Validator v3.1")
    print("=" * 50)
    
    validator = AdvancedValidator()
    
    # Teste com spec de exemplo
    test_spec = {
        'metadata': {
            'version': '3.1',
            'generated_at': '2023-01-01T00:00:00',
            'total_resources': 2,
            'total_domains': 1
        },
        'domains': {
            '10-security': {
                'phases': [{'name': '01-kms'}],
                'resource_count': 2
            }
        },
        'resources': [
            {
                'id': '10-security/01-kms/TestKMS',
                'name': 'TestKMS',
                'type': 'AWS::KMS::Key',
                'domain': '10-security',
                'phase': '01-kms',
                'properties': {'Description': 'Test key'}
            },
            {
                'id': '10-security/01-kms/TestAlias',
                'name': 'TestAlias',
                'type': 'AWS::KMS::Alias',
                'domain': '10-security',
                'phase': '01-kms',
                'properties': {'AliasName': 'alias/test-key'}
            }
        ],
        'dependencies': {}
    }
    
    # Executar validação
    result = validator.comprehensive_validation(test_spec)
    
    print(f"📊 Resultado da validação:")
    print(f"  ✅ Passou: {result['validation_passed']}")
    print(f"  ❌ Erros: {result['statistics']['total_errors']}")
    print(f"  ⚠️ Warnings: {result['statistics']['total_warnings']}")
    print(f"  📊 Score: {result['statistics']['validation_score']}/100")
    
    if result['errors']:
        print(f"\n❌ Erros encontrados:")
        for error in result['errors']:
            print(f"  • {error}")
    
    if result['warnings']:
        print(f"\n⚠️ Warnings encontrados:")
        for warning in result['warnings']:
            print(f"  • {warning}")
    
    return 0 if result['validation_passed'] else 1

if __name__ == "__main__":
    exit(main())
