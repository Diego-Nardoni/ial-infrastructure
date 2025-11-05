"""
Knowledge Graph Package
Provides dependency management and intelligent healing for IAL
"""

# Import main classes for easier access
try:
    from .dependency_graph import DependencyGraph, ResourceState, BlastRadius, ResourceNode
    from .graph_populator import GraphPopulator, InferredDependency
    from .graph_query_api import GraphQueryAPI, ImpactAnalysisResult, DependencyChain
    from .healing_orchestrator import GraphBasedHealingOrchestrator, HealingResult
    
    __all__ = [
        'DependencyGraph', 'ResourceState', 'BlastRadius', 'ResourceNode',
        'GraphPopulator', 'InferredDependency', 
        'GraphQueryAPI', 'ImpactAnalysisResult', 'DependencyChain',
        'GraphBasedHealingOrchestrator', 'HealingResult'
    ]
    
except ImportError as e:
    print(f"⚠️ Knowledge Graph: Erro importando módulos: {e}")
    __all__ = []
