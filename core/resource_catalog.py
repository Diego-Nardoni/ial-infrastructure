#!/usr/bin/env python3
"""
Resource Catalog - Catálogo básico de recursos para Audit Validator
"""

class ResourceCatalog:
    """Catálogo básico de recursos AWS"""
    
    def __init__(self):
        self.resources = {}
    
    def add_resource(self, resource_id: str, resource_type: str, metadata: dict = None):
        """Adicionar recurso ao catálogo"""
        self.resources[resource_id] = {
            'type': resource_type,
            'metadata': metadata or {},
            'status': 'active'
        }
    
    def get_resource(self, resource_id: str):
        """Obter recurso do catálogo"""
        return self.resources.get(resource_id)
    
    def list_resources(self):
        """Listar todos os recursos"""
        return list(self.resources.keys())
    
    def validate_resource(self, resource_id: str) -> bool:
        """Validar se recurso existe"""
        return resource_id in self.resources
