#!/usr/bin/env python3
"""
Pre-YAML Cost Guardrails
Estima custo ANTES de gerar YAML
"""

import json
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class CostEstimate:
    service: str
    resource_type: str
    quantity: int
    unit_cost: float
    monthly_cost: float
    billing_mode: str  # on-demand, reserved, spot, serverless


class CostGuardrails:
    """Estima custos ANTES de gerar YAML"""
    
    def __init__(self, monthly_budget: float = 500.0):
        self.monthly_budget = monthly_budget
        self.pricing = self._load_pricing_table()
    
    def _load_pricing_table(self) -> Dict[str, Dict]:
        """Tabela simplificada de preços AWS (us-east-1)"""
        return {
            "ec2": {
                "t3.micro": {"on_demand": 0.0104, "reserved": 0.0062},
                "t3.small": {"on_demand": 0.0208, "reserved": 0.0125},
                "t3.medium": {"on_demand": 0.0416, "reserved": 0.025},
                "m5.large": {"on_demand": 0.096, "reserved": 0.058}
            },
            "rds": {
                "db.t3.micro": {"on_demand": 0.017, "reserved": 0.010},
                "db.t3.small": {"on_demand": 0.034, "reserved": 0.020},
                "db.m5.large": {"on_demand": 0.192, "reserved": 0.115}
            },
            "elasticache": {
                "cache.t3.micro": {"on_demand": 0.017},
                "cache.t3.small": {"on_demand": 0.034},
                "cache.m5.large": {"on_demand": 0.188}
            }
        }
    
    def validate_deployment(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Valida se o deployment está dentro dos guardrails de custo"""
        
        estimated_cost = deployment.get('estimated_cost', 0.0)
        resources = deployment.get('resources', [])
        
        # Verificar se excede orçamento
        exceeds_budget = estimated_cost > self.monthly_budget
        
        # Verificar recursos proibidos
        prohibited_resources = self._check_prohibited_resources(resources)
        
        # Verificar recursos de alto custo
        high_cost_resources = self._check_high_cost_resources(resources)
        
        # Determinar aprovação
        reasons = []
        if exceeds_budget:
            reasons.append('budget_exceeded')
        if prohibited_resources:
            reasons.append('prohibited_resource')
        if high_cost_resources:
            reasons.append('high_cost_resource')
        
        approved = len(reasons) == 0
        
        return {
            'approved': approved,
            'estimated_cost': estimated_cost,
            'budget_limit': self.monthly_budget,
            'exceeds_budget': exceeds_budget,
            'prohibited_resources': prohibited_resources,
            'high_cost_resources': high_cost_resources,
            'reasons': reasons,
            'recommendations': self._get_cost_recommendations(resources, estimated_cost)
        }
    
    def _check_prohibited_resources(self, resources: List[str]) -> List[str]:
        """Verifica recursos proibidos por política de custo"""
        
        prohibited_patterns = [
            'p3.16xlarge',  # GPU instances caras
            'p4d.24xlarge',
            'x1e.32xlarge',  # Memory-optimized caras
            'r5.24xlarge',
            'c5n.18xlarge'  # Compute-optimized caras
        ]
        
        prohibited_found = []
        for resource in resources:
            for pattern in prohibited_patterns:
                if pattern in resource:
                    prohibited_found.append(resource)
        
        return prohibited_found
    
    def _check_high_cost_resources(self, resources: List[str]) -> List[str]:
        """Verifica recursos de alto custo que precisam de aprovação"""
        
        high_cost_patterns = [
            'xlarge',  # Instâncias grandes
            'gpu',     # Instâncias GPU
            'dedicated'  # Instâncias dedicadas
        ]
        
        high_cost_found = []
        for resource in resources:
            for pattern in high_cost_patterns:
                if pattern in resource.lower():
                    high_cost_found.append(resource)
        
        return high_cost_found
    
    def _get_cost_recommendations(self, resources: List[str], estimated_cost: float) -> List[str]:
        """Fornece recomendações para otimização de custo"""
        
        recommendations = []
        
        if estimated_cost > self.monthly_budget * 0.8:
            recommendations.append("Consider using Reserved Instances for 40-60% cost savings")
            recommendations.append("Evaluate if Spot Instances can be used for non-critical workloads")
        
        if any('large' in resource for resource in resources):
            recommendations.append("Consider starting with smaller instance types and scaling up as needed")
        
        if any('rds' in resource.lower() for resource in resources):
            recommendations.append("Consider Aurora Serverless for variable workloads")
        
        if any('s3' in resource.lower() for resource in resources):
            recommendations.append("Use S3 Intelligent Tiering for automatic cost optimization")
        
        return recommendations
    
    def estimate_from_intent(self, nl_intent: str) -> Dict[str, Any]:
        """
        Estima custo baseado em intenção NL
        
        Returns:
            {
                "estimates": List[CostEstimate],
                "total_monthly_cost": float,
                "within_budget": bool,
                "budget_usage_percent": float,
                "alternatives": List[str]
            }
        """
        estimates = []
        nl_lower = nl_intent.lower()
        
        # Detect EC2
        if "ec2" in nl_lower or "instância" in nl_lower:
            instance_type = self._detect_instance_type(nl_lower, "ec2")
            billing = "reserved" if "reserved" in nl_lower else "on_demand"
            
            hourly_cost = self.pricing["ec2"][instance_type][billing]
            monthly_cost = hourly_cost * 730  # 730 hours/month
            
            estimates.append(CostEstimate(
                service="EC2",
                resource_type=instance_type,
                quantity=1,
                unit_cost=hourly_cost,
                monthly_cost=monthly_cost,
                billing_mode=billing
            ))
        
        # Detect RDS
        if "rds" in nl_lower or "database" in nl_lower or "postgres" in nl_lower or "mysql" in nl_lower:
            instance_type = self._detect_instance_type(nl_lower, "rds")
            billing = "reserved" if "reserved" in nl_lower else "on_demand"
            
            hourly_cost = self.pricing["rds"][instance_type][billing]
            monthly_cost = hourly_cost * 730
            
            estimates.append(CostEstimate(
                service="RDS",
                resource_type=instance_type,
                quantity=1,
                unit_cost=hourly_cost,
                monthly_cost=monthly_cost,
                billing_mode=billing
            ))
        
        # Detect ElastiCache
        if "redis" in nl_lower or "elasticache" in nl_lower or "memcached" in nl_lower:
            instance_type = self._detect_instance_type(nl_lower, "elasticache")
            
            hourly_cost = self.pricing["elasticache"][instance_type]["on_demand"]
            monthly_cost = hourly_cost * 730
            
            estimates.append(CostEstimate(
                service="ElastiCache",
                resource_type=instance_type,
                quantity=1,
                unit_cost=hourly_cost,
                monthly_cost=monthly_cost,
                billing_mode="on_demand"
            ))
        
        # Detect S3
        if "s3" in nl_lower or "bucket" in nl_lower:
            storage_gb = 100  # Default 100GB
            monthly_cost = storage_gb * self.pricing["s3"]["standard"]["per_gb"]
            
            estimates.append(CostEstimate(
                service="S3",
                resource_type="Standard Storage",
                quantity=storage_gb,
                unit_cost=self.pricing["s3"]["standard"]["per_gb"],
                monthly_cost=monthly_cost,
                billing_mode="pay_as_you_go"
            ))
        
        # Detect ALB
        if "alb" in nl_lower or "load balancer" in nl_lower:
            hourly_cost = self.pricing["alb"]["hourly"]
            monthly_cost = hourly_cost * 730
            
            estimates.append(CostEstimate(
                service="ALB",
                resource_type="Application Load Balancer",
                quantity=1,
                unit_cost=hourly_cost,
                monthly_cost=monthly_cost,
                billing_mode="hourly"
            ))
        
        # Detect NAT Gateway
        if "nat" in nl_lower or "gateway" in nl_lower:
            hourly_cost = self.pricing["nat_gateway"]["hourly"]
            monthly_cost = hourly_cost * 730
            
            estimates.append(CostEstimate(
                service="NAT Gateway",
                resource_type="NAT Gateway",
                quantity=1,
                unit_cost=hourly_cost,
                monthly_cost=monthly_cost,
                billing_mode="hourly"
            ))
        
        # Calculate totals
        total_monthly_cost = sum(e.monthly_cost for e in estimates)
        within_budget = total_monthly_cost <= self.monthly_budget
        budget_usage = (total_monthly_cost / self.monthly_budget) * 100
        
        # Generate alternatives if over budget
        alternatives = []
        if not within_budget:
            alternatives = self._generate_alternatives(estimates)
        
        return {
            "estimates": [
                {
                    "service": e.service,
                    "resource_type": e.resource_type,
                    "quantity": e.quantity,
                    "monthly_cost": round(e.monthly_cost, 2),
                    "billing_mode": e.billing_mode
                }
                for e in estimates
            ],
            "total_monthly_cost": round(total_monthly_cost, 2),
            "within_budget": within_budget,
            "budget_usage_percent": round(budget_usage, 1),
            "monthly_budget": self.monthly_budget,
            "alternatives": alternatives
        }
    
    def _detect_instance_type(self, nl_lower: str, service: str) -> str:
        """Detecta tipo de instância baseado em keywords"""
        if "large" in nl_lower:
            return f"{'db.' if service == 'rds' else 'cache.' if service == 'elasticache' else ''}m5.large"
        elif "medium" in nl_lower:
            return "t3.medium"
        elif "small" in nl_lower:
            return f"{'db.' if service == 'rds' else 'cache.' if service == 'elasticache' else ''}t3.small"
        else:
            return f"{'db.' if service == 'rds' else 'cache.' if service == 'elasticache' else ''}t3.micro"
    
    def _generate_alternatives(self, estimates: List[CostEstimate]) -> List[str]:
        """Gera alternativas para reduzir custo"""
        alternatives = []
        
        for est in estimates:
            if est.service == "EC2" and est.billing_mode == "on_demand":
                alternatives.append(f"💡 Use Reserved Instances para {est.service} (economia de ~40%)")
            
            if est.service == "RDS" and "large" in est.resource_type:
                alternatives.append(f"💡 Considere instância menor para {est.service} (db.t3.small)")
            
            if est.service == "NAT Gateway":
                alternatives.append("💡 Use NAT Instance (t3.micro) em vez de NAT Gateway (economia de ~70%)")
        
        return alternatives
