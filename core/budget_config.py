#!/usr/bin/env python3
"""
Budget Configuration - Limites por phase
"""

from typing import Dict

class BudgetConfig:
    """Configuração de limites de budget por phase"""
    
    def __init__(self):
        # Default budget limits per phase (USD/month)
        self.phase_limits = {
            '00-foundation': 50.0,      # DynamoDB, S3, Lambda básico
            '10-security': 30.0,        # Security services (~$24 + overhead)
            '20-network': 20.0,         # VPC, subnets, NAT gateway
            '30-compute': 100.0,        # EC2, ECS, ALB
            '40-data': 80.0,           # RDS, DynamoDB workload tables
            '50-application': 60.0,     # Lambda, API Gateway, SQS
            '60-observability': 40.0,   # CloudWatch, X-Ray
            '70-ai-ml': 150.0,         # Bedrock, SageMaker
            '90-governance': 10.0       # Budgets, Config rules
        }
        
        # Total project budget
        self.total_budget = sum(self.phase_limits.values())  # $540/month
    
    def get_phase_limit(self, phase: str) -> float:
        """Get budget limit for a specific phase"""
        # Extract phase number/name
        phase_key = self._normalize_phase_name(phase)
        return self.phase_limits.get(phase_key, 50.0)  # Default $50
    
    def _normalize_phase_name(self, phase: str) -> str:
        """Normalize phase name to match config keys"""
        # Handle different formats: "30-compute", "compute", "30"
        if '-' in phase:
            return phase  # Already in correct format
        elif phase.isdigit():
            # Map phase numbers to names
            phase_map = {
                '00': '00-foundation',
                '10': '10-security', 
                '20': '20-network',
                '30': '30-compute',
                '40': '40-data',
                '50': '50-application',
                '60': '60-observability',
                '70': '70-ai-ml',
                '90': '90-governance'
            }
            return phase_map.get(phase, f"{phase}-unknown")
        else:
            # Try to find by name
            for key in self.phase_limits.keys():
                if phase.lower() in key.lower():
                    return key
            return f"unknown-{phase}"
    
    def get_all_limits(self) -> Dict[str, float]:
        """Get all phase limits"""
        return self.phase_limits.copy()
    
    def update_phase_limit(self, phase: str, limit: float):
        """Update budget limit for a phase"""
        phase_key = self._normalize_phase_name(phase)
        self.phase_limits[phase_key] = limit
        self.total_budget = sum(self.phase_limits.values())

# Global instance
budget_config = BudgetConfig()
