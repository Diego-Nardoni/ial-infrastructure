#!/usr/bin/env python3
"""
Resource Router - Decisão inteligente: CORE vs USER
Determina se uma solicitação deve usar bootstrap CORE ou pipeline USER
"""

import re
from typing import Dict, Any

class ResourceRouter:
    def __init__(self):
        """Inicializar padrões de classificação"""
        
        # Keywords que indicam recursos CORE
        self.core_keywords = [
            'ial foundation', 'ial system', 'bootstrap', 'core infrastructure',
            'drift detector', 'reconciliation engine', 'audit validator',
            'phase orchestrator', 'phase manager', 'resource tracker',
            'cost monitor', 'security scanner', 'conversation capture',
            'mcp provisioning', 'foundation infrastructure'
        ]
        
        # Keywords que indicam recursos USER
        self.user_keywords = [
            'my project', 'my application', 'my app', 'my service',
            'project data', 'application data', 'business logic',
            'user authentication', 'customer data', 'production workload'
        ]
        
        # Tipos de recursos que são sempre USER
        self.always_user_types = [
            'ec2 instance', 'rds database', 'rds cluster',
            'vpc', 'api gateway', 'cloudfront distribution',
            'elasticache cluster', 'elasticsearch domain',
            'ecs cluster', 'eks cluster', 'fargate service'
        ]
    
    def route_request(self, nl_intent: str) -> str:
        """
        Decide se a solicitação deve usar CORE_PATH ou USER_PATH
        
        Args:
            nl_intent: Intenção em linguagem natural
            
        Returns:
            "CORE_PATH" ou "USER_PATH"
        """
        
        nl_lower = nl_intent.lower()
        
        # 1. Verificar keywords CORE
        for keyword in self.core_keywords:
            if keyword in nl_lower:
                return "CORE_PATH"
        
        # 2. Verificar tipos sempre USER
        for user_type in self.always_user_types:
            if user_type in nl_lower:
                return "USER_PATH"
        
        # 3. Verificar keywords USER
        for keyword in self.user_keywords:
            if keyword in nl_lower:
                return "USER_PATH"
        
        # 4. Análise contextual
        context_score = self.analyze_context(nl_lower)
        
        if context_score > 0.5:
            return "USER_PATH"
        elif context_score < -0.5:
            return "CORE_PATH"
        else:
            # Default: recursos genéricos vão para USER_PATH (GitOps)
            return "USER_PATH"
    
    def analyze_context(self, nl_lower: str) -> float:
        """
        Análise contextual para determinar CORE vs USER
        
        Returns:
            Score: -1.0 (CORE) a +1.0 (USER)
        """
        
        score = 0.0
        
        # Indicadores USER (+)
        user_indicators = [
            'create', 'deploy', 'setup', 'configure',
            'bucket', 'database', 'server', 'cluster',
            'for my', 'for the', 'application', 'service'
        ]
        
        # Indicadores CORE (-)
        core_indicators = [
            'ial', 'foundation', 'system', 'infrastructure',
            'monitoring', 'logging', 'drift', 'reconciliation'
        ]
        
        # Contar indicadores USER
        for indicator in user_indicators:
            if indicator in nl_lower:
                score += 0.2
        
        # Contar indicadores CORE
        for indicator in core_indicators:
            if indicator in nl_lower:
                score -= 0.3
        
        # Limitar score entre -1.0 e +1.0
        return max(-1.0, min(1.0, score))
    
    def get_routing_explanation(self, nl_intent: str) -> Dict[str, Any]:
        """
        Explicar a decisão de roteamento
        
        Returns:
            Dicionário com detalhes da decisão
        """
        
        path = self.route_request(nl_intent)
        nl_lower = nl_intent.lower()
        
        # Identificar matches
        core_matches = [kw for kw in self.core_keywords if kw in nl_lower]
        user_matches = [kw for kw in self.user_keywords if kw in nl_lower]
        user_type_matches = [ut for ut in self.always_user_types if ut in nl_lower]
        
        context_score = self.analyze_context(nl_lower)
        
        return {
            'path': path,
            'intent': nl_intent,
            'core_matches': core_matches,
            'user_matches': user_matches,
            'user_type_matches': user_type_matches,
            'context_score': context_score,
            'rationale': self.generate_rationale(path, core_matches, user_matches, user_type_matches, context_score)
        }
    
    def generate_rationale(self, path: str, core_matches: list, user_matches: list, 
                          user_type_matches: list, context_score: float) -> str:
        """Gerar explicação da decisão"""
        
        if path == "CORE_PATH":
            if core_matches:
                return f"CORE_PATH: Detected IAL Foundation keywords: {', '.join(core_matches)}"
            else:
                return f"CORE_PATH: Context analysis score: {context_score:.2f} (< -0.5)"
        
        else:  # USER_PATH
            if user_type_matches:
                return f"USER_PATH: Detected user resource types: {', '.join(user_type_matches)}"
            elif user_matches:
                return f"USER_PATH: Detected user keywords: {', '.join(user_matches)}"
            else:
                return f"USER_PATH: Default routing for user resources (context score: {context_score:.2f})"
    
    def is_core_resource(self, nl_intent: str) -> bool:
        """Verificar se é recurso CORE (compatibilidade)"""
        return self.route_request(nl_intent) == "CORE_PATH"
    
    def is_user_resource(self, nl_intent: str) -> bool:
        """Verificar se é recurso USER"""
        return self.route_request(nl_intent) == "USER_PATH"
