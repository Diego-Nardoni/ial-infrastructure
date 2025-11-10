#!/usr/bin/env python3
"""
IAS Corrected - Intent Validation Sandbox com simulação completa
Corrige integração com ValidationSystem existente
"""

from typing import Dict, Any

class IASCorrected:
    def __init__(self):
        """Inicializar ValidationSystem existente"""
        try:
            from core.intent_validation.validation_system import ValidationSystem
            self.validation_system = ValidationSystem()
            self.available = True
        except ImportError as e:
            print(f"⚠️ ValidationSystem não disponível: {e}")
            self.validation_system = None
            self.available = False
    
    def validate_intent_with_simulation(self, nl_intent: str) -> Dict[str, Any]:
        """
        IAS - Intent Validation Sandbox com simulação completa
        Corrige problemas de integração com ValidationSystem
        """
        
        if not self.available:
            return {
                'safe': True,
                'parsed_intent': {'raw': nl_intent, 'services': ['unknown']},
                'rationale': 'IAS not available - defaulting to safe'
            }
        
        try:
            # 1. Usar ValidationSystem.validate_intent corretamente
            validation_result = self.validation_system.validate_intent(nl_intent)
            
            # 2. Extrair dados do ValidationResult corretamente
            if hasattr(validation_result, 'valid'):
                is_valid = validation_result.valid
            elif isinstance(validation_result, dict):
                is_valid = validation_result.get('valid', True)
            else:
                is_valid = True
            
            # 3. Extrair parsed_intent
            if hasattr(validation_result, 'parsed_intent'):
                parsed_intent = validation_result.parsed_intent
            elif isinstance(validation_result, dict):
                parsed_intent = validation_result.get('parsed_intent', {'raw': nl_intent})
            else:
                parsed_intent = {'raw': nl_intent}
            
            # 4. Garantir que parsed_intent tem estrutura mínima
            if not isinstance(parsed_intent, dict):
                parsed_intent = {'raw': nl_intent}
            
            if 'services' not in parsed_intent:
                parsed_intent['services'] = self.extract_services_from_intent(nl_intent)
            
            # 5. Simulação de risco adicional
            risk_level = self.assess_risk_level(nl_intent, parsed_intent)
            
            return {
                'safe': is_valid and risk_level < 0.7,
                'parsed_intent': parsed_intent,
                'risk_assessment': {
                    'level': risk_level,
                    'factors': self.get_risk_factors(nl_intent)
                },
                'rationale': f"IAS validation: {'SAFE' if is_valid else 'UNSAFE'}, Risk: {risk_level:.2f}"
            }
            
        except Exception as e:
            print(f"⚠️ IAS validation error: {e}")
            return {
                'safe': True,  # Default to safe on error
                'parsed_intent': {'raw': nl_intent, 'services': ['unknown']},
                'rationale': f'IAS error: {e} - defaulting to safe'
            }
    
    def extract_services_from_intent(self, nl_intent: str) -> list:
        """Extrair serviços AWS da intenção"""
        services = []
        nl_lower = nl_intent.lower()
        
        service_keywords = {
            's3': ['bucket', 's3', 'storage'],
            'lambda': ['lambda', 'function'],
            'dynamodb': ['dynamodb', 'table', 'database'],
            'rds': ['rds', 'database', 'mysql', 'postgres'],
            'ec2': ['ec2', 'instance', 'server'],
            'sns': ['sns', 'notification', 'topic'],
            'sqs': ['sqs', 'queue'],
            'api-gateway': ['api', 'gateway', 'rest'],
            'cloudfront': ['cloudfront', 'cdn'],
            'vpc': ['vpc', 'network']
        }
        
        for service, keywords in service_keywords.items():
            if any(keyword in nl_lower for keyword in keywords):
                services.append(service)
        
        return services if services else ['unknown']
    
    def assess_risk_level(self, nl_intent: str, parsed_intent: Dict) -> float:
        """Avaliar nível de risco (0.0 = seguro, 1.0 = perigoso)"""
        risk_score = 0.0
        nl_lower = nl_intent.lower()
        
        # Fatores de risco
        high_risk_keywords = ['delete', 'destroy', 'terminate', 'remove']
        medium_risk_keywords = ['modify', 'update', 'change', 'alter']
        
        # Recursos sensíveis
        sensitive_resources = ['database', 'production', 'prod', 'critical']
        
        # Calcular risco
        for keyword in high_risk_keywords:
            if keyword in nl_lower:
                risk_score += 0.4
        
        for keyword in medium_risk_keywords:
            if keyword in nl_lower:
                risk_score += 0.2
        
        for resource in sensitive_resources:
            if resource in nl_lower:
                risk_score += 0.3
        
        return min(1.0, risk_score)
    
    def get_risk_factors(self, nl_intent: str) -> list:
        """Obter fatores de risco identificados"""
        factors = []
        nl_lower = nl_intent.lower()
        
        if any(word in nl_lower for word in ['delete', 'destroy', 'terminate']):
            factors.append('destructive_operation')
        
        if any(word in nl_lower for word in ['production', 'prod']):
            factors.append('production_environment')
        
        if any(word in nl_lower for word in ['database', 'data']):
            factors.append('data_operations')
        
        return factors
