#!/usr/bin/env python3
"""Validate Completeness - 100% Resource Validation"""

import boto3
import yaml
import json
import sys
from pathlib import Path
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import CloudFormation YAML loader
sys.path.append(str(Path(__file__).parent))
from cf_yaml_loader import load_cf_yaml

PROJECT_ROOT = Path(__file__).parent.parent
PHASES_DIR = PROJECT_ROOT / 'phases'

# AWS clients
cloudcontrol = boto3.client('cloudcontrol')
cloudformation = boto3.client('cloudformation')

class CompletenessValidator:
    def __init__(self):
        self.expected_resources = {}
        self.actual_resources = {}
        self.missing_resources = []
        self.validation_errors = []
        
    def discover_expected_resources(self) -> Dict:
        """Descobre todos os recursos esperados das fases"""
        expected = {}
        
        for domain_dir in PHASES_DIR.iterdir():
            if not domain_dir.is_dir() or domain_dir.name.startswith('.'):
                continue
                
            for yaml_file in domain_dir.glob('*.yaml'):
                if yaml_file.name in ['domain-metadata.yaml', 'deployment-order.yaml']:
                    continue
                    
                try:
                    # Usar CloudFormation YAML loader
                    content = load_cf_yaml(yaml_file)
                    
                    if isinstance(content, dict) and 'Resources' in content:
                        for resource_name, resource_def in content['Resources'].items():
                            resource_type = resource_def.get('Type')
                            if resource_type:
                                key = f"{domain_dir.name}/{yaml_file.stem}/{resource_name}"
                                expected[key] = {
                                    'type': resource_type,
                                    'name': resource_name,
                                    'domain': domain_dir.name,
                                    'phase': yaml_file.stem,
                                    'properties': resource_def.get('Properties', {})
                                }
                                
                except Exception as e:
                    self.validation_errors.append(f"Erro lendo {yaml_file}: {e}")
                    
        return expected
    
    def get_actual_resources_cloudcontrol(self, resource_type: str) -> List[Dict]:
        """Obtém recursos reais usando Cloud Control API"""
        try:
            paginator = cloudcontrol.get_paginator('list_resources')
            resources = []
            
            for page in paginator.paginate(TypeName=resource_type):
                for resource in page.get('ResourceDescriptions', []):
                    resources.append({
                        'identifier': resource.get('Identifier'),
                        'properties': json.loads(resource.get('Properties', '{}')),
                        'type': resource_type
                    })
                    
            return resources
            
        except Exception as e:
            # Fallback para APIs específicas se Cloud Control não suportar
            return self._fallback_resource_discovery(resource_type)
    
    def _fallback_resource_discovery(self, resource_type: str) -> List[Dict]:
        """Fallback para recursos não suportados pelo Cloud Control"""
        fallback_map = {
            'AWS::S3::Bucket': self._get_s3_buckets,
            'AWS::EC2::VPC': self._get_vpcs,
            'AWS::IAM::Role': self._get_iam_roles,
            'AWS::DynamoDB::Table': self._get_dynamodb_tables,
            'AWS::ECS::Cluster': self._get_ecs_clusters
        }
        
        if resource_type in fallback_map:
            try:
                return fallback_map[resource_type]()
            except Exception as e:
                self.validation_errors.append(f"Erro fallback {resource_type}: {e}")
                return []
        
        return []
    
    def _get_s3_buckets(self) -> List[Dict]:
        """Fallback para S3 buckets"""
        s3 = boto3.client('s3')
        try:
            response = s3.list_buckets()
            return [{'identifier': bucket['Name'], 'type': 'AWS::S3::Bucket'} 
                   for bucket in response.get('Buckets', [])]
        except:
            return []
    
    def _get_vpcs(self) -> List[Dict]:
        """Fallback para VPCs"""
        ec2 = boto3.client('ec2')
        try:
            response = ec2.describe_vpcs()
            return [{'identifier': vpc['VpcId'], 'type': 'AWS::EC2::VPC'} 
                   for vpc in response.get('Vpcs', [])]
        except:
            return []
    
    def _get_iam_roles(self) -> List[Dict]:
        """Fallback para IAM roles"""
        iam = boto3.client('iam')
        try:
            paginator = iam.get_paginator('list_roles')
            roles = []
            for page in paginator.paginate():
                roles.extend([{'identifier': role['RoleName'], 'type': 'AWS::IAM::Role'} 
                            for role in page.get('Roles', [])])
            return roles
        except:
            return []
    
    def _get_dynamodb_tables(self) -> List[Dict]:
        """Fallback para DynamoDB tables"""
        dynamodb = boto3.client('dynamodb')
        try:
            response = dynamodb.list_tables()
            return [{'identifier': table, 'type': 'AWS::DynamoDB::Table'} 
                   for table in response.get('TableNames', [])]
        except:
            return []
    
    def _get_ecs_clusters(self) -> List[Dict]:
        """Fallback para ECS clusters"""
        ecs = boto3.client('ecs')
        try:
            response = ecs.list_clusters()
            return [{'identifier': cluster.split('/')[-1], 'type': 'AWS::ECS::Cluster'} 
                   for cluster in response.get('clusterArns', [])]
        except:
            return []
    
    def validate_completeness(self) -> Dict:
        """Executa validação completa de recursos"""
        
        print("🔍 Descobrindo recursos esperados...")
        self.expected_resources = self.discover_expected_resources()
        
        print(f"📋 Encontrados {len(self.expected_resources)} recursos esperados")
        
        # Agrupar por tipo de recurso para otimizar consultas
        resource_types = set(res['type'] for res in self.expected_resources.values())
        
        print("🔎 Validando recursos na AWS...")
        
        # Usar ThreadPoolExecutor para paralelizar consultas
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_type = {
                executor.submit(self.get_actual_resources_cloudcontrol, rt): rt 
                for rt in resource_types
            }
            
            actual_by_type = {}
            for future in as_completed(future_to_type):
                resource_type = future_to_type[future]
                try:
                    actual_by_type[resource_type] = future.result()
                except Exception as e:
                    self.validation_errors.append(f"Erro validando {resource_type}: {e}")
                    actual_by_type[resource_type] = []
        
        # Verificar completude
        missing = []
        found = []
        
        for expected_key, expected_resource in self.expected_resources.items():
            resource_type = expected_resource['type']
            resource_name = expected_resource['name']
            
            # Procurar recurso nos recursos reais
            actual_resources = actual_by_type.get(resource_type, [])
            
            found_resource = False
            for actual in actual_resources:
                # Matching por nome ou identificador
                if (actual.get('identifier') == resource_name or 
                    resource_name in str(actual.get('identifier', ''))):
                    found_resource = True
                    found.append(expected_key)
                    break
            
            if not found_resource:
                missing.append(expected_key)
        
        # Resultado da validação
        validation_result = {
            'timestamp': str(pd.Timestamp.now()),
            'total_expected': len(self.expected_resources),
            'total_found': len(found),
            'total_missing': len(missing),
            'completeness_percentage': (len(found) / len(self.expected_resources)) * 100 if self.expected_resources else 100,
            'is_complete': len(missing) == 0,
            'missing_resources': missing,
            'found_resources': found,
            'validation_errors': self.validation_errors,
            'resource_types_checked': list(resource_types)
        }
        
        return validation_result
    
    def generate_report(self, validation_result: Dict) -> None:
        """Gera relatório de validação"""
        
        report_file = PROJECT_ROOT / 'reports' / 'completeness_validation.json'
        
        with open(report_file, 'w') as f:
            json.dump(validation_result, f, indent=2, default=str)
        
        # Console output
        print(f"\n📊 RELATÓRIO DE COMPLETUDE")
        print(f"{'='*50}")
        print(f"Total Esperado: {validation_result['total_expected']}")
        print(f"Total Encontrado: {validation_result['total_found']}")
        print(f"Total Ausente: {validation_result['total_missing']}")
        print(f"Completude: {validation_result['completeness_percentage']:.1f}%")
        
        if validation_result['missing_resources']:
            print(f"\n❌ RECURSOS AUSENTES:")
            for missing in validation_result['missing_resources']:
                print(f"  - {missing}")
        
        if validation_result['validation_errors']:
            print(f"\n⚠️ ERROS DE VALIDAÇÃO:")
            for error in validation_result['validation_errors']:
                print(f"  - {error}")
        
        print(f"\n📄 Relatório salvo: {report_file}")

def main():
    """Execução principal"""
    try:
        validator = CompletenessValidator()
        result = validator.validate_completeness()
        validator.generate_report(result)
        
        # Exit code baseado na completude
        if result['is_complete']:
            print("✅ Validação PASSOU - Todos os recursos estão presentes")
            return 0
        else:
            print("❌ Validação FALHOU - Recursos ausentes detectados")
            return 1
            
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        return 1

if __name__ == '__main__':
    import pandas as pd
    exit(main())
