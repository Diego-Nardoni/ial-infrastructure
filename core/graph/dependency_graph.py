from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum
import sys
import os

# Import ResourceCatalog for persistence
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from resource_catalog import ResourceCatalog
    PERSISTENCE_AVAILABLE = True
except ImportError:
    PERSISTENCE_AVAILABLE = False
    print("⚠️ ResourceCatalog not available, running in memory-only mode")

class ResourceState(Enum):
    HEALTHY = "healthy"
    DRIFT = "drift"
    HEALING = "healing"
    FAILED = "failed"
    UNKNOWN = "unknown"

class BlastRadius(Enum):
    MINIMAL = "minimal"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ResourceNode:
    id: str
    type: str
    state: ResourceState
    dependencies: List[str]  # Resources this depends on
    dependents: List[str]    # Resources that depend on this
    healing_priority: int    # 1=critical, 5=low
    blast_radius: BlastRadius
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DependencyGraph:
    """
    Graph-based dependency management for intelligent self-healing
    Now with DynamoDB persistence support
    """
    
    def __init__(self, enable_persistence: bool = True, region: str = "us-east-1"):
        self.nodes: Dict[str, ResourceNode] = {}
        self.edges: List[Tuple[str, str]] = []  # (from, to) relationships
        self._healing_order_cache: Optional[List[str]] = None
        
        # Persistence support
        self.enable_persistence = enable_persistence and PERSISTENCE_AVAILABLE
        self.resource_catalog = None
        
        if self.enable_persistence:
            try:
                self.resource_catalog = ResourceCatalog()
                #print("✅ DependencyGraph: Persistência habilitada")
            except Exception as e:
                print(f"⚠️ DependencyGraph: Erro inicializando persistência: {e}")
                self.enable_persistence = False
        
        # Load existing graph from persistence if available
        if self.enable_persistence:
            self._load_from_persistence()
    
    def _load_from_persistence(self):
        """Carrega grafo existente do DynamoDB"""
        try:
            if not self.resource_catalog:
                return
            
            #print("📊 DependencyGraph: Carregando grafo do DynamoDB...")
            
            # Por enquanto, carregamento sob demanda
            # TODO: Implementar carregamento completo se necessário
            #print("✅ DependencyGraph: Modo carregamento sob demanda ativo")
            
        except Exception as e:
            print(f"⚠️ Erro carregando grafo da persistência: {e}")
    
    def load_resource_from_persistence(self, resource_id: str) -> bool:
        """Carrega um recurso específico e suas dependências do DynamoDB"""
        try:
            if not self.enable_persistence or not self.resource_catalog:
                return False
            
            # Buscar dependências e dependentes
            relationships = self.resource_catalog.get_resource_dependencies(resource_id)
            dependents = self.resource_catalog.get_resource_dependents(resource_id)
            
            # Criar nó se não existir
            if resource_id not in self.nodes:
                # Buscar metadados do recurso
                resource_data = self.resource_catalog.get_resource(resource_id)
                if resource_data:
                    self.add_node(
                        resource_id=resource_id,
                        resource_type=resource_data.get('resource_type', 'Unknown'),
                        state=ResourceState.UNKNOWN
                    )
            
            # Adicionar dependências
            for dep in relationships:
                target_id = dep['target_id']
                if target_id not in self.nodes:
                    self.add_node(target_id, 'Unknown')
                
                # Adicionar relacionamento sem persistir novamente
                self._add_dependency_memory_only(resource_id, target_id)
            
            # Adicionar dependentes
            for dep in dependents:
                source_id = dep['source_id']
                if source_id not in self.nodes:
                    self.add_node(source_id, 'Unknown')
                
                self._add_dependency_memory_only(source_id, resource_id)
            
            print(f"✅ Recurso {resource_id} carregado do DynamoDB")
            return True
            
        except Exception as e:
            print(f"❌ Erro carregando recurso {resource_id}: {e}")
            return False
    
    def _add_dependency_memory_only(self, dependent_id: str, dependency_id: str):
        """Adiciona dependência apenas em memória (sem persistir)"""
        if dependent_id not in self.nodes or dependency_id not in self.nodes:
            return
        
        # Add to dependencies list
        if dependency_id not in self.nodes[dependent_id].dependencies:
            self.nodes[dependent_id].dependencies.append(dependency_id)
        
        # Add to dependents list
        if dependent_id not in self.nodes[dependency_id].dependents:
            self.nodes[dependency_id].dependents.append(dependent_id)
        
        # Add edge
        edge = (dependency_id, dependent_id)
        if edge not in self.edges:
            self.edges.append(edge)
        
        self._invalidate_cache()
        
    def add_node(self, resource_id: str, resource_type: str, 
                 state: ResourceState = ResourceState.UNKNOWN,
                 healing_priority: int = 3,
                 blast_radius: BlastRadius = BlastRadius.MODERATE) -> ResourceNode:
        """Add a resource node to the graph"""
        
        node = ResourceNode(
            id=resource_id,
            type=resource_type,
            state=state,
            dependencies=[],
            dependents=[],
            healing_priority=healing_priority,
            blast_radius=blast_radius
        )
        
        self.nodes[resource_id] = node
        self._invalidate_cache()
        return node
    
    def add_dependency(self, dependent_id: str, dependency_id: str, 
                      relationship_type: str = "generic", metadata: Optional[Dict] = None):
        """Add a dependency relationship: dependent depends on dependency"""
        
        if dependent_id not in self.nodes or dependency_id not in self.nodes:
            raise ValueError("Both resources must exist in graph before adding dependency")
        
        # Add to dependencies list
        if dependency_id not in self.nodes[dependent_id].dependencies:
            self.nodes[dependent_id].dependencies.append(dependency_id)
        
        # Add to dependents list
        if dependent_id not in self.nodes[dependency_id].dependents:
            self.nodes[dependency_id].dependents.append(dependent_id)
        
        # Add edge
        edge = (dependency_id, dependent_id)
        if edge not in self.edges:
            self.edges.append(edge)
        
        # Persist to DynamoDB if enabled
        if self.enable_persistence and self.resource_catalog:
            try:
                if metadata is None:
                    metadata = {}
                metadata.update({
                    'detection_method': 'manual',
                    'graph_version': '1.0'
                })
                
                self.resource_catalog.add_resource_relationship(
                    dependent_id, dependency_id, relationship_type, metadata
                )
            except Exception as e:
                print(f"⚠️ Erro persistindo relacionamento: {e}")
        
        self._invalidate_cache()
    
    def get_healing_order(self) -> List[str]:
        """Calculate optimal healing order based on dependencies"""
        
        if self._healing_order_cache is not None:
            return self._healing_order_cache
        
        # Get nodes that need healing
        drift_nodes = [node_id for node_id, node in self.nodes.items() 
                      if node.state == ResourceState.DRIFT]
        
        if not drift_nodes:
            return []
        
        # Topological sort with priority weighting
        healing_order = self._topological_sort_with_priority(drift_nodes)
        
        self._healing_order_cache = healing_order
        return healing_order
    
    def _topological_sort_with_priority(self, target_nodes: List[str]) -> List[str]:
        """Topological sort considering healing priorities"""
        
        # Build subgraph of nodes that need healing and their dependencies
        relevant_nodes = set(target_nodes)
        for node_id in target_nodes:
            relevant_nodes.update(self._get_all_dependencies(node_id))
        
        # Calculate in-degree for relevant nodes
        in_degree = {node_id: 0 for node_id in relevant_nodes}
        for node_id in relevant_nodes:
            for dep_id in self.nodes[node_id].dependencies:
                if dep_id in relevant_nodes:
                    in_degree[node_id] += 1
        
        # Priority queue: nodes with no dependencies first, then by priority
        queue = []
        for node_id in relevant_nodes:
            if in_degree[node_id] == 0:
                priority = self.nodes[node_id].healing_priority
                queue.append((priority, node_id))
        
        queue.sort()  # Sort by priority (lower number = higher priority)
        
        result = []
        while queue:
            _, current_node = queue.pop(0)
            
            # Only include nodes that actually need healing
            if current_node in target_nodes:
                result.append(current_node)
            
            # Update in-degrees of dependents
            for dependent_id in self.nodes[current_node].dependents:
                if dependent_id in relevant_nodes:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        priority = self.nodes[dependent_id].healing_priority
                        queue.append((priority, dependent_id))
                        queue.sort()
        
        return result
    
    def _get_all_dependencies(self, node_id: str) -> Set[str]:
        """Get all dependencies (recursive) for a node"""
        
        dependencies = set()
        to_visit = [node_id]
        visited = set()
        
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            
            visited.add(current)
            node_deps = self.nodes[current].dependencies
            dependencies.update(node_deps)
            to_visit.extend(node_deps)
        
        return dependencies
    
    def calculate_impact_score(self, node_id: str) -> int:
        """Calculate impact score for healing this node"""
        
        node = self.nodes[node_id]
        impact_score = 0
        
        # Dependents count (how many depend on this resource)
        dependents_count = len(node.dependents)
        impact_score += dependents_count * 10
        
        # Criticality based on resource type
        criticality_weights = {
            "AWS::EC2::VPC": 100,
            "AWS::EC2::SecurityGroup": 80,
            "AWS::RDS::DBInstance": 70,
            "AWS::EC2::Instance": 50,
            "AWS::S3::Bucket": 30,
            "AWS::Lambda::Function": 40
        }
        impact_score += criticality_weights.get(node.type, 20)
        
        # Blast radius impact
        blast_radius_weights = {
            BlastRadius.MINIMAL: 5,
            BlastRadius.MODERATE: 15,
            BlastRadius.HIGH: 30,
            BlastRadius.CRITICAL: 50
        }
        impact_score += blast_radius_weights[node.blast_radius]
        
        return impact_score
    
    def get_cascade_risk(self, node_id: str) -> List[str]:
        """Get list of resources that might be affected by healing this node"""
        
        cascade_resources = []
        node = self.nodes[node_id]
        
        # Direct dependents are at risk
        cascade_resources.extend(node.dependents)
        
        # Indirect dependents (dependents of dependents)
        for dependent_id in node.dependents:
            cascade_resources.extend(self.nodes[dependent_id].dependents)
        
        return list(set(cascade_resources))  # Remove duplicates
    
    def validate_healing_safety(self, node_id: str) -> Dict[str, any]:
        """Validate if it's safe to heal this node"""
        
        node = self.nodes[node_id]
        safety_check = {
            "safe": True,
            "warnings": [],
            "blockers": [],
            "cascade_risk": self.get_cascade_risk(node_id)
        }
        
        # Check if dependencies are healthy
        unhealthy_deps = []
        for dep_id in node.dependencies:
            if self.nodes[dep_id].state != ResourceState.HEALTHY:
                unhealthy_deps.append(dep_id)
        
        if unhealthy_deps:
            safety_check["warnings"].append(f"Unhealthy dependencies: {unhealthy_deps}")
        
        # Check blast radius
        if node.blast_radius == BlastRadius.CRITICAL:
            safety_check["blockers"].append("Critical blast radius - requires manual approval")
            safety_check["safe"] = False
        
        # Check cascade risk
        if len(safety_check["cascade_risk"]) > 10:
            safety_check["warnings"].append(f"High cascade risk: {len(safety_check['cascade_risk'])} resources at risk")
        
        return safety_check
    
    def _invalidate_cache(self):
        """Invalidate cached calculations"""
        self._healing_order_cache = None
    
    def get_graph_stats(self) -> Dict[str, any]:
        """Get statistics about the dependency graph"""
        
        states = {}
        for state in ResourceState:
            states[state.value] = len([n for n in self.nodes.values() if n.state == state])
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "states": states,
            "avg_dependencies": sum(len(n.dependencies) for n in self.nodes.values()) / len(self.nodes) if self.nodes else 0,
            "avg_dependents": sum(len(n.dependents) for n in self.nodes.values()) / len(self.nodes) if self.nodes else 0
        }
    
    def remove_resource(self, resource_id: str) -> Dict[str, Any]:
        """Remove resource and handle dependencies"""
        if resource_id not in self.nodes:
            return {'success': False, 'error': f'Resource {resource_id} not found'}
        
        # Get impacted resources before removal
        impacted = self._get_all_dependents(resource_id)
        
        # Remove from dependents
        node = self.nodes[resource_id]
        for dep_id in node.dependencies:
            if dep_id in self.nodes:
                self.nodes[dep_id].dependents.remove(resource_id)
        
        # Remove from dependencies
        for dep_id in node.dependents:
            if dep_id in self.nodes:
                self.nodes[dep_id].dependencies.remove(resource_id)
        
        # Remove edges
        self.edges = [(src, tgt) for src, tgt in self.edges if src != resource_id and tgt != resource_id]
        
        # Remove node
        del self.nodes[resource_id]
        
        # Persist if available
        if self.persistence_enabled and PERSISTENCE_AVAILABLE:
            try:
                self.catalog.remove_resource(resource_id)
            except Exception as e:
                print(f"⚠️ Failed to remove from catalog: {e}")
        
        self._invalidate_cache()
        
        return {
            'success': True,
            'removed_resource': resource_id,
            'impacted_resources': impacted,
            'cleanup_required': len(impacted) > 0
        }
