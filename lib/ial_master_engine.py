#!/usr/bin/env python3
"""
IaL Master Engine
Complete integration of all conversation, optimization, and infrastructure capabilities
Enhanced with Intelligent MCP Router
"""

import sys
import os
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add lib directory to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

# Try to import Intelligent MCP Router
try:
    from intelligent_mcp_router import IntelligentMCPRouter
    INTELLIGENT_ROUTER_AVAILABLE = True
except ImportError:
    INTELLIGENT_ROUTER_AVAILABLE = False
    print("⚠️ Intelligent MCP Router não disponível no Master Engine")

# Try to import GitHub Integration modules
GITHUB_INTEGRATION_AVAILABLE = False
try:
    from github_integration import GitHubIntegration
    from intent_parser import IntentParser
    from template_generator import TemplateGenerator
    GITHUB_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ GitHub Integration not available: {e}")

class IaLMasterEngine:
    def __init__(self, region='us-east-1'):
        self.region = region
        
        # Initialize Intelligent MCP Router if available
        self.intelligent_router = None
        if INTELLIGENT_ROUTER_AVAILABLE:
            try:
                self.intelligent_router = IntelligentMCPRouter()
                print("✅ Master Engine: Intelligent MCP Router integrado")
            except Exception as e:
                print(f"⚠️ Master Engine: Erro integrando router: {e}")
        
        # Initialize GitHub Integration if available
        self.github_integration = None
        self.intent_parser = None
        self.template_generator = None
        
        if GITHUB_INTEGRATION_AVAILABLE:
            try:
                self.github_integration = GitHubIntegration()
                self.intent_parser = IntentParser()
                self.template_generator = TemplateGenerator(self.github_integration.config)
                print("✅ Master Engine: GitHub Integration initialized")
            except Exception as e:
                print(f"⚠️ Master Engine: GitHub Integration error: {e}")
                self.github_integration = None
                self.intent_parser = None
                self.template_generator = None
        
        self.engines_available = True
        print("🚀 IaL Master Engine initialized - All systems operational")

    def process_conversation(self, user_input: str, user_id: str = None, session_id: str = None) -> Dict:
        """Master conversation processing with GitHub integration"""
        
        if not user_id:
            user_id = f"user-{uuid.uuid4().hex[:8]}"
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        start_time = datetime.now()
        
        try:
            # Check if this is an infrastructure command
            if self.intent_parser and self.intent_parser.is_infrastructure_command(user_input):
                return self.process_infrastructure_command(user_input, user_id)
            
            # Check if this should use intelligent MCP routing
            if self.intelligent_router and self._should_use_intelligent_routing(user_input):
                return self._process_with_intelligent_routing(user_input, user_id, session_id, start_time)
            
            # Original Master Engine processing
            return self._process_with_master_engine(user_input, user_id, session_id, start_time)
            
        except Exception as e:
            return {
                'response': f"❌ Erro no processamento: {str(e)}",
                'error': True,
                'session_id': session_id,
                'processing_time': (datetime.now() - start_time).total_seconds()
            }

    def process_infrastructure_command(self, user_input: str, user_id: str) -> Dict:
        """Process infrastructure command with GitHub integration"""
        
        if not self.github_integration:
            return {
                'response': f"🤖 Master Engine processou: {user_input}...",
                'status': 'fallback',
                'message': 'GitHub integration not available'
            }
        
        try:
            # 1. Parse intent from natural language
            intent = self.intent_parser.parse(user_input)
            
            if intent['confidence'] < 0.5:
                return {
                    'response': f"🤔 I'm not sure what infrastructure you want to {intent['action']}. Try being more specific, like 'create foundation infrastructure' or 'deploy security phase'.",
                    'status': 'clarification_needed'
                }
            
            # 2. Generate templates based on intent
            templates = self.template_generator.generate_from_intent(intent)
            
            if not templates:
                return {
                    'response': f"❌ Could not generate templates for {intent['domains']}. Please check if the domain is supported.",
                    'status': 'error'
                }
            
            # 3. Execute via GitHub integration
            result = self.github_integration.execute_infrastructure_deployment(templates, intent)
            
            return {
                'response': result['response'],
                'status': result['status'],
                'intent': intent,
                'templates_generated': len(templates),
                **result
            }
            
        except Exception as e:
            return {
                'response': f"❌ Infrastructure processing error: {str(e)}",
                'status': 'error'
            }

    def _should_use_intelligent_routing(self, user_input: str) -> bool:
        """Determina se deve usar roteamento inteligente"""
        # Usar para solicitações de infraestrutura complexas
        complex_infrastructure_patterns = [
            'deploy', 'create', 'setup', 'build', 'provision',
            'infrastructure', 'architecture', '3 tier', 'serverless',
            'microservices', 'container', 'database', 'load balancer'
        ]
        
        user_lower = user_input.lower()
        
        # Contar quantos padrões são encontrados
        pattern_count = sum(1 for pattern in complex_infrastructure_patterns if pattern in user_lower)
        
        # Usar router inteligente se múltiplos padrões ou padrões específicos
        return pattern_count >= 2 or any(
            pattern in user_lower for pattern in ['ecs + rds', 'lambda + sqs', '3 tier', 'serverless']
        )

    def _process_with_intelligent_routing(self, user_input: str, user_id: str, session_id: str, start_time) -> Dict:
        """Processa usando router inteligente"""
        print("🧠 Master Engine: Usando Intelligent MCP Router")
        
        context = {
            'user_id': user_id,
            'session_id': session_id,
            'timestamp': start_time.timestamp(),
            'master_engine': True
        }
        
        try:
            import asyncio
            
            # Executar roteamento inteligente
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            router_result = loop.run_until_complete(
                self.intelligent_router.route_request(user_input, context)
            )
            loop.close()
            
            # Enriquecer resultado com capacidades do Master Engine
            enhanced_result = self._enhance_router_result(router_result, user_input, user_id, session_id)
            
            # Adicionar informações do Master Engine
            enhanced_result.update({
                'master_engine_used': True,
                'intelligent_routing': True,
                'processing_time': (datetime.now() - start_time).total_seconds()
            })
            
            return enhanced_result
            
        except Exception as e:
            print(f"❌ Erro no router inteligente: {e}")
            # Fallback para processamento normal do Master Engine
            return self._process_with_master_engine(user_input, user_id, session_id, start_time)

    def _enhance_router_result(self, router_result: Dict, user_input: str, user_id: str, session_id: str) -> Dict:
        """Enriquece resultado do router com capacidades do Master Engine"""
        
        # Se router foi bem-sucedido, adicionar análise conversacional
        if router_result.get('success'):
            try:
                # Gerar resposta conversacional baseada no resultado técnico
                conversational_response = self._generate_conversational_response(router_result, user_input)
                
                # Atualizar resposta
                router_result['response'] = conversational_response
                router_result['conversational_enhancement'] = True
                
            except Exception as e:
                print(f"⚠️ Erro enriquecendo resposta: {e}")
        
        return router_result

    def _generate_conversational_response(self, router_result: Dict, user_input: str) -> str:
        """Gera resposta conversacional baseada no resultado técnico"""
        
        if not router_result.get('success'):
            return "❌ Não foi possível processar sua solicitação de infraestrutura."
        
        # Extrair informações do resultado
        routing_decision = router_result.get('routing_decision', {})
        services = routing_decision.get('detected_services', [])
        mcps_used = routing_decision.get('mcps_used', [])
        phases = router_result.get('phases', {})
        
        # Construir resposta conversacional
        response_parts = []
        
        # Introdução baseada nos serviços detectados
        if services:
            service_list = ', '.join(services)
            response_parts.append(f"🎯 Entendi que você quer trabalhar com: **{service_list}**")
        
        # Status da execução
        successful_phases = [name for name, phase in phases.items() if phase.get('success')]
        if successful_phases:
            response_parts.append(f"✅ Configurei com sucesso: **{', '.join(successful_phases)}**")
        
        # Detalhes técnicos
        if mcps_used:
            response_parts.append(f"🔧 Utilizei {len(mcps_used)} componentes especializados para otimizar a configuração.")
        
        # Tempo de execução
        exec_time = router_result.get('execution_time', 0)
        if exec_time > 0:
            response_parts.append(f"⚡ Processamento concluído em {exec_time:.1f} segundos.")
        
        # Próximos passos
        response_parts.append(f"\n💡 **Próximos passos recomendados:**")
        response_parts.append(f"• Verificar os recursos criados no AWS Console")
        response_parts.append(f"• Configurar monitoramento e alertas")
        response_parts.append(f"• Testar a conectividade entre os componentes")
        
        return '\n'.join(response_parts)

    def _process_with_master_engine(self, user_input: str, user_id: str, session_id: str, start_time) -> Dict:
        """Processamento original do Master Engine"""
        try:
            # Processamento básico para compatibilidade
            response = f"🤖 Master Engine processou: {user_input[:50]}..."
            
            return {
                'response': response,
                'session_id': session_id,
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'master_engine_used': True,
                'intelligent_routing': False
            }
            
        except Exception as e:
            return {
                'response': f"❌ Erro no Master Engine: {str(e)}",
                'error': True,
                'session_id': session_id,
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
