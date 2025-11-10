#!/usr/bin/env python3
"""
Dependency Graph - Grafo básico de dependências
"""

class DependencyGraph:
    """Grafo básico de dependências"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
    
    def add_node(self, node_id: str, metadata: dict = None):
        """Adicionar nó ao grafo"""
        self.nodes[node_id] = metadata or {}
    
    def add_edge(self, from_node: str, to_node: str):
        """Adicionar aresta ao grafo"""
        self.edges.append((from_node, to_node))
    
    def get_dependencies(self, node_id: str):
        """Obter dependências de um nó"""
        return [edge[1] for edge in self.edges if edge[0] == node_id]
    
    def validate_graph(self) -> bool:
        """Validar grafo básico"""
        return len(self.nodes) > 0
