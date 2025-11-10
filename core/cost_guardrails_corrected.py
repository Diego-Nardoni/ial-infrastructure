#!/usr/bin/env python3
"""
Cost Guardrails Corrected - Estimativa de custo ANTES do YAML
Corrige integração com IntentCostGuardrails existente
"""

from typing import Dict, Any

class CostGuardrailsCorrected:
    def __init__(self):
        """Inicializar IntentCostGuardrails existente"""
        try:
            from core.intent_cost_guardrails import IntentCostGuardrails
            self.cost_guardrails = IntentCostGuardrails()
            self.available = True
        except ImportError as e:
            print(f"⚠️ IntentCostGuardrails não disponível: {e}")
            self.cost_guardrails = None
            self.available = False
    
    def estimate_before_yaml(self, parsed_intent: Dict) -> Dict[str, Any]:
        """
        Estimar custo ANTES de gerar YAML - BLOQUEIA se exceder
        Corrige problemas de integração com IntentCostGuardrails
        """
        
        if not self.available:
            return {
                'estimated_cost': 5.0,  # Default estimate
                'budget_limit': 100.0,
                'exceeds_budget': False,
                'rationale': 'Cost Guardrails not available - using default estimate'
            }
        
        try:
            # 1. Extrair recursos da intenção
            resources = self.extract_resources_from_intent(parsed_intent)
            
            # 2. Calcular custo mensal estimado
            monthly_cost = self.calculate_monthly_cost(resources)
            
            # 3. Verificar budget limits
            budget_limit = self.get_budget_limit()
            
            # 4. DECISÃO: APPROVE ou BLOCK
            exceeds_budget = monthly_cost > budget_limit
            
            if exceeds_budget:
                self.log_budget_violation(parsed_intent, monthly_cost, budget_limit)
            
            return {
                'estimated_cost': monthly_cost,
                'budget_limit': budget_limit,
                'exceeds_budget': exceeds_budget,
                'cost_breakdown': self.get_cost_breakdown(resources),
                'recommendation': self.get_cost_optimization_recommendation(resources) if exceeds_budget else None,
                'rationale': f"Estimated ${monthly_cost:.2f}/month vs ${budget_limit:.2f} budget limit"
            }
            
        except Exception as e:
            print(f"⚠️ Cost Guardrails error: {e}")
            return {
                'estimated_cost': 5.0,
                'budget_limit': 100.0,
                'exceeds_budget': False,
                'rationale': f'Cost estimation error: {e} - using default'
            }
    
    def extract_resources_from_intent(self, parsed_intent: Dict) -> list:
        """Extrair recursos da intenção parseada"""
        resources = []
        
        # Obter serviços da intenção
        services = parsed_intent.get('services', ['unknown'])
        raw_intent = parsed_intent.get('raw', '').lower()
        
        # Mapear serviços para recursos com estimativas
        service_resources = {
            's3': {'type': 'S3::Bucket', 'base_cost': 5.0},
            'lambda': {'type': 'Lambda::Function', 'base_cost': 10.0},
            'dynamodb': {'type': 'DynamoDB::Table', 'base_cost': 15.0},
            'rds': {'type': 'RDS::DBInstance', 'base_cost': 50.0},
            'ec2': {'type': 'EC2::Instance', 'base_cost': 30.0},
            'sns': {'type': 'SNS::Topic', 'base_cost': 2.0},
            'api-gateway': {'type': 'ApiGateway::RestApi', 'base_cost': 8.0},
            'cloudfront': {'type': 'CloudFront::Distribution', 'base_cost': 12.0}
        }
        
        for service in services:
            if service in service_resources:
                resource = service_resources[service].copy()
                resource['service'] = service
                
                # Ajustar custo baseado em keywords
                if any(word in raw_intent for word in ['large', 'big', 'enterprise']):
                    resource['base_cost'] *= 2
                elif any(word in raw_intent for word in ['small', 'micro', 'test']):
                    resource['base_cost'] *= 0.5
                
                resources.append(resource)
        
        # Default resource se nenhum identificado
        if not resources:
            resources.append({'type': 'Unknown::Resource', 'service': 'unknown', 'base_cost': 5.0})
        
        return resources
    
    def calculate_monthly_cost(self, resources: list) -> float:
        """Calcular custo mensal total"""
        total_cost = 0.0
        
        for resource in resources:
            base_cost = resource.get('base_cost', 5.0)
            
            # Fatores multiplicadores
            if resource.get('service') == 'rds':
                # RDS tem custos adicionais (storage, backup)
                total_cost += base_cost * 1.5
            elif resource.get('service') == 'ec2':
                # EC2 24/7
                total_cost += base_cost * 1.2
            else:
                total_cost += base_cost
        
        return round(total_cost, 2)
    
    def get_budget_limit(self) -> float:
        """Obter limite de orçamento"""
        # TODO: Integrar com configuração real
        return 100.0  # $100/month default
    
    def get_cost_breakdown(self, resources: list) -> Dict[str, float]:
        """Obter breakdown de custos por serviço"""
        breakdown = {}
        
        for resource in resources:
            service = resource.get('service', 'unknown')
            cost = resource.get('base_cost', 5.0)
            
            if service in breakdown:
                breakdown[service] += cost
            else:
                breakdown[service] = cost
        
        return breakdown
    
    def get_cost_optimization_recommendation(self, resources: list) -> str:
        """Obter recomendação de otimização de custos"""
        recommendations = []
        
        for resource in resources:
            service = resource.get('service')
            cost = resource.get('base_cost', 0)
            
            if service == 'rds' and cost > 40:
                recommendations.append("Consider using Aurora Serverless for RDS")
            elif service == 'ec2' and cost > 25:
                recommendations.append("Consider using Lambda instead of EC2 for compute")
            elif service == 's3' and cost > 10:
                recommendations.append("Use S3 Intelligent Tiering for storage optimization")
        
        return "; ".join(recommendations) if recommendations else "No specific recommendations"
    
    def log_budget_violation(self, parsed_intent: Dict, cost: float, limit: float):
        """Log violação de orçamento"""
        print(f"💰 Budget violation: ${cost:.2f} exceeds ${limit:.2f} limit")
        print(f"📋 Intent: {parsed_intent.get('raw', 'unknown')[:50]}...")
