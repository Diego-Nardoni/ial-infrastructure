"""
Policy Engine - Aplica políticas de validação configuráveis
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Optional
from .intent_parser import ParsedIntent
from .risk_classifier import RiskAssessment, RiskLevel

@dataclass
class ValidationResult:
    should_block: bool
    has_warnings: bool
    warnings: List[str]
    block_message: str
    recommendations: List[str]
    policy_applied: str
    
    # NOVOS CAMPOS para Cost Guardrails
    estimated_cost: Optional[float] = None
    cost_breakdown: Optional[Dict[str, float]] = None
    budget_exceeded: bool = False
    cost_estimation_used: bool = False

class PolicyEngine:
    def __init__(self):
        # Configurações padrão (Fase 2 - Avisos habilitados)
        self.warnings_enabled = os.getenv('IAL_VALIDATION_WARNINGS_ENABLED', 'true').lower() == 'true'
        self.enforcement_enabled = os.getenv('IAL_VALIDATION_ENFORCEMENT_ENABLED', 'false').lower() == 'true'
        
        # Políticas padrão
        self.default_policies = {
            'production_resources': {
                'risk_threshold': RiskLevel.HIGH,
                'warning_message': "⚠️ Recursos de produção detectados. Certifique-se de seguir práticas de segurança.",
                'block_message': "🚫 Criação de recursos de produção requer aprovação.",
                'enforcement': False
            },
            'destructive_operations': {
                'risk_threshold': RiskLevel.CRITICAL,
                'warning_message': "🚨 Operação destrutiva detectada. Esta ação pode causar perda de dados.",
                'block_message': "🚫 Operações destrutivas em produção são bloqueadas.",
                'enforcement': True
            },
            'security_services': {
                'risk_threshold': RiskLevel.CRITICAL,
                'warning_message': "🔐 Modificações de segurança detectadas. Revisar políticas de acesso.",
                'block_message': "🚫 Modificações de segurança requerem aprovação de administrador.",
                'enforcement': False
            }
        }

    def validate_intent(self, intent: ParsedIntent, risk: RiskAssessment) -> ValidationResult:
        """Valida intenção aplicando políticas"""
        
        warnings = []
        should_block = False
        block_message = ""
        recommendations = list(risk.recommendations)
        applied_policies = []
        
        # Aplicar políticas baseadas no risco
        for policy_name, policy_config in self.default_policies.items():
            if self._should_apply_policy(intent, risk, policy_config):
                applied_policies.append(policy_name)
                
                if self.warnings_enabled:
                    warnings.append(policy_config['warning_message'])
                
                if self.enforcement_enabled and policy_config.get('enforcement', False):
                    should_block = True
                    block_message = policy_config['block_message']
                    break  # Primeira política de bloqueio para
        
        # Adicionar recomendações específicas
        if risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.extend([
                "Considere executar em ambiente de teste primeiro",
                "Documente as mudanças para auditoria"
            ])
        
        return ValidationResult(
            should_block=should_block,
            has_warnings=len(warnings) > 0,
            warnings=warnings,
            block_message=block_message,
            recommendations=recommendations,
            policy_applied=", ".join(applied_policies) if applied_policies else "none"
        )

    def _should_apply_policy(self, intent: ParsedIntent, risk: RiskAssessment, policy_config: Dict) -> bool:
        """Determina se política deve ser aplicada"""
        
        # Verificar threshold de risco
        policy_threshold = policy_config.get('risk_threshold', RiskLevel.LOW)
        if self._risk_level_to_int(risk.level) < self._risk_level_to_int(policy_threshold):
            return False
        
        # Verificar padrões específicos
        if 'production' in intent.detected_patterns and 'production_resources' in policy_config:
            return True
        
        if any(op.value in ['delete', 'destroy'] for op in intent.operations) and 'destructive' in str(policy_config):
            return True
        
        if any(service in ['iam', 'kms'] for service in intent.aws_services) and 'security' in str(policy_config):
            return True
        
        return True  # Aplicar por padrão se threshold atendido

    def _risk_level_to_int(self, level: RiskLevel) -> int:
        """Converte RiskLevel para int para comparação"""
        mapping = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        return mapping.get(level, 1)
