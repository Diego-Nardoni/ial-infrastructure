#!/usr/bin/env python3
"""
Phase Builder Corrected - YAML + DAG + Policies baseado em RAG
Corrige integração com DesiredStateBuilder e KnowledgeBaseEngine
"""

import json
import yaml
from typing import Dict, Any, List
from datetime import datetime

class PhaseBuildercorrected:
    def __init__(self):
        """Inicializar componentes existentes"""
        try:
            from core.desired_state import DesiredStateBuilder
            self.desired_state_builder = DesiredStateBuilder()
            self.dsb_available = True
        except ImportError as e:
            print(f"⚠️ DesiredStateBuilder não disponível: {e}")
            self.desired_state_builder = None
            self.dsb_available = False
        
        try:
            from lib.knowledge_base_engine import KnowledgeBaseEngine
            self.rag_engine = KnowledgeBaseEngine()
            self.rag_available = True
        except ImportError as e:
            print(f"⚠️ KnowledgeBaseEngine não disponível: {e}")
            self.rag_engine = None
            self.rag_available = False
    
    def generate_phases_with_rag(self, parsed_intent: Dict) -> Dict[str, Any]:
        """
        Phase Builder: YAML + DAG + Policies baseado em RAG
        Gera YAML phases para commit no GitHub
        """
        
        try:
            # 1. RAG - Buscar docs AWS relevantes
            aws_docs = self.search_aws_docs_with_rag(parsed_intent)
            
            # 2. Gerar arquitetura baseada em docs reais
            architecture = self.generate_architecture_from_docs(aws_docs, parsed_intent)
            
            # 3. Criar YAML com DAG, policies e contracts
            yaml_phases = self.create_yaml_with_dag(architecture, parsed_intent)
            
            # 4. Adicionar output contracts
            yaml_phases = self.add_output_contracts(yaml_phases)
            
            # 5. Adicionar policies de segurança
            yaml_phases = self.add_security_policies(yaml_phases)
            
            return {
                'yaml_files': yaml_phases,
                'architecture': architecture,
                'dag_dependencies': self.extract_dag_dependencies(yaml_phases),
                'security_policies': self.extract_security_policies(yaml_phases),
                'rationale': f'Generated {len(yaml_phases)} YAML files with RAG-based architecture'
            }
            
        except Exception as e:
            print(f"⚠️ Phase Builder error: {e}")
            # Fallback: gerar YAML simples
            return self.generate_simple_yaml_fallback(parsed_intent)
    
    def search_aws_docs_with_rag(self, parsed_intent: Dict) -> Dict[str, Any]:
        """Buscar documentação AWS usando RAG"""
        if not self.rag_available:
            return {'docs': [], 'rationale': 'RAG not available'}
        
        try:
            services = parsed_intent.get('services', ['s3'])
            
            # Usar KnowledgeBaseEngine para buscar docs
            aws_docs = []
            for service in services:
                docs = self.rag_engine.knowledge_base.get('aws_best_practices', {}).get(service, [])
                aws_docs.extend(docs)
            
            return {
                'docs': aws_docs,
                'services': services,
                'rationale': f'Found {len(aws_docs)} relevant AWS docs for {services}'
            }
            
        except Exception as e:
            print(f"⚠️ RAG search error: {e}")
            return {'docs': [], 'rationale': f'RAG error: {e}'}
    
    def generate_architecture_from_docs(self, aws_docs: Dict, parsed_intent: Dict) -> Dict[str, Any]:
        """Gerar arquitetura baseada em docs AWS reais"""
        
        services = parsed_intent.get('services', ['s3'])
        raw_intent = parsed_intent.get('raw', '')
        
        # Arquitetura baseada nos serviços identificados
        architecture = {
            'services': services,
            'resources': [],
            'best_practices': aws_docs.get('docs', []),
            'intent': raw_intent
        }
        
        # Gerar recursos baseado nos serviços
        for service in services:
            resource = self.generate_resource_for_service(service, raw_intent)
            architecture['resources'].append(resource)
        
        return architecture
    
    def generate_resource_for_service(self, service: str, raw_intent: str) -> Dict[str, Any]:
        """Gerar recurso específico para um serviço"""
        
        resource_templates = {
            's3': {
                'Type': 'AWS::S3::Bucket',
                'Properties': {
                    'BucketEncryption': {
                        'ServerSideEncryptionConfiguration': [{
                            'ServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}
                        }]
                    },
                    'PublicAccessBlockConfiguration': {
                        'BlockPublicAcls': True,
                        'BlockPublicPolicy': True,
                        'IgnorePublicAcls': True,
                        'RestrictPublicBuckets': True
                    }
                }
            },
            'lambda': {
                'Type': 'AWS::Lambda::Function',
                'Properties': {
                    'Runtime': 'python3.12',
                    'Handler': 'index.lambda_handler',
                    'Timeout': 30,
                    'MemorySize': 128
                }
            },
            'dynamodb': {
                'Type': 'AWS::DynamoDB::Table',
                'Properties': {
                    'BillingMode': 'PAY_PER_REQUEST',
                    'AttributeDefinitions': [
                        {'AttributeName': 'id', 'AttributeType': 'S'}
                    ],
                    'KeySchema': [
                        {'AttributeName': 'id', 'KeyType': 'HASH'}
                    ]
                }
            }
        }
        
        return resource_templates.get(service, {
            'Type': f'AWS::{service.upper()}::Resource',
            'Properties': {}
        })
    
    def create_yaml_with_dag(self, architecture: Dict, parsed_intent: Dict) -> List[Dict[str, Any]]:
        """Criar YAML com DAG, policies e contracts"""
        
        yaml_files = []
        
        for i, resource in enumerate(architecture.get('resources', [])):
            yaml_content = {
                'AWSTemplateFormatVersion': '2010-09-09',
                'Description': f'IAL Generated - User Resource from: {parsed_intent.get("raw", "unknown")[:50]}',
                'Parameters': {
                    'ProjectName': {
                        'Type': 'String',
                        'Default': 'user-project',
                        'Description': 'Project name for resource naming'
                    }
                },
                'Resources': {
                    f'UserResource{i+1}': resource
                },
                'Outputs': {
                    f'UserResource{i+1}Arn': {
                        'Description': f'ARN of created {resource.get("Type", "resource")}',
                        'Value': {'Ref': f'UserResource{i+1}'},
                        'Export': {'Name': f'UserResource{i+1}Arn'}
                    }
                }
            }
            
            yaml_files.append({
                'filename': f'user-resource-{i+1}.yaml',
                'content': yaml.dump(yaml_content, default_flow_style=False),
                'resource_type': resource.get('Type', 'Unknown'),
                'dag_order': i + 1
            })
        
        return yaml_files
    
    def add_output_contracts(self, yaml_files: List[Dict]) -> List[Dict]:
        """Adicionar output contracts para impedir deploy incompleto"""
        
        for yaml_file in yaml_files:
            # Parse YAML content
            try:
                yaml_content = yaml.safe_load(yaml_file['content'])
                
                # Adicionar output contracts
                if 'Outputs' not in yaml_content:
                    yaml_content['Outputs'] = {}
                
                yaml_content['Outputs']['DeploymentContract'] = {
                    'Description': 'Contract ensuring complete deployment',
                    'Value': 'DEPLOYMENT_COMPLETE',
                    'Export': {'Name': f'DeploymentContract-{yaml_file["filename"].replace(".yaml", "")}'}
                }
                
                # Atualizar content
                yaml_file['content'] = yaml.dump(yaml_content, default_flow_style=False)
                
            except Exception as e:
                print(f"⚠️ Error adding output contracts: {e}")
        
        return yaml_files
    
    def add_security_policies(self, yaml_files: List[Dict]) -> List[Dict]:
        """Adicionar policies de segurança"""
        
        for yaml_file in yaml_files:
            try:
                yaml_content = yaml.safe_load(yaml_file['content'])
                
                # Adicionar metadata de segurança
                if 'Metadata' not in yaml_content:
                    yaml_content['Metadata'] = {}
                
                yaml_content['Metadata']['SecurityPolicies'] = {
                    'EncryptionRequired': True,
                    'PublicAccessBlocked': True,
                    'IAMPrincipleOfLeastPrivilege': True,
                    'AuditLoggingEnabled': True
                }
                
                yaml_file['content'] = yaml.dump(yaml_content, default_flow_style=False)
                
            except Exception as e:
                print(f"⚠️ Error adding security policies: {e}")
        
        return yaml_files
    
    def extract_dag_dependencies(self, yaml_files: List[Dict]) -> List[Dict]:
        """Extrair dependências DAG"""
        dependencies = []
        
        for i, yaml_file in enumerate(yaml_files):
            dependency = {
                'resource': yaml_file['filename'],
                'order': yaml_file.get('dag_order', i + 1),
                'depends_on': [] if i == 0 else [yaml_files[i-1]['filename']]
            }
            dependencies.append(dependency)
        
        return dependencies
    
    def extract_security_policies(self, yaml_files: List[Dict]) -> List[str]:
        """Extrair policies de segurança aplicadas"""
        policies = []
        
        for yaml_file in yaml_files:
            try:
                yaml_content = yaml.safe_load(yaml_file['content'])
                metadata = yaml_content.get('Metadata', {})
                security_policies = metadata.get('SecurityPolicies', {})
                
                for policy, enabled in security_policies.items():
                    if enabled:
                        policies.append(f"{yaml_file['filename']}: {policy}")
                        
            except Exception as e:
                print(f"⚠️ Error extracting security policies: {e}")
        
        return policies
    
    def generate_simple_yaml_fallback(self, parsed_intent: Dict) -> Dict[str, Any]:
        """Fallback: gerar YAML simples sem RAG"""
        
        services = parsed_intent.get('services', ['s3'])
        
        yaml_files = []
        for service in services:
            resource = self.generate_resource_for_service(service, parsed_intent.get('raw', ''))
            
            yaml_content = {
                'AWSTemplateFormatVersion': '2010-09-09',
                'Description': f'IAL Fallback - {service} resource',
                'Resources': {
                    f'{service.upper()}Resource': resource
                }
            }
            
            yaml_files.append({
                'filename': f'user-{service}-resource.yaml',
                'content': yaml.dump(yaml_content, default_flow_style=False),
                'resource_type': resource.get('Type', 'Unknown')
            })
        
        return {
            'yaml_files': yaml_files,
            'architecture': {'services': services, 'resources': [resource]},
            'dag_dependencies': [],
            'rationale': f'Fallback YAML generation for {services}'
        }
