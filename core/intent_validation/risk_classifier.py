"""
Risk Classifier - Classifica riscos baseado em serviços e operações
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict
from .intent_parser import ParsedIntent, OperationType

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RiskAssessment:
    level: RiskLevel
    score: float
    reasons: List[str]
    recommendations: List[str]

class RiskClassifier:
    def __init__(self):
        # Mapeamento de serviços por nível de risco
        self.service_risk_mapping = {
            # Serviços de alto risco
            'rds': RiskLevel.HIGH,
            'dynamodb': RiskLevel.HIGH,
            'iam': RiskLevel.CRITICAL,
            'kms': RiskLevel.CRITICAL,
            
            # Serviços de médio risco
            'ecs': RiskLevel.MEDIUM,
            'lambda': RiskLevel.MEDIUM,
            'elb': RiskLevel.MEDIUM,
            's3': RiskLevel.MEDIUM,
            
            # Serviços de baixo risco
            'cloudwatch': RiskLevel.LOW,
            'sns': RiskLevel.LOW
        }
        
        # Operações de alto risco
        self.high_risk_operations = [OperationType.DELETE, OperationType.UPDATE]
        
        # Padrões de alto risco
        self.high_risk_patterns = ['production', 'prod']

    def classify_risk(self, intent: ParsedIntent) -> RiskAssessment:
        """Classifica o risco da intenção"""
        
        risk_factors = []
        recommendations = []
        base_score = 0.0
        
        # Avaliar serviços
        max_service_risk = RiskLevel.LOW
        for service in intent.aws_services:
            service_risk = self.service_risk_mapping.get(service, RiskLevel.LOW)
            if self._risk_level_to_score(service_risk) > self._risk_level_to_score(max_service_risk):
                max_service_risk = service_risk
                risk_factors.append(f"Serviço {service} é classificado como {service_risk.value}")
        
        base_score = self._risk_level_to_score(max_service_risk)
        
        # Avaliar operações
        for operation in intent.operations:
            if operation in self.high_risk_operations:
                base_score += 0.3
                risk_factors.append(f"Operação {operation.value} é potencialmente destrutiva")
                recommendations.append("Considere fazer backup antes de operações destrutivas")
        
        # Avaliar padrões
        for pattern in intent.detected_patterns:
            if pattern in self.high_risk_patterns:
                base_score += 0.4
                risk_factors.append(f"Ambiente {pattern} detectado")
                recommendations.append("Recursos de produção requerem aprovação adicional")
        
        # Determinar nível final
        final_level = self._score_to_risk_level(min(base_score, 1.0))
        
        # Adicionar recomendações padrão
        if final_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Revisar políticas de segurança antes de prosseguir")
        
        return RiskAssessment(
            level=final_level,
            score=min(base_score, 1.0),
            reasons=risk_factors,
            recommendations=recommendations
        )

    def _risk_level_to_score(self, level: RiskLevel) -> float:
        """Converte nível de risco para score"""
        mapping = {
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 1.0
        }
        return mapping.get(level, 0.2)

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Converte score para nível de risco"""
        if score >= 0.9:
            return RiskLevel.CRITICAL
        elif score >= 0.7:
            return RiskLevel.HIGH
        elif score >= 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
