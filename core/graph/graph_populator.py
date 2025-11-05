#!/usr/bin/env python3
"""
Graph Populator - Auto-população de dependências no Knowledge Graph
Infere relacionamentos automaticamente durante deploy de recursos
"""

import sys
import os
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add core path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from .dependency_graph import DependencyGraph, ResourceState, BlastRadius
    from ..decision_ledger import DecisionLedger
except ImportError:
    from dependency_graph import DependencyGraph, ResourceState, BlastRadius
    from decision_ledger import DecisionLedger

@dataclass
class InferredDependency:
    """Dependência inferida automaticamente"""
    source_id: str
    target_id: str
    relationship_type: str
    confidence: float
    detection_method: str
    metadata: Dict

class GraphPopulator:
    """
    Componente para inferir e popular dependências automaticamente
    """
    
    def __init__(self, dependency_graph: DependencyGraph):
        self.graph = dependency_graph
        self.decision_ledger = DecisionLedger()
        
        # Padrões heurísticos para inferência de dependências
        self.dependency_patterns = {
            # VPC patterns
            'subnet_vpc': {
                'source_pattern': r'subnet-\w+',
                'target_pattern': r'vpc-\w+',
                'confidence': 1.0,
                'relationship_type': 'subnet_vpc'
            },
            
            # ECS patterns
            'ecs_subnet': {
                'source_pattern': r'ecs-(service|cluster)-\w+',
                'target_pattern': r'subnet-\w+',
                'confidence': 0.9,
                'relationship_type': 'ecs_subnet'
            },
            
            # ALB patterns
            'alb_subnet': {
                'source_pattern': r'alb-\w+',
                'target_pattern': r'subnet-\w+',
                'confidence': 0.9,
                'relationship_type': 'alb_subnet'
            },
            
            # RDS patterns
            'rds_subnet': {
                'source_pattern': r'rds-\w+',
                'target_pattern': r'subnet-\w+',
                'confidence': 0.9,
                'relationship_type': 'rds_subnet'
            },
            
            # Security Group patterns
            'resource_sg': {
                'source_pattern': r'(ecs|alb|rds)-\w+',
                'target_pattern': r'sg-\w+',
                'confidence': 0.8,
                'relationship_type': 'resource_security_group'
            }
        }
    
    def register_resource(self, resource_info: Dict) -> bool:
        """Registra recurso no grafo e infere dependências"""
        try:
            resource_id = resource_info.get('resource_id')
            resource_type = resource_info.get('resource_type', 'Unknown')
            
            if not resource_id:
                print("❌ GraphPopulator: resource_id obrigatório")
                return False
            
            # Adicionar nó ao grafo
            node = self.graph.add_node(
                resource_id=resource_id,
                resource_type=resource_type,
                state=ResourceState.HEALTHY
            )
            
            # Inferir dependências
            dependencies = self.infer_dependencies(resource_info)
            
            # Adicionar dependências ao grafo
            for dep in dependencies:
                # Criar nó de dependência se não existir
                if dep.target_id not in self.graph.nodes:
                    self.graph.add_node(
                        resource_id=dep.target_id,
                        resource_type='Unknown',
                        state=ResourceState.UNKNOWN
                    )
                
                # Adicionar relacionamento
                self.graph.add_dependency(
                    dependent_id=dep.source_id,
                    dependency_id=dep.target_id,
                    relationship_type=dep.relationship_type,
                    metadata={
                        'confidence': dep.confidence,
                        'auto_detected': True,
                        'detection_method': dep.detection_method,
                        'phase_source': resource_info.get('phase', 'unknown')
                    }
                )
                
                # Log da decisão
                self.decision_ledger.log_decision(
                    decision_type="dependency_inference",
                    context={
                        'source': dep.source_id,
                        'target': dep.target_id,
                        'type': dep.relationship_type,
                        'confidence': dep.confidence,
                        'method': dep.detection_method
                    },
                    outcome="dependency_added"
                )
            
            print(f"✅ GraphPopulator: {resource_id} registrado com {len(dependencies)} dependências")
            return True
            
        except Exception as e:
            print(f"❌ GraphPopulator: Erro registrando {resource_info.get('resource_id')}: {e}")
            return False
    
    def infer_dependencies(self, resource_info: Dict) -> List[InferredDependency]:
        """Infere dependências baseado em padrões e metadados"""
        dependencies = []
        
        # Inferir por CloudFormation outputs
        cf_deps = self._infer_from_cloudformation_outputs(resource_info)
        dependencies.extend(cf_deps)
        
        # Inferir por padrões heurísticos
        heuristic_deps = self._infer_from_heuristic_patterns(resource_info)
        dependencies.extend(heuristic_deps)
        
        # Inferir por metadados
        metadata_deps = self._infer_from_metadata(resource_info)
        dependencies.extend(metadata_deps)
        
        return dependencies
    
    def _infer_from_cloudformation_outputs(self, resource_info: Dict) -> List[InferredDependency]:
        """Infere dependências dos outputs do CloudFormation"""
        dependencies = []
        
        try:
            outputs = resource_info.get('cloudformation_outputs', {})
            resource_id = resource_info['resource_id']
            
            # Padrões comuns em outputs
            output_patterns = {
                'VpcId': 'vpc_dependency',
                'SubnetId': 'subnet_dependency', 
                'SubnetIds': 'subnet_dependency',
                'SecurityGroupId': 'security_group_dependency',
                'SecurityGroupIds': 'security_group_dependency'
            }
            
            for output_key, value in outputs.items():
                for pattern, rel_type in output_patterns.items():
                    if pattern.lower() in output_key.lower():
                        # Extrair IDs dos valores
                        target_ids = self._extract_resource_ids(value)
                        
                        for target_id in target_ids:
                            dependencies.append(InferredDependency(
                                source_id=resource_id,
                                target_id=target_id,
                                relationship_type=rel_type,
                                confidence=0.95,
                                detection_method='cloudformation_output',
                                metadata={'output_key': output_key}
                            ))
            
        except Exception as e:
            print(f"⚠️ Erro inferindo por CF outputs: {e}")
        
        return dependencies
    
    def _infer_from_heuristic_patterns(self, resource_info: Dict) -> List[InferredDependency]:
        """Infere dependências usando padrões heurísticos"""
        dependencies = []
        
        try:
            resource_id = resource_info['resource_id']
            
            # Verificar padrões contra todos os recursos existentes
            for pattern_name, pattern_config in self.dependency_patterns.items():
                source_pattern = pattern_config['source_pattern']
                target_pattern = pattern_config['target_pattern']
                
                # Se o recurso atual corresponde ao padrão source
                if re.search(source_pattern, resource_id):
                    # Buscar recursos que correspondem ao target pattern
                    for existing_id in self.graph.nodes.keys():
                        if re.search(target_pattern, existing_id):
                            dependencies.append(InferredDependency(
                                source_id=resource_id,
                                target_id=existing_id,
                                relationship_type=pattern_config['relationship_type'],
                                confidence=pattern_config['confidence'],
                                detection_method='heuristic_pattern',
                                metadata={'pattern': pattern_name}
                            ))
                
                # Se o recurso atual corresponde ao padrão target
                elif re.search(target_pattern, resource_id):
                    # Buscar recursos que correspondem ao source pattern
                    for existing_id in self.graph.nodes.keys():
                        if re.search(source_pattern, existing_id):
                            dependencies.append(InferredDependency(
                                source_id=existing_id,
                                target_id=resource_id,
                                relationship_type=pattern_config['relationship_type'],
                                confidence=pattern_config['confidence'],
                                detection_method='heuristic_pattern',
                                metadata={'pattern': pattern_name}
                            ))
        
        except Exception as e:
            print(f"⚠️ Erro inferindo por padrões: {e}")
        
        return dependencies
    
    def _infer_from_metadata(self, resource_info: Dict) -> List[InferredDependency]:
        """Infere dependências dos metadados do recurso"""
        dependencies = []
        
        try:
            resource_id = resource_info['resource_id']
            metadata = resource_info.get('metadata', {})
            
            # Padrões em metadados
            metadata_patterns = {
                'vpc_id': 'vpc_dependency',
                'subnet_id': 'subnet_dependency',
                'subnet_ids': 'subnet_dependency',
                'security_group_id': 'security_group_dependency',
                'security_group_ids': 'security_group_dependency',
                'target_group_arn': 'target_group_dependency'
            }
            
            for key, value in metadata.items():
                key_lower = key.lower()
                
                for pattern, rel_type in metadata_patterns.items():
                    if pattern in key_lower:
                        target_ids = self._extract_resource_ids(value)
                        
                        for target_id in target_ids:
                            dependencies.append(InferredDependency(
                                source_id=resource_id,
                                target_id=target_id,
                                relationship_type=rel_type,
                                confidence=0.9,
                                detection_method='metadata_analysis',
                                metadata={'metadata_key': key}
                            ))
        
        except Exception as e:
            print(f"⚠️ Erro inferindo por metadados: {e}")
        
        return dependencies
    
    def _extract_resource_ids(self, value) -> List[str]:
        """Extrai IDs de recursos de um valor (string, lista, etc.)"""
        ids = []
        
        try:
            if isinstance(value, str):
                # Padrões de IDs AWS
                patterns = [
                    r'vpc-[a-f0-9]+',
                    r'subnet-[a-f0-9]+', 
                    r'sg-[a-f0-9]+',
                    r'i-[a-f0-9]+',
                    r'vol-[a-f0-9]+',
                    r'eni-[a-f0-9]+',
                    r'igw-[a-f0-9]+',
                    r'nat-[a-f0-9]+',
                    r'rtb-[a-f0-9]+',
                    r'acl-[a-f0-9]+'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, value)
                    ids.extend(matches)
            
            elif isinstance(value, list):
                for item in value:
                    ids.extend(self._extract_resource_ids(item))
            
            elif isinstance(value, dict):
                for v in value.values():
                    ids.extend(self._extract_resource_ids(v))
        
        except Exception as e:
            print(f"⚠️ Erro extraindo IDs: {e}")
        
        return list(set(ids))  # Remove duplicatas
    
    def get_inference_statistics(self) -> Dict:
        """Retorna estatísticas sobre inferências realizadas"""
        return {
            'total_patterns': len(self.dependency_patterns),
            'graph_nodes': len(self.graph.nodes),
            'graph_edges': len(self.graph.edges)
        }
