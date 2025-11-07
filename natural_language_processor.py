#!/usr/bin/env python3
"""
IaL Natural Language Processor v3.1
Complete system with all phases integrated + Intelligent MCP Router + Intent Validation
"""

import sys
import os
import uuid
import json
import readline
import asyncio
from typing import Dict, List, Optional

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
    from ial_master_engine import IaLMasterEngine
    MASTER_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Master Engine not available: {e}")
    MASTER_ENGINE_AVAILABLE = False

# Try to import Intelligent MCP Router
try:
    from core.intelligent_mcp_router import IntelligentMCPRouter
    INTELLIGENT_ROUTER_AVAILABLE = True
    print("🧠 Intelligent MCP Router disponível")
except ImportError as e:
    print(f"⚠️ Intelligent MCP Router not available: {e}")
    INTELLIGENT_ROUTER_AVAILABLE = False

# Try to import Intent Validation System
try:
    from intent_validation import ValidationSystem
    VALIDATION_SYSTEM_AVAILABLE = True
    print("🛡️ Sistema de Validação de Intenção disponível")
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
                print("✅ Sistema de Validação de Intenção inicializado")
            except Exception as e:
                print(f"⚠️ Erro inicializando Validation System: {e}")
                self.validation_system = None
        
        # Initialize Intelligent MCP Router
        self.intelligent_router = None
        if INTELLIGENT_ROUTER_AVAILABLE:
            try:
                self.intelligent_router = IntelligentMCPRouter()
            except Exception as e:
                print(f"⚠️ Erro inicializando Intelligent Router: {e}")
                self.intelligent_router = None
        
        if MASTER_ENGINE_AVAILABLE:
            try:
                self.master_engine = IaLMasterEngine()
                self.advanced_mode = True
                print("🚀 IaL v3.1 - Advanced Mode: ALL SYSTEMS OPERATIONAL")
                print("✅ Bedrock Conversational AI")
                print("✅ Infrastructure Integration") 
                print("✅ Response Caching & Optimization")
                print("✅ Knowledge Base & RAG")
                print("✅ Cost Monitoring & Rate Limiting")
                if self.intelligent_router:
                    print("✅ Intelligent MCP Router")
                if self.validation_system:
                    print("✅ Intent Validation System")
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
                print("🧠 Usando Intelligent MCP Router")
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
                
                # Extract response and add metadata info if needed
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
            'ecs', 'lambda', 'rds', 'elb', 'vpc', 's3', 'dynamodb',
            'infrastructure', 'architecture', 'serverless', 'container'
        ]
        
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in infrastructure_keywords)

    def process_with_intelligent_router(self, user_input: str, user_id: str, session_id: str) -> str:
        """Processa usando o router inteligente"""
        context = {
            'user_id': user_id,
            'session_id': session_id or str(uuid.uuid4()),
            'timestamp': __import__('time').time()
        }
        
        # Executar roteamento inteligente (síncrono)
        try:
            # Usar asyncio para executar função async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.intelligent_router.route_request(user_input, context)
            )
            loop.close()
            
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
        
        # Construir resposta baseada no resultado
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
        """Enhanced fallback processing with DeepSeek"""
        
        # Initialize fallback mappings if not available
        if not hasattr(self, 'action_mapping'):
            self.init_fallback_mode()
        
        # Try DeepSeek first (intelligent fallback)
        deepseek_response = self.try_deepseek_fallback(user_input)
        if deepseek_response:
            return deepseek_response
        
        # Fallback to basic pattern matching
        intent = self.extract_intent(user_input)
        return self.generate_fallback_response(intent)

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
        print("✅ ADVANCED MODE: All systems operational")
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
                print("✅ Bedrock Conversational AI")
                print("✅ Infrastructure Integration") 
                print("✅ Response Caching & Optimization")
                print("✅ Knowledge Base & RAG")
                print("✅ Cost Monitoring & Rate Limiting")
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
    print("📋 Coletando informações para deploy da infraestrutura IAL...")
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
    """Deploy da infraestrutura via MCP (NEW) com fallback CDK"""
    try:
        # Try MCP Infrastructure Manager first
        print("🚀 Iniciando deploy da infraestrutura IAL via MCP...")
        
        # Check if Intelligent MCP Router is available
        try:
            from core.intelligent_mcp_router import IntelligentMCPRouter
            from core.mcp_infrastructure_manager import MCPInfrastructureManager
            
            # Initialize MCP infrastructure manager
            router = IntelligentMCPRouter()
            infra_manager = MCPInfrastructureManager(router)
            
            # Validate MCP connectivity
            import asyncio
            if asyncio.run(infra_manager.validate_mcp_connectivity()):
                print("✅ MCP servers conectados (Core + Cloud Control)")
                
                # Deploy via MCP
                result = asyncio.run(infra_manager.deploy_ial_infrastructure(config))
                
                if result.get('deployment_summary', {}).get('status') == 'success':
                    print("✅ Infraestrutura IAL criada via MCP!")
                    
                    # Show summary
                    summary = result.get('deployment_summary', {})
                    print(f"📊 Componentes criados: {summary.get('components_created', 0)}")
                    print(f"🌐 Região: {summary.get('region', 'N/A')}")
                    print(f"📋 Projeto: {summary.get('project_name', 'N/A')}")
                    
                    return {'success': True, 'method': 'MCP', 'details': result}
                else:
                    print(f"❌ Deploy MCP failed: {result.get('error', 'Unknown error')}")
                    print("🔄 Tentando fallback CDK...")
                    
            else:
                print("⚠️ MCP servers não respondem, usando fallback CDK...")
                
        except ImportError as e:
            print(f"⚠️ MCP não disponível ({e}), usando fallback CDK...")
        except Exception as e:
            print(f"⚠️ Erro MCP ({e}), usando fallback CDK...")
        
        # Fallback to CDK deployment manager
        print("📦 Preparando ambiente CDK...")
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
        from cdk_deployment_manager import CDKDeploymentManager
        
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
        start_ial_infrastructure()
    elif command == 'configure':
        configure_ial()
    elif command == 'interactive':
        interactive_mode()
    else:
        # Process infrastructure command
        processor = IaLNaturalProcessor()
        user_id = "user-" + str(uuid.uuid4())[:8]
        
        # Join all arguments as the command
        full_command = ' '.join(sys.argv[1:])
        response = processor.process_command(full_command, user_id)
        print(f"🤖 IaL: {response}")

if __name__ == "__main__":
    main()
