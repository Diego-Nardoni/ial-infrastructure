#!/usr/bin/env python3
"""
Intent Parser for IAL
Parses natural language input to extract infrastructure intent
"""

from typing import Dict, List

class IntentParser:
    def __init__(self):
        self.domain_patterns = {
            'foundation': ['foundation', 'base', 'core', 'phase 00', 'fundação', 'fase 00'],
            'security': ['security', 'segurança', 'kms', 'iam', 'secrets', 'fase 10'],
            'networking': ['network', 'rede', 'vpc', 'subnet', 'networking', 'fase 20'],
            'compute': ['compute', 'ec2', 'ecs', 'lambda', 'computação', 'fase 30'],
            'data': ['data', 'database', 'dynamodb', 'rds', 's3', 'dados', 'fase 40'],
            'application': ['application', 'app', 'aplicação', 'fase 50'],
            'observability': ['observability', 'monitoring', 'logs', 'observabilidade', 'fase 60'],
            'ai-ml': ['ai', 'ml', 'machine learning', 'bedrock', 'fase 70'],
            'governance': ['governance', 'governança', 'compliance', 'fase 90']
        }
        
        self.action_patterns = {
            'create': ['crie', 'create', 'deploy', 'implante', 'configure', 'setup'],
            'update': ['update', 'modify', 'change', 'altere', 'atualize'],
            'delete': ['delete', 'remove', 'destroy', 'remova', 'exclua'],
            'show': ['show', 'list', 'display', 'mostre', 'liste']
        }
    
    def parse(self, user_input: str) -> Dict:
        """Parse user input to extract infrastructure intent"""
        
        input_lower = user_input.lower()
        
        # Detect action
        action = 'create'  # default
        for act, patterns in self.action_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                action = act
                break
        
        # Detect domains
        domains = []
        for domain, patterns in self.domain_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                domains.append(domain)
        
        # Default to foundation if no domain detected
        if not domains:
            domains = ['foundation']
        
        # Calculate confidence based on matches
        confidence = 0.8 if domains and action != 'create' else 0.6
        if len(domains) > 1:
            confidence = 0.9
        
        return {
            'action': action,
            'domains': domains,
            'original_input': user_input,
            'confidence': confidence,
            'is_infrastructure_command': True
        }
    
    def is_infrastructure_command(self, user_input: str) -> bool:
        """Check if input is an infrastructure command"""
        input_lower = user_input.lower()
        
        # Check for infrastructure keywords
        infrastructure_keywords = [
            'crie', 'create', 'deploy', 'foundation', 'security', 
            'network', 'compute', 'phase', 'infrastructure', 'fase',
            'implante', 'configure', 'setup'
        ]
        
        return any(keyword in input_lower for keyword in infrastructure_keywords)
