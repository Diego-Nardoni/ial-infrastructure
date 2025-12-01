#!/usr/bin/env python3
"""
IAL Fallback NLP - Processamento offline sem dependências externas
"""

import re
from typing import Dict, List

class FallbackNLP:
    """Processador NLP básico para modo offline"""
    
    def __init__(self):
        self.service_patterns = {
            's3': ['bucket', 's3', 'storage', 'object'],
            'ec2': ['instance', 'ec2', 'server', 'compute'],
            'rds': ['database', 'rds', 'mysql', 'postgres'],
            'lambda': ['function', 'lambda', 'serverless'],
            'vpc': ['network', 'vpc', 'subnet', 'security group'],
            'iam': ['role', 'policy', 'user', 'permission'],
            'cloudformation': ['stack', 'template', 'deploy']
        }
        
        self.action_patterns = {
            'create': ['create', 'deploy', 'setup', 'build', 'provision'],
            'delete': ['delete', 'remove', 'destroy', 'cleanup'],
            'list': ['list', 'show', 'describe', 'get'],
            'update': ['update', 'modify', 'change', 'edit']
        }
    
    def process(self, text: str) -> Dict:
        """Processar texto e extrair intenção básica"""
        text_lower = text.lower()
        
        # Detectar serviços
        detected_services = []
        for service, patterns in self.service_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                detected_services.append(service)
        
        # Detectar ações
        detected_actions = []
        for action, patterns in self.action_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                detected_actions.append(action)
        
        # Determinar intenção principal
        if 'foundation' in text_lower or 'start' in text_lower:
            intent = 'deploy_foundation'
        elif detected_actions:
            intent = detected_actions[0]
        else:
            intent = 'unknown'
        
        return {
            'intent': intent,
            'services': detected_services,
            'actions': detected_actions,
            'confidence': 0.7 if detected_services or detected_actions else 0.3,
            'mode': 'offline_fallback'
        }
    
    def extract_entities(self, text: str) -> List[Dict]:
        """Extrair entidades básicas do texto"""
        entities = []
        
        # Extrair nomes que parecem recursos AWS
        resource_pattern = r'\b[a-zA-Z0-9\-_]+\b'
        matches = re.findall(resource_pattern, text)
        
        for match in matches:
            if len(match) > 3 and '-' in match:
                entities.append({
                    'text': match,
                    'type': 'resource_name',
                    'confidence': 0.6
                })
        
        return entities
