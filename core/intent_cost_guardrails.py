#!/usr/bin/env python3
"""
Intent Cost Guardrails - Pre-YAML Cost Validation
Estima custos ANTES da geração de YAML usando MCPs FinOps existentes
Estratégia: Estimativa habilitada por padrão + Enforcement opt-in
"""

import os
import sys
import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Add core path for imports
sys.path.append(os.path.dirname(__file__))

# Import Decision Ledger existente
try:
    from decision_ledger import DecisionLedger
except ImportError:
    # Fallback se não conseguir importar
    class DecisionLedger:
        def log(self, **kwargs):
            print(f"📝 Decision Log: {kwargs}")

@dataclass
class CostValidationResult:
    """Resultado da validação de custo"""
    estimated_cost: Optional[float] = None
    cost_breakdown: Dict[str, float] = field(default_factory=dict)
    should_block: bool = False
    block_message: str = ""
    cache_hit: bool = False
    processing_time_ms: int = 0
    services_detected: List[str] = field(default_factory=list)

@dataclass
class CostConfig:
    """Configuração do sistema de custos"""
    estimation_enabled: bool = True
    enforcement_enabled: bool = False
    default_budget: float = 150.0
    cache_ttl_minutes: int = 60
    timeout_seconds: int = 3
    show_breakdown: bool = True

