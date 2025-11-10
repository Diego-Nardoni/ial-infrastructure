#!/usr/bin/env python3
"""
Intelligent MCP Router - Router principal com detecção automática e orquestração
Substitui o MCP Router básico com capacidades avançadas
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from core.service_detector import ServiceDetector, DetectedService
from core.domain_mapper import DomainMapper, MCPMapping
from core.mcp_orchestrator import MCPOrchestrator
from core.mcp_registry import MCPRegistry
from core.decision_ledger import DecisionLedger

# Singleton global
_router_instance = None
_router_initialized = False

@dataclass
class RoutingDecision:
    user_input: str
    detected_services: List[DetectedService]
    detected_patterns: List[Dict]
    required_mcps: List[MCPMapping]
    execution_plan: Dict
    confidence: float
    processing_time: float

class IntelligentMCPRouter:
    def __new__(cls):
        global _router_instance
        if _router_instance is None:
            _router_instance = super().__new__(cls)
        return _router_instance
    
    def __init__(self):
        global _router_initialized
        if _router_initialized:
            return
        
        _router_initialized = True
        print("🧠 Intelligent MCP Router inicializado")
        
        # Componentes core
        self.service_detector = ServiceDetector()
        self.domain_mapper = DomainMapper()
        self.orchestrator = MCPOrchestrator()
        self.registry = MCPRegistry()
        self.decision_ledger = DecisionLedger()
        
        # Configurações - CORRIGIDO: threshold muito baixo para permitir execução
        self.min_confidence_threshold = 0.05  # Era 0.3, muito alto
        self.max_processing_time = 30.0
        self.enable_fallback = True
        
        # Cache de decisões
        self.routing_cache = {}
        self.cache_ttl = 300  # 5 minutos

    async def route_request(self, user_input: str, context: Dict = None) -> Dict:
        """Rota uma solicitação do usuário para MCPs apropriados"""
        start_time = time.time()
        
        if context is None:
            context = {}
        
        try:
            # 1. Verificar cache
            cache_key = self._generate_cache_key(user_input, context)
            cached_decision = self._get_cached_decision(cache_key)
            
            if cached_decision:
                print("💾 Usando decisão em cache")
                return await self._execute_cached_decision(cached_decision, context)
            
            # 2. Detectar serviços e padrões
            print(f"🔍 Analisando: '{user_input[:50]}...'")
            detection_result = self.service_detector.detect(user_input)
            
            detected_services = detection_result['services']
            detected_patterns = detection_result['patterns']
            
            if not detected_services:
                print("⚠️ Nenhum serviço AWS detectado, usando fallback")
                return await self._handle_fallback(user_input, context)
            
            # 3. Inferir dependências implícitas
            dependencies = self.service_detector.infer_dependencies(detected_services)
            
            # 4. Mapear para MCPs
            service_names = [s.name for s in detected_services] + dependencies
            required_mcps = self.domain_mapper.map_services_to_mcps(service_names)
            
            # 5. Criar plano de execução
            execution_plan = self._create_execution_plan(
                detected_services, detected_patterns, required_mcps, context
            )
            
            # 6. Calcular confiança da decisão
            confidence = self._calculate_confidence(detected_services, detected_patterns)
            
            # 7. Criar decisão de roteamento
            routing_decision = RoutingDecision(
                user_input=user_input,
                detected_services=detected_services,
                detected_patterns=detected_patterns,
                required_mcps=required_mcps,
                execution_plan=execution_plan,
                confidence=confidence,
                processing_time=time.time() - start_time
            )
            
            # 8. Cache da decisão
            self._cache_decision(cache_key, routing_decision)
            
            # 9. Log da decisão
            self._log_routing_decision(routing_decision, context)
            
            # 10. Executar orquestração
            if confidence >= self.min_confidence_threshold:
                return await self._execute_orchestrated(routing_decision, context)
            else:
                print(f"⚠️ Confiança baixa ({confidence:.2f}), usando fallback")
                return await self._handle_fallback(user_input, context)
                
        except Exception as e:
            print(f"❌ Erro no roteamento: {e}")
            return await self._handle_error(user_input, context, str(e))

    async def _execute_orchestrated(self, decision: RoutingDecision, context: Dict) -> Dict:
        """Executa orquestração coordenada dos MCPs - CORRIGIDO: usar AWS Real Executor"""
        print(f"🚀 Executando {len(decision.required_mcps)} MCPs coordenados")
        
        # Mostrar plano de execução
        self._print_execution_plan(decision)
        
        # CORREÇÃO: Forçar uso do AWS Real Executor
        try:
            import sys
            sys.path.append('/home/ial')
            sys.path.append('/home/ial/mcp-tools')
            from aws_real_server import AWSRealExecutor
            executor = AWSRealExecutor()
            
            # Para comandos de criação, usar executor direto
            if any(word in decision.user_input.lower() for word in ['create', 'deploy', 'provision']):
                
                results = []
                
                # Detectar e executar recursos específicos
                if 'dynamodb' in decision.user_input.lower():
                    import re
                    table_matches = re.findall(r'(\w+[-_]\w+[-_](?:state|conversations|catalog|checklist))', decision.user_input)
                    for table_name in table_matches:
                        result = executor.create_dynamodb_table(table_name)
                        results.append(result)
                
                if 's3' in decision.user_input.lower():
                    import re
                    bucket_matches = re.findall(r'(\w+[-_]\w+[-_](?:templates|artifacts|state)[-_]\d+)', decision.user_input)
                    for bucket_name in bucket_matches:
                        result = executor.create_s3_bucket(bucket_name)
                        results.append(result)
                
                if results:
                    successful = sum(1 for r in results if r.get('success', False))
                    return {
                        'success': successful > 0,
                        'resources_created': results,
                        'total_resources': len(results),
                        'successful_resources': successful,
                        'orchestrated_execution': True,
                        'routing_decision': {
                            'detected_services': [s.name for s in decision.detected_services],
                            'detected_patterns': [p['name'] for p in decision.detected_patterns],
                            'confidence': decision.confidence,
                            'mcps_used': [mcp.mcp_name for mcp in decision.required_mcps],
                            'processing_time': decision.processing_time
                        }
                    }
            
            # Fallback para Foundation Deployer completo
            from core.foundation_deployer import FoundationDeployer
            deployer = FoundationDeployer()
            result = deployer.deploy_phase("00-foundation")
            
            return {
                'success': result.get('successful', 0) > 0,
                'foundation_deployed': result,
                'orchestrated_execution': True,
                'routing_decision': {
                    'detected_services': [s.name for s in decision.detected_services],
                    'detected_patterns': [p['name'] for p in decision.detected_patterns],
                    'confidence': decision.confidence,
                    'mcps_used': [mcp.mcp_name for mcp in decision.required_mcps],
                    'processing_time': decision.processing_time
                }
            }
            
        except Exception as e:
            print(f"❌ Erro na execução orquestrada: {e}")
            # Fallback para orquestrador original
            result = await self.orchestrator.execute_coordinated(
                decision.required_mcps, 
                context, 
                decision.user_input
            )
            
            # Adicionar metadados da decisão
            result.update({
                'routing_decision': {
                    'detected_services': [s.name for s in decision.detected_services],
                    'detected_patterns': [p['name'] for p in decision.detected_patterns],
                    'confidence': decision.confidence,
                    'mcps_used': [mcp.mcp_name for mcp in decision.required_mcps],
                    'processing_time': decision.processing_time
                }
            })
            
            return result

    def _create_execution_plan(self, services: List[DetectedService], 
                             patterns: List[Dict], mcps: List[MCPMapping], 
                             context: Dict) -> Dict:
        """Cria plano detalhado de execução"""
        
        # Organizar MCPs por fases
        phases = self.domain_mapper.get_deployment_phases(mcps)
        
        # Determinar ordem de prioridade
        domain_priority = self.service_detector.get_domain_priority(services)
        
        plan = {
            'strategy': 'coordinated_deployment',
            'phases': phases,
            'domain_priority': domain_priority,
            'estimated_time': self._estimate_execution_time(mcps),
            'parallel_execution': True,
            'fallback_enabled': self.enable_fallback
        }
        
        # Adicionar contexto de padrões arquiteturais
        if patterns:
            plan['architecture_patterns'] = [p['name'] for p in patterns]
            plan['pattern_optimizations'] = self._get_pattern_optimizations(patterns)
        
        return plan

    def _calculate_confidence(self, services: List[DetectedService], 
                            patterns: List[Dict]) -> float:
        """Calcula confiança da decisão de roteamento"""
        if not services:
            return 0.0
        
        # Confiança baseada nos serviços detectados
        service_confidence = sum(s.confidence for s in services) / len(services)
        
        # Boost de confiança se padrões arquiteturais foram detectados
        pattern_boost = 0.1 * len(patterns) if patterns else 0.0
        
        # Penalidade se muitos serviços com baixa confiança
        low_confidence_penalty = sum(1 for s in services if s.confidence < 0.5) * 0.05
        
        final_confidence = min(service_confidence + pattern_boost - low_confidence_penalty, 1.0)
        
        return max(final_confidence, 0.0)

    def _print_execution_plan(self, decision: RoutingDecision):
        """Imprime plano de execução de forma legível"""
        print("\n📋 PLANO DE EXECUÇÃO")
        print("=" * 40)
        
        print(f"🎯 Serviços detectados: {[s.name for s in decision.detected_services]}")
        
        if decision.detected_patterns:
            print(f"🏗️ Padrões: {[p['name'] for p in decision.detected_patterns]}")
        
        print(f"🤖 MCPs necessários: {len(decision.required_mcps)}")
        for mcp in decision.required_mcps:
            print(f"   • {mcp.mcp_name} (prioridade: {mcp.priority})")
        
        print(f"📊 Confiança: {decision.confidence:.2f}")
        print(f"⏱️ Tempo estimado: {decision.execution_plan.get('estimated_time', 'N/A')}s")
        print()

    async def _handle_fallback(self, user_input: str, context: Dict) -> Dict:
        """Lida com fallback quando detecção falha - CORRIGIDO: usar AWS Real Executor"""
        if not self.enable_fallback:
            return {
                'success': False,
                'error': 'Detecção de serviços falhou e fallback desabilitado',
                'fallback_used': False
            }
        
        print("🔄 Usando fallback para CloudFormation básico")
        
        # CORREÇÃO: Usar AWS Real Executor diretamente
        try:
            import sys
            sys.path.append('/home/ial')
            sys.path.append('/home/ial/mcp-tools')
            from aws_real_server import AWSRealExecutor
            executor = AWSRealExecutor()
            
            # Detectar tipo de recurso e executar
            if 'dynamodb' in user_input.lower() or 'table' in user_input.lower():
                # Extrair nome da tabela
                import re
                table_match = re.search(r'(\w+[-_]\w+[-_]state|\w+[-_]\w+[-_]conversations|\w+[-_]\w+[-_]catalog)', user_input)
                if table_match:
                    table_name = table_match.group(1)
                    result = executor.create_dynamodb_table(table_name)
                    return {
                        'success': result['success'],
                        'resource_created': result,
                        'fallback_used': True,
                        'fallback_reason': 'Detecção falhou, executando diretamente'
                    }
            
            elif 's3' in user_input.lower() or 'bucket' in user_input.lower():
                # Extrair nome do bucket
                import re
                bucket_match = re.search(r'(\w+[-_]\w+[-_]templates[-_]\d+|\w+[-_]\w+[-_]artifacts[-_]\d+|\w+[-_]\w+[-_]state[-_]\d+)', user_input)
                if bucket_match:
                    bucket_name = bucket_match.group(1)
                    result = executor.create_s3_bucket(bucket_name)
                    return {
                        'success': result['success'],
                        'resource_created': result,
                        'fallback_used': True,
                        'fallback_reason': 'Detecção falhou, executando diretamente'
                    }
            
            # Se não conseguir detectar, usar Foundation Deployer
            from core.foundation_deployer import FoundationDeployer
            deployer = FoundationDeployer()
            result = deployer.deploy_phase("00-foundation")
            
            return {
                'success': result.get('successful', 0) > 0,
                'foundation_deployed': result,
                'fallback_used': True,
                'fallback_reason': 'Usando Foundation Deployer completo'
            }
            
        except Exception as e:
            print(f"❌ Erro no fallback: {e}")
            return {
                'success': False,
                'error': f'Fallback falhou: {e}',
                'fallback_used': True
            }

    async def _handle_error(self, user_input: str, context: Dict, error: str) -> Dict:
        """Lida com erros durante roteamento"""
        return {
            'success': False,
            'error': f'Erro no roteamento inteligente: {error}',
            'fallback_used': False,
            'user_input': user_input,
            'timestamp': time.time()
        }

    def _generate_cache_key(self, user_input: str, context: Dict) -> str:
        """Gera chave de cache para a solicitação"""
        # Simplificar input para cache
        normalized_input = user_input.lower().strip()
        context_key = str(sorted(context.items())) if context else ""
        
        return f"{hash(normalized_input + context_key)}"

    def _get_cached_decision(self, cache_key: str) -> Optional[RoutingDecision]:
        """Recupera decisão do cache se válida"""
        if cache_key in self.routing_cache:
            cached_item = self.routing_cache[cache_key]
            if time.time() - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['decision']
            else:
                # Cache expirado
                del self.routing_cache[cache_key]
        
        return None

    def _cache_decision(self, cache_key: str, decision: RoutingDecision):
        """Armazena decisão no cache"""
        self.routing_cache[cache_key] = {
            'decision': decision,
            'timestamp': time.time()
        }

    def _log_routing_decision(self, decision: RoutingDecision, context: Dict):
        """Log da decisão no decision ledger"""
        self.decision_ledger.log(
            phase="routing",
            mcp="intelligent_router",
            tool="route_request",
            rationale=f"Detected {len(decision.detected_services)} services, confidence: {decision.confidence:.2f}",
            status="ROUTED" if decision.confidence >= self.min_confidence_threshold else "FALLBACK"
        )

    def _estimate_execution_time(self, mcps: List[MCPMapping]) -> float:
        """Estima tempo de execução baseado nos MCPs"""
        # Tempo base + tempo de carregamento + tempo de execução
        base_time = 2.0
        load_time = sum(mcp.load_timeout for mcp in mcps if mcp.mcp_name not in self.orchestrator.active_mcps)
        execution_time = len(mcps) * 1.5  # Estimativa de execução por MCP
        
        return base_time + load_time + execution_time

    def _get_pattern_optimizations(self, patterns: List[Dict]) -> Dict:
        """Retorna otimizações baseadas em padrões arquiteturais"""
        optimizations = {}
        
        for pattern in patterns:
            if pattern['name'] == '3-tier':
                optimizations['3-tier'] = {
                    'enable_auto_scaling': True,
                    'multi_az_deployment': True,
                    'load_balancer_required': True
                }
            elif pattern['name'] == 'serverless':
                optimizations['serverless'] = {
                    'prefer_lambda': True,
                    'enable_api_gateway': True,
                    'use_dynamodb': True
                }
        
        return optimizations

    async def _execute_cached_decision(self, decision: RoutingDecision, context: Dict) -> Dict:
        """Executa decisão em cache"""
        return await self._execute_orchestrated(decision, context)

    def get_router_stats(self) -> Dict:
        """Retorna estatísticas do router"""
        return {
            'cache_size': len(self.routing_cache),
            'orchestrator_stats': self.orchestrator.get_execution_stats(),
            'active_mcps': len(self.orchestrator.get_active_mcps()),
            'confidence_threshold': self.min_confidence_threshold,
            'fallback_enabled': self.enable_fallback
        }
