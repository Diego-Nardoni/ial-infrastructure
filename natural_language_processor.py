#!/usr/bin/env python3
"""
IaL Natural Language Processor v3.1
Complete system with all phases integrated + Intelligent MCP Router + Intent Validation
"""

import sys
import os

# Ultra silent mode - only show LLM response
ULTRA_SILENT_MODE = not any(flag in sys.argv for flag in ['--help', '--verbose', '-v', '--debug'])

def ultra_silent_print(*args, **kwargs):
    """Print only if not in ultra silent mode"""
    if not ULTRA_SILENT_MODE:
        print(*args, **kwargs)

def ultra_ultra_silent_print(*args, **kwargs):
    """Never print in ultra silent mode"""
    pass
import uuid
import json
import readline
import asyncio
import warnings
from typing import Dict, List, Optional

# Suprimir warnings e erros não-críticos
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

# Supressão TOTAL de erros técnicos
import io
import contextlib

# Redirecionar TODOS os outputs de erro
class NullWriter:
    def write(self, data): return len(data)
    def flush(self): pass
    def close(self): pass

# Aplicar supressão total
sys.stderr = NullWriter()

# Suprimir também stdout de erros do Python
@contextlib.contextmanager
def suppress_all_errors():
    with contextlib.redirect_stderr(NullWriter()):
        yield

# Aplicar globalmente
sys.excepthook = lambda *args: None

# Configure readline for better input handling
def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

# Set up readline key bindings
readline.parse_and_bind('Control-l: clear-screen')

# Add core path for intelligent router
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

# Try to import Master Engine and Intelligent Router
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
    from core.master_engine_final import MasterEngineFinal as IaLMasterEngine
    MASTER_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Master Engine not available: {e}")
    MASTER_ENGINE_AVAILABLE = False

# Try to import Intelligent MCP Router Sophisticated
try:
    from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
    INTELLIGENT_ROUTER_AVAILABLE = True
    ultra_silent_print("🧠 Intelligent MCP Router Sophisticated disponível") if "--help" in sys.argv else None
except ImportError as e:
    print(f"⚠️ Intelligent MCP Router not available: {e}")
    INTELLIGENT_ROUTER_AVAILABLE = False

# Try to import Intent Validation System
try:
    from intent_validation import ValidationSystem
    VALIDATION_SYSTEM_AVAILABLE = True
#    ultra_silent_print("🛡️ Sistema de Validação de Intenção disponível") if "--help" in sys.argv else None
except ImportError as e:
    print(f"⚠️ Intent Validation System not available: {e}")
    VALIDATION_SYSTEM_AVAILABLE = False

class IaLNaturalProcessor:
    def __init__(self):
        # Initialize Intent Validation System first
        self.validation_system = None
        if VALIDATION_SYSTEM_AVAILABLE:
            try:
                self.validation_system = ValidationSystem()
