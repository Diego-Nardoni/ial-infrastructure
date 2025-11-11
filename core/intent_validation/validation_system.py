"""
Validation System - Sistema principal de validação de intenção
Integra todos os componentes e fornece interface limpa para o IAL
"""

import sys
import os
import time
from typing import Dict, Optional

# Import DecisionLedger existente
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from decision_ledger import DecisionLedger

# Imports locais com fallback
try:
    from intent_parser import IntentParser, ParsedIntent
    from risk_classifier import RiskClassifier, RiskAssessment
    from policy_engine import PolicyEngine, ValidationResult
except ImportError:
    # Fallback para imports absolutos
    from .intent_parser import IntentParser, ParsedIntent
    from .risk_classifier import RiskClassifier, RiskAssessment
    from .policy_engine import PolicyEngine, ValidationResult

class ValidationSystem:
    def __init__(self):
        # Componentes principais
        self.intent_parser = IntentParser()
        self.risk_classifier = RiskClassifier()
        self.policy_engine = PolicyEngine()
        
        # Reutilizar DecisionLedger existente
        self.decision_ledger = DecisionLedger()
        
        # NOVO: Integrar Cost Guardrails
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from intent_cost_guardrails import IntentCostGuardrails
            self.cost_guardrails = IntentCostGuardrails()
            self.cost_guardrails_available = True
            #print("✅ Cost Guardrails integrado ao ValidationSystem")
        except ImportError as e:
            print(f"⚠️ Cost Guardrails não disponível: {e}")
            self.cost_guardrails = None
            self.cost_guardrails_available = False
        
        # Configurações
        self.enabled = os.getenv('IAL_VALIDATION_ENABLED', 'true').lower() == 'true'
        self.max_processing_time = 5.0  # 5 segundos máximo
        
        #print("✅ Sistema de Validação de Intenção inicializado")

    def validate_intent(self, user_input: str, context: Optional[Dict] = None) -> ValidationResult:
        """
        Ponto de entrada principal para validação de intenção
        Interface limpa para integração com IAL
        """
        
        if not self.enabled:
            return self._create_passthrough_result()
        
        start_time = time.time()
        
        try:
            # 1. Parse da intenção
            intent = self.intent_parser.parse_intent(user_input)
            
            # 2. Classificação de risco
            risk = self.risk_classifier.classify_risk(intent)
            
            # 3. Aplicação de políticas
            validation_result = self.policy_engine.validate_intent(intent, risk)
            
            # 4. NOVO: Validação de custo (se disponível)
            if self.cost_guardrails_available and self.cost_guardrails:
                try:
                    cost_result = self.cost_guardrails.validate_cost(user_input, context)
                    
                    # Integrar resultado de custo no validation_result
                    validation_result.estimated_cost = cost_result.estimated_cost
                    validation_result.cost_breakdown = cost_result.cost_breakdown
                    validation_result.budget_exceeded = cost_result.should_block
                    validation_result.cost_estimation_used = cost_result.estimated_cost is not None
                    
                    # Se cost guardrails determina bloqueio, sobrescrever
                    if cost_result.should_block:
                        validation_result.should_block = True
                        validation_result.block_message = cost_result.block_message
                        
                except Exception as e:
                    print(f"⚠️ Erro na validação de custo: {e}")
                    # Continuar sem cost validation
            
            # 5. Log da decisão
            processing_time = time.time() - start_time
            self._log_validation_decision(intent, risk, validation_result, processing_time, context)
            
            return validation_result
            
        except Exception as e:
            # Fallback silencioso - não quebrar sistema existente
            self._log_validation_error(user_input, str(e), context)
            return self._create_passthrough_result()

    def _create_passthrough_result(self) -> ValidationResult:
        """Cria resultado que permite passagem sem validação"""
        return ValidationResult(
            should_block=False,
            has_warnings=False,
            warnings=[],
            block_message="",
            recommendations=[],
            policy_applied="passthrough",
            # Novos campos de custo
            estimated_cost=None,
            cost_breakdown=None,
            budget_exceeded=False,
            cost_estimation_used=False
        )

    def _log_validation_decision(self, intent: ParsedIntent, risk: RiskAssessment, 
                               result: ValidationResult, processing_time: float, 
                               context: Optional[Dict]):
        """Log da decisão de validação usando DecisionLedger existente"""
        
        metadata = {
            'intent_confidence': intent.confidence,
            'risk_level': risk.level.value,
            'risk_score': risk.score,
            'services_detected': intent.aws_services,
            'operations_detected': [op.value for op in intent.operations],
            'patterns_detected': intent.detected_patterns,
            'processing_time_ms': int(processing_time * 1000),
            'warnings_count': len(result.warnings),
            'blocked': result.should_block,
            'policy_applied': result.policy_applied
        }
        
        if context:
            metadata.update({
                'user_id': context.get('user_id', 'unknown'),
                'session_id': context.get('session_id', 'unknown')
            })
        
        status = "blocked" if result.should_block else "allowed"
        if result.has_warnings:
            status += "_with_warnings"
        
        self.decision_ledger.log(
            phase="intent-validation",
            mcp="validation-system", 
            tool="validate_intent",
            rationale=f"Risk: {risk.level.value}, Policy: {result.policy_applied}",
            status=status,
            metadata=metadata
        )

    def _log_validation_error(self, user_input: str, error: str, context: Optional[Dict]):
        """Log de erro na validação"""
        
        metadata = {
            'error': error,
            'input_length': len(user_input),
            'fallback_used': True
        }
        
        if context:
            metadata.update({
                'user_id': context.get('user_id', 'unknown'),
                'session_id': context.get('session_id', 'unknown')
            })
        
        self.decision_ledger.log(
            phase="intent-validation",
            mcp="validation-system",
            tool="validate_intent", 
            rationale=f"Validation failed: {error}",
            status="error_fallback",
            metadata=metadata
        )

    def get_system_status(self) -> Dict:
        """Retorna status do sistema de validação"""
        return {
            'enabled': self.enabled,
            'warnings_enabled': self.policy_engine.warnings_enabled,
            'enforcement_enabled': self.policy_engine.enforcement_enabled,
            'components': {
                'intent_parser': 'active',
                'risk_classifier': 'active', 
                'policy_engine': 'active',
                'decision_ledger': 'integrated'
            }
        }
