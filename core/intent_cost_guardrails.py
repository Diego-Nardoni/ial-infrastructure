#!/usr/bin/env python3
"""
Intent Cost Guardrails - REAL LLM + MCP Cost Analysis
Custo REAL usando LLM para análise + MCP Cost Server para preços AWS API
"""

import os
import sys
import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Add core path for imports
sys.path.append(os.path.dirname(__file__))

@dataclass
class CostValidationResult:
    """Resultado da validação de custo REAL"""
    estimated_cost: Optional[float] = None
    cost_breakdown: Dict[str, float] = field(default_factory=dict)
    should_block: bool = False
    block_message: str = ""
    cache_hit: bool = False
    processing_time_ms: int = 0
    services_detected: List[str] = field(default_factory=list)
    cost_source: str = "unknown"  # "mcp_real", "llm_analysis", "unavailable"

@dataclass
class CostConfig:
    """Configuração do sistema de custos REAL"""
    estimation_enabled: bool = True
    enforcement_enabled: bool = False
    default_budget: float = 150.0
    cache_ttl_minutes: int = 60
    timeout_seconds: int = 5
    show_breakdown: bool = True
    require_real_costs: bool = True  # Não mostrar custos falsos

class RealCostGuardrails:
    """
    Sistema de custos REAL usando LLM + MCP Cost Server
    """
    
    def __init__(self):
        self.config = self._load_config()
        self.cache = {}
        
        # Initialize LLM and MCP components
        self.llm_provider = None
        self.mcp_cost_server = None
        self._init_components()
    
    def _init_components(self):
        """Initialize LLM and MCP components"""
        try:
            from core.llm_provider import LLMProvider
            self.llm_provider = LLMProvider()
            print("✅ LLM Provider initialized for cost analysis")
        except Exception as e:
            print(f"⚠️ LLM Provider not available: {e}")
        
        try:
            from core.mcp_orchestrator import MCPOrchestrator
            self.mcp_orchestrator = MCPOrchestrator()
            print("✅ MCP Orchestrator initialized for cost analysis")
        except Exception as e:
            print(f"⚠️ MCP Orchestrator not available: {e}")
    
    def _load_config(self) -> CostConfig:
        """Load cost configuration"""
        try:
            config_path = "/etc/ial/cost_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                return CostConfig(**config_data)
        except Exception as e:
            print(f"⚠️ Using default cost config: {e}")
        
        return CostConfig()
    
    async def estimate_intent_cost(self, user_request: str) -> Optional[float]:
        """
        Estima custo REAL usando LLM + MCP Cost Server
        
        Args:
            user_request: Requisição do usuário (ex: "listar ec2")
            
        Returns:
            float: Custo real em USD/mês ou None se não disponível
        """
        
        if not self.config.estimation_enabled:
            return None
        
        try:
            # 1. USAR LLM PARA ANÁLISE INTELIGENTE
            infrastructure_analysis = await self._analyze_with_llm(user_request)
            
            if not infrastructure_analysis or not infrastructure_analysis.get('services'):
                print("🔍 LLM: Nenhum serviço AWS detectado")
                return None
            
            # 2. USAR MCP COST SERVER PARA PREÇOS REAIS
            real_cost = await self._get_real_cost_from_mcp(infrastructure_analysis)
            
            if real_cost is not None:
                print(f"💰 Custo real obtido via MCP: ${real_cost}")
                return real_cost
            
            # 3. SE MCP FALHA, NÃO MOSTRAR CUSTO FALSO
            if self.config.require_real_costs:
                print("⚠️ Custo real não disponível, não mostrando estimativa falsa")
                return None
            
            return None
            
        except Exception as e:
            print(f"⚠️ Erro na estimativa de custo real: {e}")
            return None
    
    async def _analyze_with_llm(self, user_request: str) -> Optional[Dict]:
        """Usa LLM para análise inteligente da infraestrutura"""
        
        if not self.llm_provider:
            return None
        
        try:
            # Prompt otimizado para análise de infraestrutura
            analysis_prompt = f"""
Analise esta requisição de infraestrutura AWS e identifique os serviços e recursos:

REQUISIÇÃO: "{user_request}"

Identifique:
1. Serviços AWS mencionados ou implícitos
2. Tipos de recursos (instâncias, storage, etc.)
3. Região (se mencionada)
4. Configurações específicas

Responda em JSON:
{{
    "services": ["ec2", "s3", "rds"],
    "resources": [
        {{
            "service": "ec2",
            "type": "instance",
            "size": "t2.small",
            "quantity": 1
        }}
    ],
    "region": "us-east-1",
    "operation": "list|create|modify"
}}

ANÁLISE:
"""
            
            # Usar LLM para análise
            llm_response = await self.llm_provider.generate_response(analysis_prompt)
            
            # Parse resposta do LLM
            analysis = self._parse_llm_analysis(llm_response)
            
            if analysis:
                print(f"🧠 LLM detectou serviços: {analysis.get('services', [])}")
                return analysis
            
            return None
            
        except Exception as e:
            print(f"⚠️ Erro na análise LLM: {e}")
            return None
    
    def _parse_llm_analysis(self, llm_response: str) -> Optional[Dict]:
        """Parse robusto da análise do LLM"""
        
        try:
            # Se for dict do LLM Provider, extrair texto
            if isinstance(llm_response, dict):
                text = llm_response.get('response', llm_response.get('processed_text', str(llm_response)))
            else:
                text = str(llm_response)
            
            # Extrair JSON da resposta
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
                
                # Validar estrutura
                if 'services' in analysis and isinstance(analysis['services'], list):
                    return analysis
            
            # Fallback: detecção por keywords (mínima)
            return self._keyword_fallback_analysis(text)
            
        except Exception as e:
            print(f"⚠️ Erro parsing LLM analysis: {e}")
            return None
    
    def _keyword_fallback_analysis(self, text: str) -> Optional[Dict]:
        """Fallback mínimo por keywords quando LLM parsing falha"""
        
        text_lower = text.lower()
        
        # Mapeamento mínimo de serviços
        service_keywords = {
            'ec2': ['ec2', 'instance', 'virtual machine', 'vm', 'compute'],
            's3': ['s3', 'bucket', 'storage', 'object'],
            'rds': ['rds', 'database', 'mysql', 'postgres', 'aurora'],
            'lambda': ['lambda', 'function', 'serverless'],
            'dynamodb': ['dynamodb', 'nosql', 'table'],
            'ecs': ['ecs', 'container', 'fargate', 'docker'],
            'elasticache': ['redis', 'elasticache', 'cache', 'memcached']
        }
        
        detected_services = []
        for service, keywords in service_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_services.append(service)
        
        if detected_services:
            return {
                'services': detected_services,
                'resources': [{'service': s, 'type': 'unknown', 'quantity': 1} for s in detected_services],
                'region': 'us-east-1',
                'operation': 'list'
            }
        
        return None
    
    async def _get_real_cost_from_mcp(self, infrastructure_analysis: Dict) -> Optional[float]:
        """Obtém custo REAL via MCP Cost Server"""
        
        if not self.mcp_orchestrator:
            return None
        
        try:
            services = infrastructure_analysis.get('services', [])
            resources = infrastructure_analysis.get('resources', [])
            region = infrastructure_analysis.get('region', 'us-east-1')
            
            total_cost = 0.0
            
            # Para cada serviço, consultar MCP Cost Server
            for service in services:
                service_cost = await self._get_service_cost_via_mcp(service, region, resources)
                if service_cost is not None:
                    total_cost += service_cost
                    print(f"💰 {service}: ${service_cost}/mês")
                else:
                    print(f"⚠️ {service}: custo não disponível via MCP")
                    # Se qualquer serviço falha e require_real_costs=True, retorna None
                    if self.config.require_real_costs:
                        return None
            
            return total_cost if total_cost > 0 else None
            
        except Exception as e:
            print(f"⚠️ Erro obtendo custo via MCP: {e}")
            return None
    
    async def _get_service_cost_via_mcp(self, service: str, region: str, resources: List[Dict]) -> Optional[float]:
        """Consulta MCP Cost Server para custo específico do serviço"""
        
        try:
            # Mapear serviços para MCPs específicos
            cost_mcp_mapping = {
                'ec2': 'aws-cost-explorer-mcp',
                's3': 'aws-cost-explorer-mcp',
                'rds': 'aws-cost-explorer-mcp',
                'lambda': 'aws-cost-explorer-mcp',
                'dynamodb': 'aws-cost-explorer-mcp',
                'ecs': 'aws-cost-explorer-mcp',
                'elasticache': 'aws-cost-explorer-mcp'
            }
            
            mcp_server = cost_mcp_mapping.get(service, 'aws-cost-explorer-mcp')
            
            # Construir query para MCP Cost Server
            cost_query = f"Calculate monthly cost for {service} service in {region}"
            
            # Adicionar detalhes específicos do recurso se disponível
            service_resources = [r for r in resources if r.get('service') == service]
            if service_resources:
                resource = service_resources[0]
                if resource.get('type') and resource.get('size'):
                    cost_query += f" with {resource['type']} {resource['size']}"
                if resource.get('quantity', 1) > 1:
                    cost_query += f" quantity {resource['quantity']}"
            
            # Consultar MCP Cost Server
            result = self.mcp_orchestrator.orchestrate([mcp_server], cost_query)
            
            if result.get('success'):
                # Extrair custo da resposta MCP
                cost = self._extract_cost_from_mcp_response(result.get('response', ''))
                return cost
            
            return None
            
        except Exception as e:
            print(f"⚠️ Erro consultando MCP para {service}: {e}")
            return None
    
    def _extract_cost_from_mcp_response(self, mcp_response: str) -> Optional[float]:
        """Extrai valor de custo da resposta do MCP"""
        
        try:
            import re
            
            # Padrões para extrair custos
            cost_patterns = [
                r'\$(\d+\.?\d*)',  # $25.50
                r'(\d+\.?\d*)\s*USD',  # 25.50 USD
                r'(\d+\.?\d*)\s*dollars?',  # 25.50 dollars
                r'cost[:\s]*\$?(\d+\.?\d*)',  # cost: $25.50
                r'price[:\s]*\$?(\d+\.?\d*)',  # price: $25.50
            ]
            
            for pattern in cost_patterns:
                match = re.search(pattern, mcp_response, re.IGNORECASE)
                if match:
                    cost_value = float(match.group(1))
                    if 0 < cost_value < 10000:  # Sanity check
                        return cost_value
            
            return None
            
        except Exception as e:
            print(f"⚠️ Erro extraindo custo da resposta MCP: {e}")
            return None
    
    async def validate_cost(self, intent: str, context: Optional[Dict] = None) -> CostValidationResult:
        """
        Validação de custo REAL com LLM + MCP
        """
        start_time = time.time()
        
        if not self.config.estimation_enabled:
            return CostValidationResult()
        
        try:
            # Estimar custo real
            estimated_cost = await self.estimate_intent_cost(intent)
            
            if estimated_cost is None:
                return CostValidationResult(
                    cost_source="unavailable",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Verificar enforcement
            should_block = False
            block_message = ""
            
            if self.config.enforcement_enabled and estimated_cost > self.config.default_budget:
                should_block = True
                block_message = f"⚠️ Custo estimado ${estimated_cost:.2f}/mês excede budget ${self.config.default_budget}"
            
            return CostValidationResult(
                estimated_cost=estimated_cost,
                should_block=should_block,
                block_message=block_message,
                cost_source="mcp_real",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
            
        except Exception as e:
            print(f"⚠️ Erro na validação de custo real: {e}")
            return CostValidationResult(
                cost_source="error",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

# Alias para compatibilidade
IntentCostGuardrails = RealCostGuardrails