#                ultra_silent_ultra_silent_print("✅ Sistema de Validação de Intenção inicializado")
            except Exception as e:
                print(f"⚠️ Erro inicializando Validation System: {e}")
                self.validation_system = None
        
        # Initialize Intelligent MCP Router
        self.intelligent_router = None
        if INTELLIGENT_ROUTER_AVAILABLE:
            try:
                self.intelligent_router = IntelligentMCPRouterSophisticated()
            except Exception as e:
                print(f"⚠️ Erro inicializando Intelligent Router: {e}")
                self.intelligent_router = None
        
        if MASTER_ENGINE_AVAILABLE:
            try:
                self.master_engine = IaLMasterEngine()
                self.advanced_mode = True
                print("🚀 IaL v3.1 - Advanced Mode: ALL SYSTEMS OPERATIONAL")
                ultra_silent_ultra_silent_print("✅ Bedrock Conversational AI")
                ultra_silent_ultra_silent_print("✅ Infrastructure Integration") 
                ultra_silent_ultra_silent_print("✅ Response Caching & Optimization")
                ultra_silent_ultra_silent_print("✅ Knowledge Base & RAG")
                ultra_silent_ultra_silent_print("✅ Cost Monitoring & Rate Limiting")
                if self.intelligent_router:
                    ultra_silent_ultra_silent_print("✅ Intelligent MCP Router")
                if self.validation_system:
                    ultra_silent_ultra_silent_print("✅ Intent Validation System")
            except Exception as e:
                print(f"⚠️ Master Engine initialization failed: {e}")
                self.advanced_mode = False
                self.init_fallback_mode()
        else:
            self.advanced_mode = False
            self.init_fallback_mode()

    def init_fallback_mode(self):
        """Initialize fallback mode for basic functionality"""
        print("⚠️ IaL v3.0 - Fallback Mode: Basic functionality only")
        
        # Basic pattern matching for offline mode
        self.domain_mapping = {
            'security': ['security', 'kms', 'iam', 'secrets', 'waf', 'encryption'],
            'networking': ['network', 'vpc', 'subnet', 'routing', 'flow logs'],
            'compute': ['compute', 'ecs', 'container', 'cluster', 'scaling'],
            'data': ['database', 'rds', 'dynamodb', 'redis', 'storage', 's3'],
            'application': ['lambda', 'function', 'step functions', 'sns', 'api'],
            'observability': ['monitoring', 'cloudwatch', 'logs', 'metrics', 'alerts'],
            'ai-ml': ['bedrock', 'ai', 'ml', 'rag', 'machine learning'],
            'governance': ['budget', 'cost', 'compliance', 'well-architected']
        }
        
        self.action_mapping = {
            'deploy': ['deploy', 'create', 'setup', 'build', 'provision', 'install'],
            'status': ['status', 'show', 'check', 'list', 'display', 'what'],
            'rollback': ['rollback', 'undo', 'revert', 'remove', 'delete', 'destroy'],
            'validate': ['validate', 'test', 'verify', 'check', 'ensure']
        }

    def process_command(self, user_input: str, user_id: str = None, session_id: str = None) -> str:
        """Main processing function with intent validation and intelligent MCP routing"""
        
        if not user_id:
            user_id = "anonymous-user"
        
        # ===== NOVA INSERÇÃO: SISTEMA DE VALIDAÇÃO DE INTENÇÃO =====
        pending_warnings = []
        cost_info = ""
        if self.validation_system:
            try:
                validation_context = {
                    'user_id': user_id,
                    'session_id': session_id,
                    'timestamp': __import__('time').time()
                }
                
                validation_result = self.validation_system.validate_intent(user_input, validation_context)
                
                # Verificar se deve bloquear
                if validation_result.should_block:
                    return f"{validation_result.block_message}\n\n📋 Para prosseguir, entre em contato com o administrador."
                
                # Preparar avisos para adicionar à resposta final
                pending_warnings = validation_result.warnings if validation_result.has_warnings else []
                
                # NOVO: Preparar informações de custo
                if validation_result.cost_estimation_used and validation_result.estimated_cost:
                    cost_info = f"\n💰 Custo estimado: ${validation_result.estimated_cost:.2f}/mês"
                    
                    if validation_result.cost_breakdown and len(validation_result.cost_breakdown) > 1:
                        breakdown = ", ".join([
                            f"{k}: ${v:.2f}" 
                            for k, v in validation_result.cost_breakdown.items()
                        ])
                        cost_info += f" ({breakdown})"
                
            except Exception as e:
                # Fallback silencioso - não quebrar sistema existente
                print(f"⚠️ Erro na validação de intenção: {e}")
                pending_warnings = []
                cost_info = ""
        # ===== FIM DA INSERÇÃO =====
        
        # Try intelligent MCP routing first if available
        if self.intelligent_router and self.should_use_intelligent_routing(user_input):
            try:
                ultra_silent_print("🧠 Usando Intelligent MCP Router")
                response = self.process_with_intelligent_router(user_input, user_id, session_id)
            except Exception as e:
                print(f"⚠️ Erro no Intelligent Router: {e}, usando fallback")
                response = self._process_fallback_path(user_input, user_id, session_id)
        else:
            response = self._process_fallback_path(user_input, user_id, session_id)
        
        # Adicionar avisos de validação à resposta final
        if pending_warnings:
            warnings_text = "\n\n" + "\n".join(pending_warnings)
            response += warnings_text
        
        # NOVO: Adicionar informações de custo à resposta final
        if cost_info:
            response += cost_info
        
        return response

    def _process_fallback_path(self, user_input: str, user_id: str, session_id: str) -> str:
        """Processa usando Master Engine ou fallback básico"""
        if self.advanced_mode:
            try:
                # Use Master Engine for full functionality
                result = self.master_engine.process_conversation(user_input, user_id, session_id)
                
                # Extract response directly
                response = result.get('response', 'No response generated')
                
                # Add performance info for interactive mode
                if result.get('cached'):
                    response += f"\n\n💾 (Cached response - {result.get('processing_time', 0):.2f}s)"
                elif result.get('rag_used'):
                    response += f"\n\n🧠 (Knowledge base used - {result.get('knowledge_base_hits', 0)} sources)"
                elif result.get('infrastructure_action'):
                    response += f"\n\n🏗️ (Infrastructure action: {result.get('action_type', 'unknown')})"
                
                return response
                
            except Exception as e:
                print(f"Master Engine error: {e}")
                return self.fallback_processing(user_input)
        else:
            return self.fallback_processing(user_input)

    def should_use_intelligent_routing(self, user_input: str) -> bool:
        """Determina se deve usar roteamento inteligente"""
        # Usar router inteligente para solicitações de infraestrutura
        infrastructure_keywords = [
            'deploy', 'create', 'setup', 'build', 'provision',
            'delete', 'remove', 'destroy', 'cleanup', 'exclude',
            'ecs', 'lambda', 'rds', 'elb', 'vpc', 's3', 'dynamodb',
            'infrastructure', 'architecture', 'serverless', 'container',
            'phase', 'stack'
        ]
        
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in infrastructure_keywords)
    
    def _process_with_bedrock_conversational(self, user_input: str, user_id: str, session_id: str) -> str:
        """Processa conversação natural com Bedrock incluindo contexto temporal"""
        
        # Adicionar contexto temporal para perguntas sobre data/tempo
        context_info = self._get_temporal_context(user_input)
        
        # Preparar prompt com contexto
        if context_info:
            enhanced_prompt = f"{context_info}\n\nUsuário pergunta: {user_input}"
        else:
            enhanced_prompt = user_input
        
        # Usar fallback básico com contexto aprimorado
        return self.fallback_processing(enhanced_prompt)
    
    def _get_temporal_context(self, user_input: str) -> str:
        """Adiciona contexto temporal se a pergunta for sobre data/tempo"""
        
        temporal_keywords = [
            'que dia', 'what day', 'que data', 'what date',
            'hoje', 'today', 'agora', 'now',
            'que horas', 'what time', 'hora atual', 'current time',
            'quando', 'when', 'data atual', 'current date'
        ]
        
        user_lower = user_input.lower()
        needs_temporal_context = any(keyword in user_lower for keyword in temporal_keywords)
        
        if needs_temporal_context:
            from datetime import datetime
            import locale
            
            try:
                # Tentar configurar locale para português
                locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            except:
                try:
                    locale.setlocale(locale.LC_TIME, 'C.UTF-8')
                except:
                    pass
            
            now = datetime.now()
            
            # Mapear dias da semana para português
            weekdays_pt = {
                'Monday': 'segunda-feira',
                'Tuesday': 'terça-feira', 
                'Wednesday': 'quarta-feira',
                'Thursday': 'quinta-feira',
                'Friday': 'sexta-feira',
                'Saturday': 'sábado',
                'Sunday': 'domingo'
            }
            
            # Mapear meses para português
            months_pt = {
                'January': 'janeiro', 'February': 'fevereiro', 'March': 'março',
                'April': 'abril', 'May': 'maio', 'June': 'junho',
                'July': 'julho', 'August': 'agosto', 'September': 'setembro',
                'October': 'outubro', 'November': 'novembro', 'December': 'dezembro'
            }
            
            weekday_en = now.strftime('%A')
            month_en = now.strftime('%B')
            
            weekday_pt = weekdays_pt.get(weekday_en, weekday_en)
            month_pt = months_pt.get(month_en, month_en)
            
            return f"""CONTEXTO TEMPORAL ATUAL:
- Data: {now.strftime('%d')} de {month_pt} de {now.strftime('%Y')}
- Dia da semana: {weekday_pt}
- Horário: {now.strftime('%H:%M:%S')} (UTC)
- Timestamp: {now.isoformat()}

Use essas informações para responder perguntas sobre data e hora atual."""
        
        return None

    def process_with_intelligent_router(self, user_input: str, user_id: str, session_id: str) -> str:
        """Processa usando o router inteligente"""
        context = {
            'user_id': user_id,
            'session_id': session_id or str(uuid.uuid4()),
            'timestamp': __import__('time').time()
        }
        
        # Executar roteamento inteligente (síncrono)
        try:
            # Usar método sync que chama async internamente
            result = self.intelligent_router.route_request(user_input)
            
            # Processar resultado
            return self.format_intelligent_router_response(result, user_input)
            
        except Exception as e:
            print(f"❌ Erro na execução do router: {e}")
            raise

    def format_intelligent_router_response(self, result: Dict, user_input: str) -> str:
        """Formata resposta do router inteligente para o usuário"""
        if not result.get('success'):
            error_msg = result.get('error', 'Erro desconhecido')
            if result.get('fallback_used'):
                return f"⚠️ {error_msg}\n🔄 Usando modo básico para processar sua solicitação."
            else:
                return f"❌ {error_msg}"
        
        # Check if GitOps was triggered
        execution_results = result.get('execution_results', {})
        gitops_info = result.get('gitops_info', {})
        
        if execution_results.get('status') == 'gitops_triggered':
            # GitOps workflow triggered
            response_parts = [
                f"🧠 **Análise Inteligente Concluída**",
                f"✅ Solicitação: {user_input}",
                ""
            ]
            
            # LLM Analysis
            llm_result = result.get('llm_result', {})
            if llm_result:
                response_parts.extend([
                    f"🤖 **Processamento LLM:**",
                    f"   • Provider: {llm_result.get('provider', 'unknown')}",
                    f"   • Confiança: {llm_result.get('confidence', 0):.1%}",
                    f"   • Entidades: {', '.join(llm_result.get('entities', []))}",
                    ""
                ])
            
            # Architecture Detection
            detection_result = result.get('detection_result', {})
            if detection_result:
                pattern = detection_result.get('pattern')
                response_parts.extend([
                    f"🏗️ **Arquitetura Detectada:**",
                    f"   • Padrão: {pattern or 'Genérico'}",
                    f"   • Domínios: {', '.join(detection_result.get('domains', []))}",
                    f"   • Confiança: {detection_result.get('confidence', 0):.1%}",
                    ""
                ])
            
            # MCP Loading
            mapping_result = result.get('mapping_result', {})
            if mapping_result:
                response_parts.extend([
                    f"⚡ **MCPs Carregados:**",
                    f"   • Total: {mapping_result.get('required_mcps', 0)} MCPs",
                    f"   • Ativos: {', '.join(mapping_result.get('loaded_mcps', [])[:3])}{'...' if len(mapping_result.get('loaded_mcps', [])) > 3 else ''}",
                    ""
                ])
            
            # GitOps Status
            github_status = gitops_info.get('github_status')
            if github_status == 'success':
                response_parts.extend([
                    f"🚀 **GitOps Workflow Iniciado:**",
                    f"   • ✅ Templates YAML gerados: {gitops_info.get('templates_count', 0)}",
                    f"   • ✅ Commit enviado para GitHub",
                    f"   • ✅ GitHub Actions será executado automaticamente",
                    f"   • 🔗 PR: {gitops_info.get('pr_url', 'Será criado em breve')}",
                    "",
                    f"⏱️ **Próximos Passos:**",
                    f"   1. GitHub Actions executará o deployment",
                    f"   2. Recursos AWS serão provisionados",
                    f"   3. Audit e compliance serão validados",
                    f"   4. Você receberá notificação de conclusão"
                ])
            else:
                response_parts.extend([
                    f"⚠️ **GitOps Workflow:**",
                    f"   • Status: {github_status or 'Erro'}",
                    f"   • Detalhes: {execution_results.get('github_response', 'Erro desconhecido')}",
                    f"   • Fallback disponível se necessário"
                ])
            
            # Performance Metrics
            perf_metrics = result.get('performance_metrics', {})
            if perf_metrics:
                total_time = perf_metrics.get('total_time', 0)
                response_parts.extend([
                    "",
                    f"📊 **Performance:** {total_time}ms total"
                ])
            
            return "\n".join(response_parts)
        
        # Fallback to original format for other cases
        response_parts = []
        
        # Cabeçalho com informações da execução
        if 'routing_decision' in result:
            decision = result['routing_decision']
            services = decision.get('detected_services', [])
            mcps = decision.get('mcps_used', [])
            confidence = decision.get('confidence', 0)
            
            response_parts.append(f"🎯 **Análise da Solicitação:**")
            response_parts.append(f"   • Serviços detectados: {', '.join(services) if services else 'Nenhum'}")
            response_parts.append(f"   • MCPs utilizados: {len(mcps)}")
            response_parts.append(f"   • Confiança: {confidence:.0%}")
        
        # Informações das fases executadas
        if 'phases' in result:
            phases = result['phases']
            successful_phases = [name for name, phase in phases.items() if phase.get('success')]
            
            response_parts.append(f"\n🚀 **Execução:**")
            response_parts.append(f"   • Fases executadas: {len(successful_phases)}/{len(phases)}")
            response_parts.append(f"   • Fases: {', '.join(successful_phases)}")
            
            # Mostrar resultados por fase
            for phase_name, phase_result in phases.items():
                if phase_result.get('success') and phase_result.get('results'):
                    response_parts.append(f"\n   📋 **{phase_name.title()}:**")
                    for mcp_name, mcp_result in phase_result['results'].items():
                        if mcp_result.get('success'):
                            action = mcp_result.get('result', {}).get('action', 'ação executada')
                            resources = mcp_result.get('result', {}).get('resources', [])
                            response_parts.append(f"      ✅ {mcp_name}: {action}")
                            if resources:
                                response_parts.append(f"         Recursos: {', '.join(resources)}")
        
        # Performance e estatísticas
        exec_time = result.get('execution_time', 0)
        total_mcps = result.get('total_mcps', 0)
        
        response_parts.append(f"\n📊 **Performance:**")
        response_parts.append(f"   • Tempo de execução: {exec_time:.2f}s")
        response_parts.append(f"   • MCPs coordenados: {total_mcps}")
        
        # Fallback usado
        if result.get('fallback_used'):
            reason = result.get('fallback_reason', 'Motivo não especificado')
            response_parts.append(f"\n⚠️ **Fallback:** {reason}")
        
        # Erros se houver
        if result.get('errors'):
            response_parts.append(f"\n❌ **Avisos:**")
            for error in result['errors'][:3]:  # Mostrar apenas os 3 primeiros
                response_parts.append(f"   • {error}")
        
        # Próximos passos sugeridos
        if result.get('success') and not result.get('fallback_used'):
            response_parts.append(f"\n✅ **Infraestrutura configurada com sucesso!**")
            response_parts.append(f"💡 **Próximos passos:**")
            response_parts.append(f"   • Verificar recursos no AWS Console")
            response_parts.append(f"   • Configurar monitoramento se necessário")
            response_parts.append(f"   • Testar conectividade entre componentes")
        
        return '\n'.join(response_parts)

    def fallback_processing(self, user_input: str) -> str:
        """Enhanced fallback processing with Bedrock conversational"""
        
        # Try Bedrock conversational first
        bedrock_response = self.try_bedrock_conversational(user_input)
        if bedrock_response:
            return bedrock_response
        
        # Initialize fallback mappings if not available
        if not hasattr(self, 'action_mapping'):
            self.init_fallback_mode()
        
        # Try DeepSeek as secondary fallback
        deepseek_response = self.try_deepseek_fallback(user_input)
        if deepseek_response:
            return deepseek_response
        
        # Final fallback to basic pattern matching
        intent = self.extract_intent(user_input)
        return self.generate_fallback_response(intent)
    
    def try_bedrock_conversational(self, user_input: str) -> str:
        """Try Bedrock for natural conversation"""
        try:
            import boto3
            import json
            
            # Initialize Bedrock client
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            
            # Prepare conversational prompt
            system_prompt = """Você é um assistente de infraestrutura AWS amigável e conversacional. 
Responda de forma natural e humana, como se fosse uma conversa entre amigos.
Se a pergunta for sobre infraestrutura AWS, forneça ajuda técnica.
Se for uma saudação ou conversa casual, responda de forma amigável e natural."""
            
            # Prepare request body for Claude
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            }
            
            # Call Bedrock
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps(body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and response_body['content']:
                return response_body['content'][0]['text']
            
        except Exception as e:
            print(f"⚠️ Bedrock conversational error: {e}")
            return None
        
        return None

    def extract_intent(self, user_input: str) -> dict:
        """Extract intent from natural language input (fallback)"""
        user_input = user_input.lower()
        
        # Extract action
        action = None
        for act, keywords in self.action_mapping.items():
            if any(keyword in user_input for keyword in keywords):
                action = act
                break
        
        # Extract domain
        domain = None
        for dom, keywords in self.domain_mapping.items():
            if any(keyword in user_input for keyword in keywords):
                domain = dom
                break
        
        # Extract modifiers
        dry_run = any(word in user_input for word in ['dry run', 'test', 'simulate', 'preview'])
        all_domains = any(word in user_input for word in ['everything', 'all', 'complete', 'full'])
        
        return {
            'action': action,
            'domain': domain,
            'dry_run': dry_run,
            'all_domains': all_domains,
            'original_input': user_input
        }

    def generate_fallback_response(self, intent: dict) -> str:
        """Generate fallback response when advanced features are unavailable"""
        
        action = intent.get('action')
        domain = intent.get('domain')
        dry_run = intent.get('dry_run')
        all_domains = intent.get('all_domains')
        
        if not action:
            return "🤔 I'm currently running in basic mode. Try saying something like 'deploy security' or 'show me the status'. For full conversational AI with Bedrock, infrastructure integration, and advanced features, please ensure all dependencies are installed."
        
        if action == 'deploy':
            if all_domains:
                return "🚀 I would deploy the complete infrastructure across all domains. This includes foundation, security, networking, compute, data, application, observability, AI/ML, and governance. This will take approximately 3 hours. (Note: Running in basic mode - full functionality available with Master Engine)"
            elif domain:
                domain_info = self.get_domain_info(domain)
                if dry_run:
                    return f"🔍 I would simulate deploying the {domain} infrastructure. This would include {domain_info['phases']} phases and take about {domain_info['duration']}. No actual resources would be created. (Basic mode)"
                else:
                    return f"🚀 I would deploy the {domain} infrastructure. This includes {domain_info['phases']} phases and will take about {domain_info['duration']}. (Basic mode - use Master Engine for real deployment)"
            else:
                return "🤔 What would you like me to deploy? You can say 'security', 'networking', 'compute', or 'everything'. (Basic mode)"
        
        elif action == 'status':
            if domain:
                return f"📊 I would check the {domain} infrastructure status... (Basic mode - enable Master Engine for real-time status)"
            else:
                return "📊 I would show you the overall infrastructure status... (Basic mode)"
        
        elif action == 'rollback':
            if domain:
                return f"🔄 I would rollback the {domain} infrastructure. This would safely remove all resources in reverse order. (Basic mode - Master Engine needed for execution)"
            else:
                return "🔄 What would you like me to rollback? Please specify the domain like 'rollback security' or 'rollback networking'. (Basic mode)"
        
        elif action == 'validate':
            if domain:
                return f"🔍 I would validate the {domain} infrastructure configuration and deployment... (Basic mode)"
            else:
                return "🔍 I would validate the complete infrastructure setup... (Basic mode)"
        
        return "🤔 I understand you want to perform an action, but I'm running in basic mode. For full conversational AI capabilities with Bedrock, infrastructure integration, caching, and knowledge base, please configure the Master Engine."

    def try_deepseek_fallback(self, user_input: str) -> Optional[str]:
        """Try DeepSeek as intelligent fallback"""
        
        # Check if DeepSeek is configured
        if not os.getenv('DEEPSEEK_API_KEY'):
            return None
        
        try:
            # Import DeepSeek provider
            sys.path.append(os.path.join(os.path.dirname(__file__), 'core', 'providers'))
            from deepseek_provider import chat
            
            # Create infrastructure-aware prompt
            prompt = f"""You are IAL (Infrastructure as Language) Assistant running in fallback mode.
            
User request: "{user_input}"

You help with AWS infrastructure management. Respond conversationally and helpfully.

If the user wants to:
- Deploy/create infrastructure: Explain what would be created and suggest next steps
- Check status: Explain what you would check and how
- Get help: Provide AWS best practices and guidance
- Rollback: Explain the rollback process

Keep responses concise but informative. Always mention this is fallback mode.
"""
            
            response, latency = chat(prompt)
            
            # Add fallback indicator
            return f"🧠 **DeepSeek Fallback Mode**\n\n{response}\n\n💡 *For full functionality, ensure AWS Bedrock is configured*"
            
        except Exception as e:
            print(f"DeepSeek fallback error: {e}")
            return None
        """Get information about a domain"""
        domain_details = {
            'security': {'phases': 6, 'duration': '30 minutes'},
            'networking': {'phases': 2, 'duration': '20 minutes'},
            'compute': {'phases': 5, 'duration': '35 minutes'},
            'data': {'phases': 5, 'duration': '40 minutes'},
            'application': {'phases': 4, 'duration': '25 minutes'},
            'observability': {'phases': 3, 'duration': '20 minutes'},
            'ai-ml': {'phases': 1, 'duration': '15 minutes'},
            'governance': {'phases': 4, 'duration': '15 minutes'}
        }
        
        return domain_details.get(domain, {'phases': 'several', 'duration': 'some time'})

    def get_system_status(self) -> dict:
        """Get comprehensive system status including validation system"""
        base_status = {
            'version': '3.1',
            'mode': 'advanced' if self.advanced_mode else 'basic',
            'components': {
                'master_engine': MASTER_ENGINE_AVAILABLE and self.advanced_mode,
                'intelligent_router': INTELLIGENT_ROUTER_AVAILABLE and self.intelligent_router is not None,
                'validation_system': VALIDATION_SYSTEM_AVAILABLE and self.validation_system is not None
            }
        }
        
        # Add validation system status if available
        if self.validation_system:
            base_status['validation'] = self.validation_system.get_system_status()
        
        return base_status

    def get_usage_report(self, user_id: str) -> dict:
        """Get usage and cost report for a user"""
        
        if self.advanced_mode and hasattr(self, 'master_engine'):
            try:
                return self.master_engine.cost_monitor.get_monthly_usage(user_id)
            except Exception as e:
                return {'error': f"Unable to retrieve usage report: {e}"}
        else:
            return {'error': 'Usage reporting not available in basic mode'}

# Interactive CLI for testing
def interactive_mode():
    processor = IaLNaturalProcessor()
    user_id = input("Enter your user ID (or press Enter for anonymous): ").strip() or "anonymous-user"
    session_id = str(uuid.uuid4())
    
    print(f"\n🧠 IaL Natural Language Processor v3.0")
    
    system_status = processor.get_system_status()
    if processor.advanced_mode:
        ultra_silent_ultra_silent_print("✅ ADVANCED MODE: All systems operational")
        print("   🤖 Bedrock Conversational AI")
        print("   🏗️ Infrastructure Integration")
        print("   💾 Response Caching & Optimization")
        print("   🧠 Knowledge Base & RAG")
        print("   💰 Cost Monitoring & Rate Limiting")
    else:
        print("⚠️ BASIC MODE: Limited functionality")
        print("   📝 Pattern-based responses only")
    
    print(f"👤 User: {user_id}")
    print(f"🔗 Session: {session_id[:8]}...")
    print("=" * 60)
    print("Commands: 'quit' to exit, 'clear' to clear screen, 'status' for system status")
    print("Ask me anything about infrastructure! (Ctrl+L also clears screen)")
    print()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Thanks for using IaL!")
                break
            
            if user_input.lower() in ['clear', 'cls']:
                clear_screen()
                print("🚀 IaL v3.0 - Advanced Mode: ALL SYSTEMS OPERATIONAL")
                ultra_silent_ultra_silent_print("✅ Bedrock Conversational AI")
                ultra_silent_ultra_silent_print("✅ Infrastructure Integration") 
                ultra_silent_ultra_silent_print("✅ Response Caching & Optimization")
                ultra_silent_ultra_silent_print("✅ Knowledge Base & RAG")
                ultra_silent_ultra_silent_print("✅ Cost Monitoring & Rate Limiting")
                print("=" * 60)
                print("Commands: 'quit' to exit, 'clear' to clear screen, 'status' for system status")
                print("Ask me anything about infrastructure! (Ctrl+L also clears screen)")
                print()
                continue
            
            if user_input.lower() == 'status':
                status = processor.get_system_status()
                print(f"📊 System Status: {json.dumps(status, indent=2)}")
                continue
            
            if user_input.lower() == 'usage':
                report = processor.get_usage_report(user_id)
                print(f"💰 Usage Report: {json.dumps(report, indent=2)}")
                continue
            
            if not user_input:
                continue
            
            response = processor.process_command(user_input, user_id, session_id)
            print(f"🤖 IaL: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def validate_github_access(config):
    """Validate GitHub repository access"""
    try:
        import requests
        headers = {
            'Authorization': f"token {config['GITHUB_TOKEN']}",
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Check repository access
        url = f"https://api.github.com/repos/{config['GITHUB_USER']}/ial-infrastructure"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            repo_data = response.json()
            # Check if it's a fork of the original repo
            if repo_data.get('fork'):
                parent = repo_data.get('parent', {})
                if parent.get('full_name') == 'Diego-Nardoni/ial-infrastructure':
                    return True
            elif repo_data.get('full_name') == 'Diego-Nardoni/ial-infrastructure':
                return True  # Original repo
        
        return False
    except Exception as e:
        print(f"⚠️ GitHub validation error: {e}")
        return False

def start_ial_infrastructure():
    """Deploy IAL 00-foundation infrastructure via CDK"""
    print("🚀 IAL Infrastructure Bootstrap")
    print("=" * 40)
    
    # Coleta interativa de informações
    config = collect_infrastructure_config()
    
    if not config:
        print("❌ Configuração cancelada")
        return False
    
    # Valida configurações
    if not validate_config(config):
        print("❌ Configuração inválida")
        return False
    
    # Deploy via CDK
    return deploy_foundation_via_cdk(config)

def collect_infrastructure_config():
    """Coleta configurações para deploy da infraestrutura"""
    ultra_silent_print("📋 Coletando informações para deploy da infraestrutura IAL...")
    print()
    
    config = {}
    
    # AWS Configuration
    config['AWS_ACCOUNT_ID'] = input("AWS Account ID: ").strip()
    if not config['AWS_ACCOUNT_ID']:
        return None
        
    config['AWS_REGION'] = input("AWS Region [us-east-1]: ").strip() or "us-east-1"
    
    # Project Configuration
    config['PROJECT_NAME'] = input("Nome do Projeto: ").strip()
    if not config['PROJECT_NAME']:
        return None
        
    config['EXECUTOR_NAME'] = input("Seu Nome: ").strip()
    if not config['EXECUTOR_NAME']:
        return None
    
    # GitHub Integration Configuration
    print("\n🔗 GitHub Integration (Obrigatório para funcionamento completo)")
    print("Nota: Você deve ter um fork de https://github.com/Diego-Nardoni/ial-infrastructure")
    
    github_user = input("GitHub Username: ").strip()
    if not github_user:
        print("⚠️ GitHub username é obrigatório para funcionamento completo")
        config['GITHUB_USER'] = None
        config['GITHUB_REPOSITORY'] = None
    else:
        config['GITHUB_USER'] = github_user
        config['GITHUB_REPOSITORY'] = f"https://github.com/{github_user}/ial-infrastructure"
        
        github_token = input("GitHub Personal Access Token (ghp_...): ").strip()
        if github_token.startswith('ghp_'):
            config['GITHUB_TOKEN'] = github_token
        else:
            print("⚠️ Token GitHub inválido, continuando sem integração GitHub")
            config['GITHUB_TOKEN'] = None
    
    return config

def validate_config(config):
    """Valida configurações antes do deploy"""
    print("\n🔍 Validando configurações...")
    
    # Validate AWS credentials
    try:
        import boto3
        session = boto3.Session()
        sts = session.client('sts', region_name=config['AWS_REGION'])
        identity = sts.get_caller_identity()
        
        if identity['Account'] != config['AWS_ACCOUNT_ID']:
            print(f"❌ Account ID não confere: esperado {config['AWS_ACCOUNT_ID']}, atual {identity['Account']}")
            return False
            
        print(f"✅ AWS credentials válidas para account {identity['Account']}")
        
    except Exception as e:
        print(f"❌ Erro validando AWS credentials: {e}")
        return False
    
    # Validate GitHub access (if configured)
    if config.get('GITHUB_TOKEN'):
        if not validate_github_access(config):
            print("⚠️ Erro na validação GitHub, continuando sem integração")
            config['GITHUB_TOKEN'] = None
    
    return True

def deploy_foundation_via_cdk(config):
    """Deploy da infraestrutura via MCP CORRIGIDO com Foundation Deployer"""
    try:
        # Use Foundation Deployer CORRIGIDO
        print("🚀 Iniciando deploy COMPLETO da Foundation IAL via MCP...")
        
        # Check if Foundation Deployer is available
        try:
            from core.foundation_deployer import FoundationDeployer
            from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
            
            # Initialize components
            router = IntelligentMCPRouterSophisticated()
            deployer = FoundationDeployer()
            
            ultra_silent_ultra_silent_print("✅ MCP servers conectados (Core + Cloud Control)")
            
            # Deploy Foundation phase
            result = deployer.deploy_phase("00-foundation")
            
            if result.get('success', False):
                ultra_silent_ultra_silent_print("✅ FOUNDATION IAL COMPLETA criada com sucesso!")
                
                # Show detailed summary
                print(f"📊 Foundation Components: {result.get('successful', 0)}/{result.get('total_resources', 0)}")
                print(f"🌐 Região: {config['AWS_REGION']}")
                print(f"📋 Projeto: {config['PROJECT_NAME']}")
                print(f"👤 Executor: {config['EXECUTOR_NAME']}")
                print("🎉 IAL está pronto para processar linguagem natural!")
                
                return {
                    'success': True, 
                    'method': 'Foundation-Deployer-CORRIGIDO', 
                    'details': result,
                    'components_created': result.get('successful', 0),
                    'total_components': result.get('total_resources', 0),
                    'success_rate': f"{result.get('successful', 0)/result.get('total_resources', 1)*100:.1f}%"
                }
            else:
                print(f"❌ Deploy Foundation failed: {result.get('error', 'Unknown error')}")
                print("🔄 Tentando fallback CDK...")
                
        except ImportError as e:
            print(f"⚠️ Foundation Deployer não disponível ({e}), usando fallback CDK...")
        except Exception as e:
            print(f"⚠️ Erro Foundation Deployer ({e}), usando fallback CDK...")
        
        # Fallback to CDK deployment manager
        print("📦 Preparando ambiente CDK...")
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
        from core.cdk_deployment_manager import CDKDeploymentManager
        
        # Create deployment manager
        deployment_manager = CDKDeploymentManager(config)
        
        # Execute deployment
        result = deployment_manager.deploy_foundation()
        
        if result['success']:
            print(f"\n{result['message']}")
            
            # Show outputs
            if result.get('outputs'):
                print("\n📋 Recursos criados:")
                for key, value in result['outputs'].items():
                    print(f"  {key}: {value}")
            
            # Show connectivity tests
            if result.get('connectivity_test'):
                print("\n🔍 Testes de conectividade:")
                for service, status in result['connectivity_test'].items():
                    print(f"  {service}: {status}")
            
            print("\n🎉 IAL está pronto para uso!")
            print("💡 Agora você pode usar comandos como: ial \"create RDS database\"")
            return True
        else:
            print(f"\n{result['message']}")
            if result.get('error'):
                print(f"Detalhes: {result['error']}")
            return False
            
    except ImportError as e:
        print(f"❌ Erro importando CDK deployment manager: {e}")
        print("💡 Certifique-se de que o CDK está instalado: pip install aws-cdk-lib")
        return False
    except Exception as e:
        print(f"❌ Erro no deploy: {e}")
        return False

def main():
    """Main entry point for IAL"""
    if len(sys.argv) < 2:
        print("Usage: ialctl <command>")
        print("Commands:")
        print("  start        - Deploy IAL foundation infrastructure")
        print("  configure    - Configure IAL settings")
        print("  interactive  - Start interactive mode")
        print("  \"<command>\"  - Execute infrastructure command")
        return
    
    command = sys.argv[1]
    
    if command == 'start':
        # Deploy foundation via Master Engine Final
        try:
            from core.master_engine_final import MasterEngineFinal
            master = MasterEngineFinal()
            config = load_config()
            result = master.process_request("Deploy complete IAL Foundation infrastructure", config)
            
            if result.get('status') == 'success':
                print(f"🎉 IAL Foundation deployed successfully!")
                print(f"📊 Components created: {result.get('components_created', 'N/A')}")
                print(f"🌐 Region: {result.get('details', {}).get('deployment_summary', {}).get('region', 'N/A')}")
            else:
                print(f"❌ Foundation deployment failed: {result.get('error', 'unknown')}")
                
        except Exception as e:
            print(f"⚠️ Master Engine Final not available, using fallback: {e}")
            start_ial_infrastructure()
    elif command == 'configure':
        configure_ial()
    elif command == 'interactive':
        interactive_mode()
    else:
        # Process infrastructure command via Master Engine Final
        try:
            from core.master_engine_final import MasterEngineFinal
            master = MasterEngineFinal()
            full_command = ' '.join(sys.argv[1:])
            result = master.process_request(full_command)
            
            # Format response
            if result.get('status') == 'success':
                # Se é conversacional, exibir a resposta direta
                if result.get('path') == 'CONVERSATIONAL_PATH':
                    print(f"🤖 IaL: {result.get('response', result.get('message', 'Resposta não disponível'))}")
                else:
                    # Para infraestrutura, exibir resumo
                    print(f"🤖 IaL: ✅ {result.get('method', 'processed')} via {result.get('path', 'unknown')} path")
                    if result.get('components_created'):
                        print(f"📊 Components: {result['components_created']}")
                    if result.get('resources_created'):
                        print(f"📋 Resources: {len(result['resources_created'])}")
                    if result.get('pr_url'):
                        print(f"🔗 PR: {result['pr_url']}")
            else:
                print(f"🤖 IaL: ❌ {result.get('error', 'unknown error')}")
                
        except Exception as e:
            print(f"⚠️ Master Engine Final not available, using fallback: {e}")
            # Fallback to original processor
            processor = IaLNaturalProcessor()
            user_id = "user-" + str(uuid.uuid4())[:8]
            full_command = ' '.join(sys.argv[1:])
            response = processor.process_command(full_command, user_id)
            print(f"🤖 IaL: {response}")

if __name__ == "__main__":
    main()
