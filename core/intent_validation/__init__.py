"""
Sistema de Validação de Intenção para IAL
Integração não-disruptiva com sistema existente
"""

from .validation_system import ValidationSystem
from .intent_parser import IntentParser, ParsedIntent
from .risk_classifier import RiskClassifier, RiskLevel
from .policy_engine import PolicyEngine, ValidationResult

__all__ = [
    'ValidationSystem',
    'IntentParser', 
    'ParsedIntent',
    'RiskClassifier',
    'RiskLevel', 
    'PolicyEngine',
    'ValidationResult'
]
