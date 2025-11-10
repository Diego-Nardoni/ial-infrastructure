#!/usr/bin/env python3
"""
Graph Query API - Interface unificada para consultas do Knowledge Graph
Fornece APIs para impact analysis, dependency chains e healing order
"""

import sys
import os
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta

# Add core path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from .dependency_graph import DependencyGraph, ResourceState, BlastRadius
    from ..resource_catalog import ResourceCatalog
except ImportError:
    from .dependency_graph import DependencyGraph, ResourceState, BlastRadius
    from resource_catalog import ResourceCatalog

@dataclass
class ImpactAnalysisResult:
    """Resultado de análise de impacto"""
    resource_id: str
    direct_dependents: List[str]
    indirect_dependents: List[str]
    cascade_risk_score: int
    affected_services: List[str]
    blast_radius: str
    recommendations: List[str]

@dataclass
class DependencyChain:
    """Cadeia de dependências"""
    root_resource: str
    chain: List[str]
    depth: int
    critical_path: bool

class GraphQueryAPI:
    """
    API unificada para consultas do Knowledge Graph
    """
    
    def __init__(self, dependency_graph: DependencyGraph, resource_catalog: Optional[ResourceCatalog] = None):
        self.graph = dependency_graph
        self.resource_catalog = resource_catalog
        
        # Cache para queries frequentes (TTL: 5 minutos)
        self._cache = {}
        self._cache_ttl = 300
        
        print("✅ GraphQueryAPI inicializada")
    
    def get_impacted_resources(self, resource_id: str, max_depth: int = 5) -> ImpactAnalysisResult:
        """
        Análise completa de impacto de um recurso
        
        Args:
            resource_id: ID do recurso para análise
            max_depth: Profundidade máxima da análise
            
        Returns:
            Resultado completo da análise de impacto
        """
        cache_key = f"impact_{resource_id}_{max_depth}"
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached
        
        try:
            # Carregar recurso do DynamoDB se necessário
            if resource_id not in self.graph.nodes:
                self.graph.load_resource_from_persistence(resource_id)
            
            if resource_id not in self.graph.nodes:
                return ImpactAnalysisResult(
                    resource_id=resource_id,
                    direct_dependents=[],
                    indirect_dependents=[],
                    cascade_risk_score=0,
                    affected_services=[],
                    blast_radius="unknown",
                    recommendations=["Recurso não encontrado no grafo"]
                )
            
            # Análise de dependentes diretos
            direct_dependents = self.graph.nodes[resource_id].dependents.copy()
            
            # Análise de dependentes indiretos (BFS)
            indirect_dependents = []
            visited = set([resource_id] + direct_dependents)
            queue = direct_dependents.copy()
            current_depth = 1
            
            while queue and current_depth < max_depth:
                next_level = []
                
                for dependent_id in queue:
                    if dependent_id in self.graph.nodes:
                        for next_dependent in self.graph.nodes[dependent_id].dependents:
                            if next_dependent not in visited:
                                indirect_dependents.append(next_dependent)
                                next_level.append(next_dependent)
                                visited.add(next_dependent)
                
                queue = next_level
                current_depth += 1
            
            # Calcular score de risco em cascata
            cascade_risk_score = self._calculate_cascade_risk_score(
                resource_id, direct_dependents, indirect_dependents
            )
            
            # Identificar serviços afetados
            affected_services = self._identify_affected_services(
                direct_dependents + indirect_dependents
            )
            
            # Obter blast radius
            blast_radius = self.graph.nodes[resource_id].blast_radius.value
            
            # Gerar recomendações
            recommendations = self._generate_impact_recommendations(
                resource_id, direct_dependents, indirect_dependents, cascade_risk_score
            )
            
            result = ImpactAnalysisResult(
                resource_id=resource_id,
                direct_dependents=direct_dependents,
                indirect_dependents=indirect_dependents,
                cascade_risk_score=cascade_risk_score,
                affected_services=affected_services,
                blast_radius=blast_radius,
                recommendations=recommendations
            )
            
            # Cache do resultado
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"❌ Erro na análise de impacto para {resource_id}: {e}")
            return ImpactAnalysisResult(
                resource_id=resource_id,
                direct_dependents=[],
                indirect_dependents=[],
                cascade_risk_score=0,
                affected_services=[],
                blast_radius="unknown",
                recommendations=[f"Erro na análise: {str(e)}"]
            )
    
    def get_dependency_chain(self, resource_id: str, max_depth: int = 10) -> List[DependencyChain]:
        """
        Obtém cadeias completas de dependências
        
        Args:
            resource_id: ID do recurso raiz
            max_depth: Profundidade máxima das cadeias
            
        Returns:
            Lista de cadeias de dependências
        """
        cache_key = f"chains_{resource_id}_{max_depth}"
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached
        
        try:
            chains = []
            
            # Carregar recurso se necessário
            if resource_id not in self.graph.nodes:
                self.graph.load_resource_from_persistence(resource_id)
            
            if resource_id not in self.graph.nodes:
                return []
            
            # DFS para encontrar todas as cadeias
            def find_chains(current_id: str, path: List[str], depth: int):
                if depth >= max_depth:
                    return
                
                if current_id in self.graph.nodes:
                    dependencies = self.graph.nodes[current_id].dependencies
                    
                    if not dependencies:
                        # Fim da cadeia
                        if len(path) > 1:
                            chains.append(DependencyChain(
                                root_resource=resource_id,
                                chain=path.copy(),
                                depth=len(path),
                                critical_path=self._is_critical_path(path)
                            ))
                    else:
                        for dep_id in dependencies:
                            if dep_id not in path:  # Evitar ciclos
                                new_path = path + [dep_id]
                                find_chains(dep_id, new_path, depth + 1)
            
            find_chains(resource_id, [resource_id], 0)
            
            # Ordenar por criticidade e profundidade
            chains.sort(key=lambda x: (not x.critical_path, -x.depth))
            
            # Cache do resultado
            self._cache_result(cache_key, chains)
            
            return chains
            
        except Exception as e:
            print(f"❌ Erro obtendo cadeias de dependência para {resource_id}: {e}")
            return []
    
    def get_healing_order(self, failed_resources: List[str]) -> List[str]:
        """
        Calcula ordem otimizada de cura para recursos com falha
        
        Args:
            failed_resources: Lista de recursos com falha
            
        Returns:
            Lista ordenada de recursos para cura
        """
        try:
            # Marcar recursos como com drift
            for resource_id in failed_resources:
                if resource_id in self.graph.nodes:
                    self.graph.nodes[resource_id].state = ResourceState.DRIFT
            
            # Usar algoritmo do grafo
            healing_order = self.graph.get_healing_order()
            
            # Filtrar apenas recursos solicitados
            filtered_order = [r for r in healing_order if r in failed_resources]
            
            return filtered_order
            
        except Exception as e:
            print(f"❌ Erro calculando ordem de cura: {e}")
            return failed_resources  # Fallback para ordem original
    
    def explain_dependency(self, source_id: str, target_id: str) -> Dict:
        """
        Explica por que dois recursos têm dependência
        
        Args:
            source_id: Recurso dependente
            target_id: Recurso de dependência
            
        Returns:
            Explicação detalhada da dependência
        """
        try:
            explanation = {
                'source': source_id,
                'target': target_id,
                'relationship_exists': False,
                'relationship_type': 'none',
                'confidence': 0.0,
                'detection_method': 'unknown',
                'explanation': 'Nenhuma dependência encontrada',
                'technical_reason': '',
                'business_impact': ''
            }
            
            # Verificar se dependência existe no grafo
            if (source_id in self.graph.nodes and 
                target_id in self.graph.nodes[source_id].dependencies):
                
                explanation['relationship_exists'] = True
                
                # Buscar detalhes da dependência no DynamoDB
                if self.resource_catalog:
                    dependencies = self.resource_catalog.get_resource_dependencies(source_id)
                    
                    for dep in dependencies:
                        if dep['target_id'] == target_id:
                            explanation.update({
                                'relationship_type': dep['relationship_type'],
                                'confidence': dep['confidence'],
                                'detection_method': dep['detection_method'],
                                'explanation': self._generate_dependency_explanation(
                                    source_id, target_id, dep['relationship_type']
                                ),
                                'technical_reason': self._get_technical_reason(dep['relationship_type']),
                                'business_impact': self._get_business_impact(dep['relationship_type'])
                            })
                            break
            
            return explanation
            
        except Exception as e:
            print(f"❌ Erro explicando dependência {source_id} → {target_id}: {e}")
            return {
                'source': source_id,
                'target': target_id,
                'relationship_exists': False,
                'explanation': f'Erro na análise: {str(e)}'
            }
    
    def _calculate_cascade_risk_score(self, resource_id: str, direct: List[str], indirect: List[str]) -> int:
        """Calcula score de risco em cascata"""
        score = 0
        
        # Score base por dependentes diretos
        score += len(direct) * 10
        
        # Score por dependentes indiretos (peso menor)
        score += len(indirect) * 5
        
        # Bonus por blast radius do recurso
        if resource_id in self.graph.nodes:
            blast_radius = self.graph.nodes[resource_id].blast_radius
            blast_weights = {
                BlastRadius.MINIMAL: 5,
                BlastRadius.MODERATE: 15,
                BlastRadius.HIGH: 30,
                BlastRadius.CRITICAL: 50
            }
            score += blast_weights.get(blast_radius, 10)
        
        return min(score, 100)  # Cap em 100
    
    def _identify_affected_services(self, resource_ids: List[str]) -> List[str]:
        """Identifica serviços AWS afetados"""
        services = set()
        
        for resource_id in resource_ids:
            if resource_id in self.graph.nodes:
                resource_type = self.graph.nodes[resource_id].type
                
                # Mapear tipo para serviço
                service_mapping = {
                    'AWS::EC2::VPC': 'EC2',
                    'AWS::EC2::Subnet': 'EC2',
                    'AWS::EC2::Instance': 'EC2',
                    'AWS::RDS::DBInstance': 'RDS',
                    'AWS::ECS::Service': 'ECS',
                    'AWS::ElasticLoadBalancingV2::LoadBalancer': 'ELB',
                    'AWS::S3::Bucket': 'S3',
                    'AWS::Lambda::Function': 'Lambda'
                }
                
                service = service_mapping.get(resource_type, 'Unknown')
                services.add(service)
        
        return list(services)
    
    def _generate_impact_recommendations(self, resource_id: str, direct: List[str], 
                                       indirect: List[str], risk_score: int) -> List[str]:
        """Gera recomendações baseadas na análise de impacto"""
        recommendations = []
        
        if risk_score > 70:
            recommendations.append("⚠️ ALTO RISCO: Mudanças neste recurso podem causar impacto significativo")
            recommendations.append("Considere fazer mudanças durante janela de manutenção")
        
        if len(direct) > 5:
            recommendations.append(f"Recurso tem {len(direct)} dependentes diretos - validar impacto")
        
        if len(indirect) > 10:
            recommendations.append(f"Impacto indireto em {len(indirect)} recursos - monitorar cascata")
        
        if not recommendations:
            recommendations.append("✅ Impacto baixo - mudanças podem ser feitas com segurança")
        
        return recommendations
    
    def _is_critical_path(self, path: List[str]) -> bool:
        """Verifica se uma cadeia é crítica"""
        for resource_id in path:
            if resource_id in self.graph.nodes:
                node = self.graph.nodes[resource_id]
                if (node.blast_radius == BlastRadius.CRITICAL or 
                    node.healing_priority == 1):
                    return True
        return False
    
    def _generate_dependency_explanation(self, source_id: str, target_id: str, rel_type: str) -> str:
        """Gera explicação textual da dependência"""
        explanations = {
            'subnet_vpc': f"{source_id} é uma subnet que pertence à VPC {target_id}",
            'ecs_subnet': f"Serviço ECS {source_id} está executando na subnet {target_id}",
            'alb_subnet': f"Load Balancer {source_id} está configurado na subnet {target_id}",
            'rds_subnet': f"Instância RDS {source_id} está na subnet {target_id}",
            'resource_security_group': f"{source_id} usa o security group {target_id}"
        }
        
        return explanations.get(rel_type, f"{source_id} depende de {target_id}")
    
    def _get_technical_reason(self, rel_type: str) -> str:
        """Retorna razão técnica da dependência"""
        reasons = {
            'subnet_vpc': "Subnets são componentes lógicos dentro de uma VPC",
            'ecs_subnet': "Serviços ECS precisam de subnet para conectividade de rede",
            'alb_subnet': "ALBs precisam de subnets para distribuir tráfego",
            'rds_subnet': "RDS precisa de subnet group para isolamento de rede"
        }
        
        return reasons.get(rel_type, "Dependência técnica identificada")
    
    def _get_business_impact(self, rel_type: str) -> str:
        """Retorna impacto de negócio da dependência"""
        impacts = {
            'subnet_vpc': "Falha na VPC afeta todas as subnets e recursos conectados",
            'ecs_subnet': "Falha na subnet pode interromper serviços ECS",
            'alb_subnet': "Falha na subnet pode afetar balanceamento de carga",
            'rds_subnet': "Falha na subnet pode afetar conectividade do banco"
        }
        
        return impacts.get(rel_type, "Impacto de negócio a ser avaliado")
    
    def _get_cached_result(self, cache_key: str):
        """Obtém resultado do cache se válido"""
        if cache_key in self._cache:
            cached_time, result = self._cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_ttl:
                return result
        return None
    
    def _cache_result(self, cache_key: str, result):
        """Armazena resultado no cache"""
        self._cache[cache_key] = (datetime.now(), result)
        
        # Limpeza básica do cache
        if len(self._cache) > 100:
            # Remove entradas mais antigas
            oldest_keys = sorted(self._cache.keys(), 
                               key=lambda k: self._cache[k][0])[:20]
            for key in oldest_keys:
                del self._cache[key]
    
    def get_api_statistics(self) -> Dict:
        """Retorna estatísticas da API"""
        return {
            'cache_size': len(self._cache),
            'cache_ttl_seconds': self._cache_ttl,
            'graph_nodes': len(self.graph.nodes),
            'graph_edges': len(self.graph.edges)
        }
