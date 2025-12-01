"""
Intent Parser - Reutiliza ServiceDetector existente do IAL
"""

import sys
import os
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

# Import ServiceDetector existente
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from service_detector import ServiceDetector

class OperationType(Enum):
    CREATE = "create"
    UPDATE = "update" 
    DELETE = "delete"
    READ = "read"

@dataclass
class ParsedIntent:
    raw_text: str
    operations: List[OperationType]
    aws_services: List[str]
    confidence: float
    detected_patterns: List[str]

class IntentParser:
    def __init__(self):
        # Reutilizar ServiceDetector existente
        self.service_detector = ServiceDetector()
        
        # Padrões de operações
        self.operation_patterns = {
            OperationType.CREATE: ['create', 'deploy', 'launch', 'setup', 'provision', 'build'],
            OperationType.UPDATE: ['update', 'modify', 'change', 'scale', 'resize'],
            OperationType.DELETE: ['delete', 'remove', 'terminate', 'destroy', 'rollback'],
            OperationType.READ: ['show', 'list', 'describe', 'get', 'status', 'check']
        }

    def parse_intent(self, user_input: str) -> ParsedIntent:
        """Parse user intent reutilizando ServiceDetector"""
        
        # Usar ServiceDetector existente
        detection_result = self.service_detector.detect(user_input)
        detected_services = detection_result.get('services', [])
        
        # Extrair nomes dos serviços
        service_names = [service.name for service in detected_services]
        
        # Detectar operações
        operations = self._detect_operations(user_input)
        
        # Detectar padrões arquiteturais
        patterns = self._detect_patterns(user_input, service_names)
        
        # Calcular confiança
        confidence = self._calculate_confidence(user_input, service_names, operations)
        
        return ParsedIntent(
            raw_text=user_input,
            operations=operations,
            aws_services=service_names,
            confidence=confidence,
            detected_patterns=patterns
        )
    
    def parse_intent_dict(self, user_input: str) -> Dict:
        """Parse intent retornando dicionário para compatibilidade com testes"""
        parsed = self.parse_intent(user_input)
        
        # Determinar tipo de intent baseado nos serviços e operações
        intent_type = self._determine_intent_type(parsed.aws_services, parsed.operations)
        
        return {
            'intent_type': intent_type,
            'entities': {
                'services': parsed.aws_services,
                'operations': [op.value for op in parsed.operations],
                'patterns': parsed.detected_patterns
            },
            'confidence': parsed.confidence,
            'raw_text': parsed.raw_text
        }
    
    def _determine_intent_type(self, services: List[str], operations: List[OperationType]) -> str:
        """Determina o tipo de intent baseado nos serviços e operações"""
        
        # Análise de custo
        cost_keywords = ['cost', 'billing', 'budget', 'price', 'expense']
        if any(keyword in ' '.join(services).lower() for keyword in cost_keywords):
            return 'cost_analysis'
        
        # Análise de segurança
        security_services = ['iam', 'kms', 'waf', 'guardduty', 'security']
        security_keywords = ['security', 'vulnerability', 'compliance', 'audit']
        if (any(service in security_services for service in services) or 
            any(keyword in ' '.join(services).lower() for keyword in security_keywords)):
            return 'security_analysis'
        
        # Deployment
        if OperationType.CREATE in operations:
            return 'deployment'
        
        # Update
        if OperationType.UPDATE in operations:
            return 'update'
        
        # Análise/leitura
        if OperationType.READ in operations:
            return 'analysis'
        
        # Default
        if not services and not operations:
            return 'unknown'
        
        return 'deployment'
        
        # Detectar operações
        operations = self._detect_operations(user_input)
        
        # Detectar padrões arquiteturais
        patterns = self._detect_patterns(user_input)
        
        # Calcular confiança
        confidence = self._calculate_confidence(detected_services, operations)
        
        return ParsedIntent(
            raw_text=user_input,
            operations=operations,
            aws_services=service_names,
            confidence=confidence,
            detected_patterns=patterns
        )

    def _detect_operations(self, text: str) -> List[OperationType]:
        """Detectar operações no texto"""
        text_lower = text.lower()
        operations = []
        
        for op_type, keywords in self.operation_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                operations.append(op_type)
        
        return operations

    def _detect_patterns(self, text: str) -> List[str]:
        """Detectar padrões arquiteturais"""
        text_lower = text.lower()
        patterns = []
        
        pattern_keywords = {
            '3-tier': ['3 tier', 'web app', 'presentation'],
            'serverless': ['serverless', 'lambda', 'event driven'],
            'microservices': ['microservices', 'containers'],
            'production': ['production', 'prod', 'live']
        }
        
        for pattern, keywords in pattern_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                patterns.append(pattern)
        
        return patterns

    def _calculate_confidence(self, services, operations) -> float:
        """Calcular confiança da análise"""
        base_confidence = 0.3
        
        if services:
            base_confidence += 0.4
        if operations:
            base_confidence += 0.3
            
        return min(base_confidence, 1.0)