class IntentCostGuardrails:
    """
    Componente principal para validação de custos antes da geração de YAML
    """
    
    def __init__(self):
        self.config = self._load_config()
        self.cache = {}  # Cache simples de preços
        self.decision_ledger = DecisionLedger()
        
        # Padrões para detectar serviços AWS
        self.service_patterns = {
            'ecs': ['ecs', 'container', 'fargate', 'cluster', 'task', 'service'],
            'rds': ['rds', 'database', 'mysql', 'postgres', 'aurora', 'db'],
            'redis': ['redis', 'elasticache', 'cache', 'memcached'],
            'elb': ['elb', 'alb', 'nlb', 'load balancer', 'balancer', 'lb'],
            's3': ['s3', 'bucket', 'storage', 'object'],
            'lambda': ['lambda', 'function', 'serverless'],
            'dynamodb': ['dynamodb', 'nosql', 'table', 'item'],
            'vpc': ['vpc', 'network', 'subnet', 'security group'],
            'apigateway': ['api gateway', 'api', 'rest', 'http', 'endpoint']
        }
        
        # Preços heurísticos para fallback (USD/mês)
        self.fallback_prices = {
            'ecs': 45.0,
            'rds': 65.0, 
            'redis': 25.0,
            'elb': 20.0,
            's3': 5.0,
            'lambda': 10.0,
            'dynamodb': 15.0,
            'vpc': 0.0,  # VPC básico é gratuito
            'apigateway': 12.0
        }
        
        print("💰 Intent Cost Guardrails inicializado")
    
    def estimate_intent_cost(self, parsed_intent: Dict) -> float:
        """
        CORREÇÃO: Método faltante para estimativa de custo
        
        Args:
            parsed_intent: Intent parseado pelo IAS
            
        Returns:
            float: Custo estimado em USD/mês
        """
        try:
            # Extrair serviços do intent parseado
            services = []
            
            if isinstance(parsed_intent, dict):
                # Tentar extrair serviços de diferentes campos
                if 'services' in parsed_intent:
                    services = parsed_intent['services']
                elif 'resources' in parsed_intent:
                    services = [r.get('type', '').lower() for r in parsed_intent['resources']]
                elif 'raw' in parsed_intent:
                    services = self._detect_services(parsed_intent['raw'])
                else:
                    # Fallback: detectar serviços do intent completo
                    intent_str = str(parsed_intent)
                    services = self._detect_services(intent_str)
            else:
                # Se não for dict, tentar como string
                services = self._detect_services(str(parsed_intent))
            
            if not services:
                return 0.0
            
            # Estimar custo dos serviços detectados
            estimated_cost, _ = self._estimate_cost(services)
            return estimated_cost
            
        except Exception as e:
            print(f"⚠️ Erro estimando custo: {e}")
            return 0.0

    def validate_cost(self, intent: str, context: Optional[Dict] = None) -> CostValidationResult:
        """
        Ponto de entrada principal para validação de custo
        
        Args:
            intent: Intenção do usuário em linguagem natural
            context: Contexto adicional (user_id, session_id, etc.)
            
        Returns:
            CostValidationResult com estimativa e decisão de bloqueio
        """
        start_time = time.time()
        
        # Se estimativa desabilitada, retorna resultado vazio
        if not self.config.estimation_enabled:
            return CostValidationResult()
        
        try:
            # 1. Detectar serviços AWS na intenção
            services = self._detect_services(intent)
            
            if not services:
                return CostValidationResult()  # Nenhum serviço detectado
            
            # 2. Estimar custo dos serviços
            estimated_cost, breakdown = self._estimate_cost(services)
            
            # 3. Verificar se deve bloquear (só se enforcement habilitado)
            should_block = False
            block_message = ""
            
            if self.config.enforcement_enabled and estimated_cost > self.config.default_budget:
                should_block = True
                block_message = (
                    f"⚠️ Custo estimado ${estimated_cost:.2f}/mês excede o budget "
                    f"configurado (${self.config.default_budget:.2f}/mês).\n"
                    f"Deseja continuar mesmo assim? (sim/não)"
                )
            
            # 4. Criar resultado
            processing_time = int((time.time() - start_time) * 1000)
            
            result = CostValidationResult(
                estimated_cost=estimated_cost,
                cost_breakdown=breakdown,
                should_block=should_block,
                block_message=block_message,
                cache_hit=False,  # TODO: implementar cache
                processing_time_ms=processing_time,
                services_detected=services
            )
            
            # 5. Log da decisão
            self._log_cost_validation(intent, result, context)
            
            return result
            
        except Exception as e:
            # Fallback silencioso - nunca quebrar o sistema
            print(f"⚠️ Erro na validação de custo: {e}")
            self._log_cost_error(intent, str(e), context)
            return CostValidationResult()
    
    def _detect_services(self, intent: str) -> List[str]:
        """Detecta serviços AWS mencionados na intenção"""
        intent_lower = intent.lower()
        detected_services = []
        
        for service, patterns in self.service_patterns.items():
            if any(pattern in intent_lower for pattern in patterns):
                detected_services.append(service)
        
        return detected_services
    
    def _estimate_cost(self, services: List[str]) -> Tuple[float, Dict[str, float]]:
        """
        Estima custo dos serviços
        
        Estratégia:
        1. Tentar usar MCP de pricing (TODO: implementar)
        2. Fallback para preços heurísticos
        """
        
        total_cost = 0.0
        breakdown = {}
        
        for service in services:
            # Por enquanto usar fallback, depois integrar com MCP
            service_cost = self._get_service_price_fallback(service)
            
            if service_cost > 0:
                total_cost += service_cost
                breakdown[service.upper()] = service_cost
        
        return total_cost, breakdown
    
    def _get_service_price_fallback(self, service: str) -> float:
        """Obtém preço usando heurística (fallback)"""
        return self.fallback_prices.get(service, 0.0)
    
    def _load_config(self) -> CostConfig:
        """Carrega configuração do arquivo ial-config.yaml"""
        
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ial-config.yaml')
        
        # Valores padrão
        defaults = {
            'estimation_enabled': True,
            'enforcement_enabled': False,
            'default_budget': 150.0,
            'cache_ttl_minutes': 60,
            'timeout_seconds': 3,
            'show_breakdown': True
        }
        
        try:
            # Tentar carregar YAML
            import yaml
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                cost_config = config_data.get('cost_guardrails', {})
                estimation = cost_config.get('estimation', {})
                enforcement = cost_config.get('enforcement', {})
                
                return CostConfig(
                    estimation_enabled=estimation.get('enabled', defaults['estimation_enabled']),
                    enforcement_enabled=enforcement.get('enabled', defaults['enforcement_enabled']),
                    default_budget=float(enforcement.get('default_monthly_budget_usd', defaults['default_budget'])),
                    cache_ttl_minutes=int(estimation.get('cache_ttl_minutes', defaults['cache_ttl_minutes'])),
                    timeout_seconds=int(estimation.get('timeout_seconds', defaults['timeout_seconds'])),
                    show_breakdown=estimation.get('show_breakdown', defaults['show_breakdown'])
                )
        except Exception as e:
            print(f"⚠️ Erro carregando config, usando padrões: {e}")
        
        # Fallback para env vars e depois padrões
        return CostConfig(
            estimation_enabled=os.getenv('COST_ESTIMATION_ENABLED', str(defaults['estimation_enabled'])).lower() == 'true',
            enforcement_enabled=os.getenv('COST_ENFORCEMENT_ENABLED', str(defaults['enforcement_enabled'])).lower() == 'true',
            default_budget=float(os.getenv('DEFAULT_BUDGET', str(defaults['default_budget']))),
            cache_ttl_minutes=int(os.getenv('CACHE_TTL_MINUTES', str(defaults['cache_ttl_minutes']))),
            timeout_seconds=int(os.getenv('TIMEOUT_SECONDS', str(defaults['timeout_seconds']))),
            show_breakdown=os.getenv('SHOW_COST_BREAKDOWN', str(defaults['show_breakdown'])).lower() == 'true'
        )
    
    def _log_cost_validation(self, intent: str, result: CostValidationResult, context: Optional[Dict]):
        """Log da validação de custo usando Decision Ledger existente"""
        
        metadata = {
            'estimated_cost': result.estimated_cost,
            'services_detected': result.services_detected,
            'cost_breakdown': result.cost_breakdown,
            'processing_time_ms': result.processing_time_ms,
            'cache_hit': result.cache_hit,
            'blocked': result.should_block,
            'enforcement_enabled': self.config.enforcement_enabled,
            'estimation_enabled': self.config.estimation_enabled
        }
        
        if context:
            metadata.update({
                'user_id': context.get('user_id', 'unknown'),
                'session_id': context.get('session_id', 'unknown')
            })
        
        status = "blocked" if result.should_block else "estimated"
        
        self.decision_ledger.log(
            phase="cost-validation",
            mcp="intent-cost-guardrails", 
            tool="validate_cost",
            rationale=f"Estimated ${result.estimated_cost:.2f}/mês for services: {', '.join(result.services_detected)}",
            status=status,
            metadata=metadata
        )
    
    def _log_cost_error(self, intent: str, error: str, context: Optional[Dict]):
        """Log de erro na validação de custo"""
        
        metadata = {
            'error': error,
            'intent_length': len(intent),
            'fallback_used': True
        }
        
        if context:
            metadata.update({
                'user_id': context.get('user_id', 'unknown'),
                'session_id': context.get('session_id', 'unknown')
            })
        
        self.decision_ledger.log(
            phase="cost-validation",
            mcp="intent-cost-guardrails",
            tool="validate_cost", 
            rationale=f"Cost validation failed: {error}",
            status="error_fallback",
            metadata=metadata
        )
    
    def get_config_status(self) -> Dict:
        """Retorna status da configuração"""
        return {
            'estimation_enabled': self.config.estimation_enabled,
            'enforcement_enabled': self.config.enforcement_enabled,
            'default_budget': self.config.default_budget,
            'services_supported': list(self.service_patterns.keys()),
            'fallback_prices_available': len(self.fallback_prices)
        }
