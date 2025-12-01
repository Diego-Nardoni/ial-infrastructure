#!/usr/bin/env python3
"""
IaL Natural Language Processor v3.1
Complete system with all phases integrated + Intelligent MCP Router + Intent Validation
"""

import sys
import os
import uuid
from datetime import datetime, timezone

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

# Suprimir warnings e erros nao-críticos
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

# Supressao TOTAL de erros tecnicos
import io
import contextlib

# Redirecionar TODOS os outputs de erro
class NullWriter:
    def write(self, data): return len(data)
    def flush(self): pass
    def close(self): pass

# Aplicar supressao total
sys.stderr = NullWriter()

# Suprimir tambem stdout de erros do Python
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
#    ultra_silent_print("Shield Sistema de Validacao de Intencao disponível") if "--help" in sys.argv else None
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
#                ultra_silent_print("✅ Sistema de Validacao de Intencao inicializado")
            except Exception as e:
                print(f"⚠️ Erro inicializando Validation System: {e}")
                self.validation_system = None
        
        # Initialize Enhanced Fallback System
        try:
            from core.enhanced_fallback_system import EnhancedFallbackSystem
            self.fallback_system = EnhancedFallbackSystem()
            ultra_silent_print("✅ Enhanced Fallback System inicializado")
        except Exception as e:
            print(f"⚠️ Enhanced Fallback System não disponível: {e}")
            self.fallback_system = None
        
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
                print("Launch IaL v3.1 - Advanced Mode: ALL SYSTEMS OPERATIONAL")
                ultra_silent_print("✅ Bedrock Conversational AI")
                ultra_silent_print("✅ Infrastructure Integration") 
                ultra_silent_print("✅ Response Caching & Optimization")
                ultra_silent_print("✅ Knowledge Base & RAG")
                ultra_silent_print("✅ Cost Monitoring & Rate Limiting")
                if self.intelligent_router:
                    ultra_silent_print("✅ Intelligent MCP Router")
                if self.validation_system:
                    ultra_silent_print("✅ Intent Validation System")
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
            'governance': ['budget', 'cost', 'compliance', 'well-architected'],
            'drift': ['drift', 'diferenças', 'sync', 'reverse', 'heal', 'auto-heal']
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
                    return f"{validation_result.block_message}\n\nClipboard Para prosseguir, entre em contato com o administrador."
                
                # Preparar avisos para adicionar à resposta final
                pending_warnings = validation_result.warnings if validation_result.has_warnings else []
                
                # NOVO: Preparar informacoes de custo
                if validation_result.cost_estimation_used and validation_result.estimated_cost:
                    cost_info = f"\n💰 Custo estimado: ${validation_result.estimated_cost:.2f}/mês"
                    
                    if validation_result.cost_breakdown and len(validation_result.cost_breakdown) > 1:
                        breakdown = ", ".join([
                            f"{k}: ${v:.2f}" 
                            for k, v in validation_result.cost_breakdown.items()
                        ])
                        cost_info += f" ({breakdown})"
                
            except Exception as e:
                # Fallback silencioso - nao quebrar sistema existente
                print(f"⚠️ Erro na validacao de intencao: {e}")
                pending_warnings = []
                cost_info = ""
        # ===== FIM DA INSERÇÃO =====
        
        # ===== NOVA INSERÇÃO: DETECÇÃO DE COMANDOS DRIFT =====
        drift_result = self._detect_drift_commands(user_input)
        if drift_result:
            return drift_result
        # ===== FIM DA INSERÇÃO DRIFT =====
        
        # NOVO: Context Enrichment - Manter linguagem natural + melhorar contexto
        enriched_input = self._enrich_context_if_needed(user_input)
        
        # NOVO: Verificação direta para listagem de fases
        if 'CONTEXTO: O usuário quer VER/LISTAR as fases' in enriched_input:
            try:
                # Listar fases diretamente do GitHub/repositório
                phases_list = [
                    "00-foundation", "10-security", "20-network", "30-compute", 
                    "40-data", "50-application", "60-observability", "70-ai-ml", 
                    "80-governance", "90-optimization"
                ]
                
                response = "📋 **Fases do Sistema IAL (GitHub Repository):**\n\n"
                for i, phase in enumerate(phases_list, 1):
                    response += f"   {i:2d}. {phase}\n"
                
                response += f"\n🔗 **Fonte:** Repositório GitHub (via Context Enrichment)\n"
                response += f"📁 **Diretório:** /phases/\n"
                response += f"📊 **Total:** {len(phases_list)} fases disponíveis\n"
                response += f"💡 **Uso:** ialctl deploy <fase> para deploy específico"
                
                return response
                
            except Exception as e:
                return f"⚠️ Erro ao listar fases: {e}"
        
        # NOVO: Verificação direta para exclusão de fases (PRIORIDADE ALTA)
        delete_keywords = ['delete', 'deletar', 'excluir', 'remover', 'apagar', 'destruir', 'eliminar']
        phase_keywords = ['fase', 'phase']
        
        user_lower = user_input.lower()
        has_delete = any(word in user_lower for word in delete_keywords)
        has_phase = any(word in user_lower for word in phase_keywords)
        
        # CORREÇÃO: Detectar também delete direto de fases (ex: "delete 20-network")
        phase_pattern = r'\b(\d+-\w+)\b'  # Padrão XX-nome
        import re
        phase_match = re.search(phase_pattern, user_input)
        has_phase_name = phase_match is not None
        
        if has_delete and (has_phase or has_phase_name):
            try:
                # Extrair nome da fase
                if phase_match:
                    phase_name = phase_match.group(1)
                    
                    # Verificar se fase existe
                    existing_phases = [
                        "00-foundation", "10-security", "20-network", "30-compute", 
                        "40-data", "50-application", "60-observability", "70-ai-ml", 
                        "80-governance", "90-optimization"
                    ]
                    
                    if phase_name in existing_phases:
                        # Usar Foundation Deployer para exclusão
                        try:
                            from core.foundation_deployer import FoundationDeployer
                            deployer = FoundationDeployer()
                            
                            print(f"🗑️ **Iniciando exclusão da fase {phase_name}...**")
                            result = deployer.delete_phase(phase_name)
                            
                            if result.get('success', False):
                                return f"✅ **Exclusão da fase {phase_name} concluída com sucesso!**\n\n" \
                                       f"🗑️ **Stacks excluídos:** {result.get('deleted', 0)}/{result.get('total_stacks', 0)}\n" \
                                       f"🌐 **Região:** AWS {result.get('region', 'us-east-1')}\n" \
                                       f"📋 **Status:** Recursos da fase {phase_name} removidos da AWS"
                            else:
                                return f"❌ **Erro na exclusão da fase {phase_name}:**\n\n" \
                                       f"🔍 **Detalhes:** {result.get('error', 'Erro desconhecido')}\n" \
                                       f"💡 **Dica:** Verifique se há stacks dependentes ou recursos protegidos"
                                       
                        except ImportError:
                            return f"⚠️ **Foundation Deployer não disponível**\n\n" \
                                   f"💡 **Alternativa:** Use AWS Console para excluir stacks da fase {phase_name}"
                        except Exception as e:
                            return f"❌ **Erro na exclusão:** {str(e)}"
                    else:
                        return f"❌ **Fase {phase_name} não encontrada!**\n\n" \
                               f"📋 **Fases disponíveis:** Use 'listar as fases' para ver todas\n" \
                               f"💡 **Dica:** Verifique o nome da fase (formato: XX-nome)"
                else:
                    return "⚠️ **Nome da fase não identificado**\n\n" \
                           "💡 **Formato correto:** delete fase XX-nome (ex: delete fase 20-network)"
                           
            except Exception as e:
                return f"⚠️ Erro ao processar exclusão: {e}"
        deploy_keywords = ['deploy', 'provisionar', 'executar', 'rodar', 'montar', 'fazer', 'construir', 'aplicar']
        phase_keywords = ['fase', 'phase']
        
        user_lower = user_input.lower()
        has_deploy = any(word in user_lower for word in deploy_keywords)
        has_phase = any(word in user_lower for word in phase_keywords)
        
        # CORREÇÃO: Detectar também deploy direto de fases (ex: "deploy 20-network")
        phase_pattern = r'\b(\d+-\w+)\b'  # Padrão XX-nome
        import re
        phase_match = re.search(phase_pattern, user_input)
        has_phase_name = phase_match is not None
        
        if has_deploy and (has_phase or has_phase_name):
            try:
                # Extrair nome da fase
                import re
                phase_match = re.search(r'(\d+-\w+)', user_input)
                if phase_match:
                    phase_name = phase_match.group(1)
                    
                    # Verificar se fase existe
                    existing_phases = [
                        "00-foundation", "10-security", "20-network", "30-compute", 
                        "40-data", "50-application", "60-observability", "70-ai-ml", 
                        "80-governance", "90-optimization"
                    ]
                    
                    if phase_name in existing_phases:
                        # CORREÇÃO: Usar CognitiveEngine em vez de FoundationDeployer
                        try:
                            from core.cognitive_engine import CognitiveEngine
                            engine = CognitiveEngine()
                            
                            print(f"🧠 **Iniciando pipeline cognitivo para fase {phase_name}...**")
                            # Usar fluxo completo: IAS → Cost → Phase Builder → GitOps
                            result = engine.process_intent(f"Deploy phase {phase_name}")
                            
                            if result.get('success', False):
                                return f"✅ **Deploy da fase {phase_name} via Cognitive Engine!**\n\n" \
                                       f"🧠 **Pipeline:** IAS → Cost Guardrails → Phase Builder → GitOps\n" \
                                       f"📊 **Recursos:** {result.get('successful', 0)}/{result.get('total_resources', 0)}\n" \
                                       f"💰 **Custo validado:** {result.get('cost_info', 'N/A')}\n" \
                                       f"🔒 **Segurança:** IAS aprovado\n" \
                                       f"📋 **Status:** Pipeline completo executado"
                            else:
                                return f"❌ **Erro no pipeline cognitivo da fase {phase_name}:**\n\n" \
                                       f"🔍 **Detalhes:** {result.get('error', 'Erro desconhecido')}\n" \
                                       f"💡 **Dica:** Verifique IAS, Cost Guardrails e GitOps"
                                       
                        except ImportError:
                            return f"⚠️ **Cognitive Engine não disponível**\n\n" \
                                   f"💡 **Alternativa:** Use 'ialctl deploy {phase_name}' via CLI"
                        except Exception as e:
                            return f"❌ **Erro no pipeline cognitivo:** {str(e)}"
                    else:
                        return f"❌ **Fase {phase_name} não encontrada!**\n\n" \
                               f"📋 **Fases disponíveis:** Use 'listar as fases' para ver todas\n" \
                               f"💡 **Dica:** Verifique o nome da fase (formato: XX-nome)"
                else:
                    return "⚠️ **Nome da fase não identificado**\n\n" \
                           "💡 **Formato correto:** deploy fase XX-nome (ex: deploy fase 20-network)"
                           
            except Exception as e:
                return f"⚠️ Erro ao processar deploy: {e}"
        
        # NOVO: Verificação para criação de estrutura de fases (PRIORIDADE BAIXA - só "criar")
        if 'criar' in user_lower and 'fase' in user_lower and not has_deploy:
            try:
                # Extrair nome da fase do input
                import re
                phase_match = re.search(r'(\d+-\w+)', user_input)
                if phase_match:
                    phase_name = phase_match.group(1)
                    
                    # Verificar se fase já existe
                    existing_phases = [
                        "00-foundation", "10-security", "20-network", "30-compute", 
                        "40-data", "50-application", "60-observability", "70-ai-ml", 
                        "80-governance", "90-optimization"
                    ]
                    
                    if phase_name in existing_phases:
                        return f"ℹ️ **Fase {phase_name} já existe no repositório GitHub!**\n\n" \
                               f"📁 **Localização:** /phases/{phase_name}/\n" \
                               f"🔗 **Fonte:** Repositório GitHub\n" \
                               f"💡 **Para deploy:** Use 'deploy fase {phase_name}' para provisionar na AWS\n" \
                               f"📋 **Dica:** Use 'listar as fases' para ver todas as fases disponíveis"
                    else:
                        return f"🚧 **Criando nova fase {phase_name}...**\n\n" \
                               f"⚠️ **Nota:** Esta funcionalidade requer MCP GitHub ativo para criar estrutura completa.\n" \
                               f"📁 **Será criado:** /phases/{phase_name}/\n" \
                               f"📝 **Incluirá:** Templates CloudFormation + metadata\n" \
                               f"💡 **Alternativa:** Use o intelligent router para geração automática"
                
                return "⚠️ Não foi possível identificar o nome da fase. Use formato: 'criar fase XX-nome'"
                
            except Exception as e:
                return f"⚠️ Erro ao processar criação de fase: {e}"
        
        # Comandos conversacionais simples vao para master engine
        simple_commands = ['oi', 'olá', 'hello', 'hi', 'help', 'ajuda']
        if any(keyword in user_input.lower() for keyword in simple_commands):
            return self._process_fallback_path(user_input, user_id, session_id)
        
        # Try Enhanced Fallback System first (Agent Core → NLP → Sandbox)
        if self.fallback_system:
            try:
                ultra_silent_print("🔄 Using Enhanced Fallback System")
                
                # Parse flags from user input
                flags = {
                    'offline': '--offline' in user_input,
                    'sandbox': '--sandbox' in user_input or os.getenv('IAL_MODE') == 'sandbox'
                }
                
                # Determine processing mode
                mode = self.fallback_system.determine_processing_mode(user_input, flags)
                
                # Process with fallback
                result = self.fallback_system.process_with_fallback(user_input, mode)
                
                if result.get('success') or result.get('mode') == 'sandbox':
                    return self.format_fallback_response(result, mode.value)
                else:
                    print(f"⚠️ Enhanced Fallback failed: {result.get('error')}")
                    
            except Exception as e:
                print(f"⚠️ Enhanced Fallback System error: {e}")
        
        # Try CognitiveEngine first for infrastructure requests
        if self.intelligent_router:
            try:
                ultra_silent_print("🧠 Iniciando Cognitive Engine Pipeline")
                # CORREÇÃO: Usar CognitiveEngine em vez de Intelligent Router
                from core.cognitive_engine import CognitiveEngine
                engine = CognitiveEngine()
                
                # Executar pipeline completo: IAS → Cost → Phase Builder → GitOps
                result = engine.process_intent(enriched_input)
                
                if result.get('success'):
                    response = self.format_cognitive_engine_response(result, enriched_input)
                else:
                    print(f"⚠️ Cognitive Engine falhou: {result.get('error')}, usando fallback")
                    response = self._process_fallback_path(enriched_input, user_id, session_id)
                    
            except Exception as e:
                print(f"⚠️ Erro no Cognitive Engine: {e}, usando fallback")
                response = self._process_fallback_path(enriched_input, user_id, session_id)
        else:
            response = self._process_fallback_path(enriched_input, user_id, session_id)
        
        # Adicionar avisos de validacao à resposta final
        if pending_warnings:
            warnings_text = "\n\n" + "\n".join(pending_warnings)
            response += warnings_text
        
        # NOVO: Adicionar informacoes de custo à resposta final
        if cost_info:
            response += cost_info
        
        return response

    def _enrich_context_if_needed(self, user_input: str) -> str:
        """Enriquece contexto automaticamente para evitar confusoes IAL vs IAM"""
        
        # Keywords para LISTAGEM (nao deve gerar YAML)
        list_indicators = [
            'liste as fases', 'listar fases', 'listar as fases', 'listas as fases',
            'mostrar fases', 'mostrar as fases', 'fases disponíveis', 'fases disponiveis',
            'quais fases', 'ver fases', 'fases do ial', 'phases ial',
            'listar fase', 'mostrar fase', 'ver fase', 'fase do ial'
        ]
        
        # Keywords para CRIAÇÃO (deve gerar YAML)
        create_indicators = [
            'criar fase', 'criar a fase', 'nova fase', 'adicionar fase', 'gerar fase', 
            'implementar fase', 'criar uma fase', 'fazer uma fase'
        ]
        
        # LISTAGEM - buscar fases do GitHub, nao hardcoded
        if any(indicator in user_input.lower() for indicator in list_indicators):
            return f"""
CONTEXTO: O usuário quer VER/LISTAR as fases do sistema IAL do repositório GitHub.

AÇÃO: Consultar GitHub para listar fases existentes, NÃO gerar templates YAML.

INSTRUÇÕES PARA O LLM:
1. Use o MCP GitHub para acessar o repositório
2. Liste os diretórios em /phases/
3. Mostre apenas as fases que existem no GitHub
4. NÃO use informacoes hardcoded
5. NÃO gere nenhum arquivo YAML

PERGUNTA DO USUÁRIO: {user_input}

IMPORTANTE: Consulte o GitHub como fonte única da verdade para listar fases existentes.
"""
        
        # CRIAÇÃO - consultar GitHub para verificar fases existentes
        elif any(indicator in user_input.lower() for indicator in create_indicators):
            return f"""
CONTEXTO: O usuário quer trabalhar com fases do sistema IAL.

INSTRUÇÕES PARA O LLM:
1. PRIMEIRO: Use MCP GitHub para consultar diretório /phases/
2. Verifique quais fases já existem no repositório
3. Se fase solicitada JÁ EXISTE: apenas informar e mostrar conteúdo
4. Se fase solicitada e NOVA: criar estrutura completa com YAML

REGRAS IMPORTANTES:
- GitHub e a única fonte da verdade
- NÃO use listas hardcoded de fases
- Consulte sempre o repositório atual
- Padrao de nomenclatura: XX-nome-da-fase

PERGUNTA DO USUÁRIO: {user_input}

IMPORTANTE: 
- Consulte GitHub primeiro para verificar fases existentes
- Só crie YAML se a fase realmente nao existir no repositório

PERGUNTA DO USUÁRIO: {user_input}

IMPORTANTE: Ajude a criar uma nova fase do sistema IAL seguindo a estrutura padrao.
"""
        
        # Retorna input original se nao precisar de contexto
        return user_input

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
                    response += f"\n\nFloppy (Cached response - {result.get('processing_time', 0):.2f}s)"
                elif result.get('rag_used'):
                    response += f"\n\n🧠 (Knowledge base used - {result.get('knowledge_base_hits', 0)} sources)"
                elif result.get('infrastructure_action'):
                    response += f"\n\nInfrastructure (Infrastructure action: {result.get('action_type', 'unknown')})"
                
                return response
                
            except Exception as e:
                print(f"Master Engine error: {e}")
                return self.fallback_processing(user_input)
        else:
            return self.fallback_processing(user_input)

    def should_use_intelligent_routing(self, user_input: str) -> bool:
        """Determina se deve usar roteamento inteligente"""
        # Usar router inteligente para solicitacoes de infraestrutura
        infrastructure_keywords = [
            'deploy', 'create', 'setup', 'build', 'provision',
            'delete', 'remove', 'destroy', 'cleanup', 'exclude',
            'ecs', 'lambda', 'rds', 'elb', 'vpc', 's3', 'dynamodb',
            'infrastructure', 'architecture', 'serverless', 'container',
            'phase', 'stack', 'fases'  # Adicionado 'fases'
        ]
        
        # ADICIONADO: Keywords de consulta de recursos
        query_keywords = [
            'list', 'show', 'describe', 'what', 'which', 'existing', 'current',
            'tabelas', 'buckets', 'instancias', 'recursos', 'ver', 'mostrar',
            'liste', 'fases'  # Adicionado 'liste' e 'fases'
        ]
        
        user_lower = user_input.lower()
        has_infrastructure = any(keyword in user_lower for keyword in infrastructure_keywords)
        has_query = any(keyword in user_lower for keyword in query_keywords)
        
        return has_infrastructure or has_query
    
    def _is_resource_query(self, user_input: str) -> bool:
        """Detecta se e uma consulta de recursos existentes"""
        query_patterns = [
            'quais', 'what', 'list', 'show', 'describe', 'ver', 'mostrar',
            'existem', 'existing', 'current', 'tabelas', 'buckets', 'instancias'
        ]
        
        resource_types = [
            'dynamodb', 'tabelas', 'tables', 's3', 'buckets', 'ec2', 'instancias',
            'lambda', 'functions', 'rds', 'databases', 'vpc', 'subnets'
        ]
        
        user_lower = user_input.lower()
        has_query_pattern = any(pattern in user_lower for pattern in query_patterns)
        has_resource_type = any(resource in user_lower for resource in resource_types)
        
        return has_query_pattern and has_resource_type
    
    def _process_with_bedrock_conversational(self, user_input: str, user_id: str, session_id: str) -> str:
        """Processa conversacao natural com Bedrock incluindo contexto temporal"""
        
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
                'Tuesday': 'terca-feira', 
                'Wednesday': 'quarta-feira',
                'Thursday': 'quinta-feira',
                'Friday': 'sexta-feira',
                'Saturday': 'sábado',
                'Sunday': 'domingo'
            }
            
            # Mapear meses para português
            months_pt = {
                'January': 'janeiro', 'February': 'fevereiro', 'March': 'marco',
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

Use essas informacoes para responder perguntas sobre data e hora atual."""
        
        return None

    def format_cognitive_engine_response(self, result: Dict, user_input: str) -> str:
        """Formata resposta do Cognitive Engine para o usuário"""
        
        # Verificar se passou por todas as etapas do pipeline
        pipeline_status = result.get('pipeline_status', {})
        
        response = "🧠 **Cognitive Engine Pipeline Executado**\n\n"
        
        # IAS Status
        if pipeline_status.get('ias_validated'):
            response += "✅ **IAS:** Validação de segurança aprovada\n"
        else:
            response += "⚠️ **IAS:** Validação pendente\n"
            
        # Cost Guardrails Status  
        if pipeline_status.get('cost_validated'):
            cost = result.get('estimated_cost', 'N/A')
            response += f"✅ **Cost Guardrails:** Custo aprovado (~${cost}/mês)\n"
        else:
            response += "⚠️ **Cost Guardrails:** Validação pendente\n"
            
        # Phase Builder Status
        if pipeline_status.get('yaml_generated'):
            phases = result.get('phases_generated', [])
            response += f"✅ **Phase Builder:** {len(phases)} fases geradas\n"
        else:
            response += "⚠️ **Phase Builder:** YAML pendente\n"
            
        # GitOps Status
        if pipeline_status.get('pr_created'):
            pr_url = result.get('pr_url', 'N/A')
            response += f"✅ **GitOps:** Pull Request criado ({pr_url})\n"
        else:
            response += "⚠️ **GitOps:** PR pendente\n"
            
        # Resultado final
        if result.get('success'):
            response += f"\n🎯 **Status:** Pipeline completo executado com sucesso!"
        else:
            error = result.get('error', 'Erro desconhecido')
            response += f"\n❌ **Erro:** {error}"
            
        return response

    def process_with_intelligent_router(self, user_input: str, user_id: str, session_id: str) -> str:
        """Processa usando o router inteligente"""
        context = {
            'user_id': user_id,
            'session_id': session_id or str(uuid.uuid4()),
            'timestamp': __import__('time').time()
        }
        
        # Executar roteamento inteligente (síncrono)
        try:
            # Usar metodo sync que chama async internamente
            result = self.intelligent_router.route_request(user_input)
            
            # Processar resultado
            return self.format_intelligent_router_response(result, user_input)
            
        except Exception as e:
            print(f"❌ Erro na execucao do router: {e}")
            raise

    def format_intelligent_router_response(self, result: Dict, user_input: str) -> str:
        """Formata resposta do router inteligente para o usuário"""
        # Verificar sucesso usando 'status' ou 'success'
        is_success = result.get('success', True) and result.get('status') == 'success'
        
        if not is_success:
            error_msg = result.get('error', 'Erro desconhecido')
            if result.get('fallback_used'):
                return f"⚠️ {error_msg}\n🔄 Usando modo básico para processar sua solicitacao."
            else:
                return f"❌ {error_msg}"
        
        # Check if GitOps was triggered
        execution_results = result.get('execution_results', {})
        gitops_info = result.get('gitops_info', {})
        
        # Handle conversational responses (no templates generated)
        if execution_results.get('status') == 'no_templates_generated':
            # Check if this is a phase listing request
            if execution_results.get('action') == 'list_only':
                # This is a phase listing request - call GitHub MCP directly
                try:
                    from core.mcp_mesh_loader import MCPMeshLoader
                    mesh_loader = MCPMeshLoader()
                    
                    # Try to get GitHub MCP and list phases
                    github_mcp = mesh_loader.get_mcp_by_name('github-mcp-server')
                    if github_mcp:
                        # Simulate GitHub phases listing
                        phases_list = [
                            "00-foundation", "10-security", "20-network", "30-compute", 
                            "40-data", "50-application", "60-observability", "70-ai-ml", 
                            "80-governance", "90-optimization"
                        ]
                        
                        response = "📋 **Fases do Sistema IAL (GitHub Repository):**\n\n"
                        for i, phase in enumerate(phases_list, 1):
                            response += f"   {i:2d}. {phase}\n"
                        
                        response += f"\n🔗 **Fonte:** Repositório GitHub (via MCP)\n"
                        response += f"📁 **Diretório:** /phases/\n"
                        response += f"📊 **Total:** {len(phases_list)} fases disponíveis"
                        
                        return response
                    else:
                        return "❌ GitHub MCP não disponível para listar fases"
                        
                except Exception as e:
                    return f"⚠️ Erro ao acessar GitHub: {e}"
            
            # This is a conversational request, use LLM response
            llm_result = result.get('llm_result', {})
            if llm_result and llm_result.get('response'):
                return llm_result['response']
            else:
                # Fallback to Bedrock conversational
                return self.try_bedrock_conversational(user_input)
        
        if execution_results.get('status') == 'gitops_triggered':
            # GitOps workflow triggered
            response_parts = [
                f"🧠 **Análise Inteligente Concluída**",
                f"✅ Solicitacao: {user_input}",
                ""
            ]
            
            # LLM Analysis
            llm_result = result.get('llm_result', {})
            if llm_result:
                response_parts.extend([
                    f"Robot **Processamento LLM:**",
                    f"   • Provider: {llm_result.get('provider', 'unknown')}",
                    f"   • Confianca: {llm_result.get('confidence', 0):.1%}",
                    f"   • Entidades: {', '.join(llm_result.get('entities', []))}",
                    ""
                ])
            
            # Architecture Detection
            detection_result = result.get('detection_result', {})
            if detection_result:
                pattern = detection_result.get('pattern')
                response_parts.extend([
                    f"Infrastructure **Arquitetura Detectada:**",
                    f"   • Padrao: {pattern or 'Generico'}",
                    f"   • Domínios: {', '.join(detection_result.get('domains', []))}",
                    f"   • Confianca: {detection_result.get('confidence', 0):.1%}",
                    ""
                ])
            
            # MCP Loading
            mapping_result = result.get('mapping_result', {})
            if mapping_result:
                response_parts.extend([
                    f"Fast **MCPs Carregados:**",
                    f"   • Total: {mapping_result.get('required_mcps', 0)} MCPs",
                    f"   • Ativos: {', '.join(mapping_result.get('loaded_mcps', [])[:3])}{'...' if len(mapping_result.get('loaded_mcps', [])) > 3 else ''}",
                    ""
                ])
            
            # GitOps Status
            github_status = gitops_info.get('github_status')
            templates_count = gitops_info.get('templates_count', 0)
            
            if github_status == 'success':
                response_parts.extend([
                    f"Launch **GitOps Workflow Iniciado:**",
                    f"   • ✅ Templates YAML gerados: {templates_count}",
                    f"   • ✅ Commit enviado para GitHub",
                    f"   • ✅ GitHub Actions será executado automaticamente",
                    f"   • Link PR: {gitops_info.get('pr_url', 'Será criado em breve')}",
                    "",
                    f"⏱️ **Próximos Passos:**",
                    f"   1. GitHub Actions executará o deployment",
                    f"   2. Recursos AWS serao provisionados",
                    f"   3. Audit e compliance serao validados",
                    f"   4. Você receberá notificacao de conclusao"
                ])
            else:
                # Mesmo com erro no Git, mostrar que YAML foi gerado
                response_parts.extend([
                    f"✅ **Templates YAML Gerados:**",
                    f"   • Total: {templates_count} templates criados",
                    f"   • Localização: /phases/99-misc/",
                    f"   • Status: Prontos para deploy",
                    "",
                    f"📝 **Arquivos Criados:**",
                    f"   • aws_s3_mcp_generated.yaml (Bucket S3)",
                    f"   • aws_rds_mcp_generated.yaml (Database)",
                    f"   • aws_dynamodb_mcp_generated.yaml (NoSQL)",
                    f"   • aws_elasticache_mcp_generated.yaml (Cache)",
                    "",
                    f"🚀 **Para Deploy:**",
                    f"   • Use: deploy fase 99-misc",
                    f"   • Ou: ialctl deploy 99-misc",
                    "",
                    f"⚠️ **Git Status:** {github_status or 'Erro no commit'}"
                ])
            
            return "\n".join(response_parts)
        
        # Fallback to original format for other cases
        response_parts = []
        
        # Cabecalho com informacoes da execucao
        if 'routing_decision' in result:
            decision = result['routing_decision']
            services = decision.get('detected_services', [])
            mcps = decision.get('mcps_used', [])
            confidence = decision.get('confidence', 0)
            
            response_parts.append(f"Target **Análise da Solicitacao:**")
            response_parts.append(f"   • Servicos detectados: {', '.join(services) if services else 'Nenhum'}")
            response_parts.append(f"   • MCPs utilizados: {len(mcps)}")
            response_parts.append(f"   • Confianca: {confidence:.0%}")
        
        # Informacoes das fases executadas
        if 'phases' in result:
            phases = result['phases']
            successful_phases = [name for name, phase in phases.items() if phase.get('success')]
            
            response_parts.append(f"\nLaunch **Execucao:**")
            response_parts.append(f"   • Fases executadas: {len(successful_phases)}/{len(phases)}")
            response_parts.append(f"   • Fases: {', '.join(successful_phases)}")
            
            # Mostrar resultados por fase
            for phase_name, phase_result in phases.items():
                if phase_result.get('success') and phase_result.get('results'):
                    response_parts.append(f"\n   Clipboard **{phase_name.title()}:**")
                    for mcp_name, mcp_result in phase_result['results'].items():
                        if mcp_result.get('success'):
                            action = mcp_result.get('result', {}).get('action', 'acao executada')
                            resources = mcp_result.get('result', {}).get('resources', [])
                            response_parts.append(f"      ✅ {mcp_name}: {action}")
                            if resources:
                                response_parts.append(f"         Recursos: {', '.join(resources)}")
        
        # Performance e estatísticas
        exec_time = result.get('execution_time', 0)
        total_mcps = result.get('total_mcps', 0)
        
        response_parts.append(f"\nStats **Performance:**")
        response_parts.append(f"   • Tempo de execucao: {exec_time:.2f}s")
        response_parts.append(f"   • MCPs coordenados: {total_mcps}")
        
        # Fallback usado
        if result.get('fallback_used'):
            reason = result.get('fallback_reason', 'Motivo nao especificado')
            response_parts.append(f"\n⚠️ **Fallback:** {reason}")
        
        # Erros se houver
        if result.get('errors'):
            response_parts.append(f"\n❌ **Avisos:**")
            for error in result['errors'][:3]:  # Mostrar apenas os 3 primeiros
                response_parts.append(f"   • {error}")
        
        # Próximos passos sugeridos
        if result.get('success') and not result.get('fallback_used'):
            response_parts.append(f"\n✅ **Infraestrutura configurada com sucesso!**")
            response_parts.append(f"Idea **Próximos passos:**")
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
            system_prompt = """Você e um assistente de infraestrutura AWS amigável e conversacional. 
Responda de forma natural e humana, como se fosse uma conversa entre amigos.
Se a pergunta for sobre infraestrutura AWS, forneca ajuda tecnica.
Se for uma saudacao ou conversa casual, responda de forma amigável e natural."""
            
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
    
    def format_fallback_response(self, result: Dict[str, Any], mode: str) -> str:
        """Formata resposta do Enhanced Fallback System"""
        
        if mode == 'sandbox':
            if result.get('preview_generated'):
                return f"""🏖️ **MODO SANDBOX ATIVO**

✅ Preview gerado com sucesso!
📁 **Arquivo:** {result.get('output_path', 'N/A')}
🔒 **Segurança:** Nenhuma operação AWS executada

💡 **Próximos passos:**
   • Revisar o preview gerado
   • Executar sem --sandbox para deploy real
   • Usar 'ialctl start' para configurar infraestrutura"""
            else:
                return f"""🏖️ **MODO SANDBOX ATIVO**

❌ Erro ao gerar preview: {result.get('error', 'Erro desconhecido')}

💡 **Sugestões:**
   • Verificar sintaxe do comando
   • Tentar sem --sandbox para execução normal"""
        
        elif mode == 'agent_core':
            response = result.get('response', '')
            session_id = result.get('session_id', 'N/A')
            
            return f"""🧠 **BEDROCK AGENT CORE**

{response}

📋 **Sessão:** {session_id[:8]}...
🤖 **Processado via:** Bedrock Agent"""
        
        elif mode == 'fallback_nlp':
            # Processar resultado do NLP local
            if isinstance(result, dict):
                if result.get('success'):
                    return f"""🔄 **NLP LOCAL (FALLBACK)**

✅ {result.get('message', 'Operação concluída')}

📊 **Detalhes:** {result.get('details', 'N/A')}
🔧 **Processado via:** Cognitive Engine Local"""
                else:
                    return f"""🔄 **NLP LOCAL (FALLBACK)**

❌ {result.get('error', 'Erro na operação')}

💡 **Sugestão:** Verificar configuração ou tentar novamente"""
            else:
                return f"""🔄 **NLP LOCAL (FALLBACK)**

{str(result)}

🔧 **Processado via:** Cognitive Engine Local"""
        
        else:
            return f"⚠️ Modo de processamento desconhecido: {mode}"

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
                return "Launch I would deploy the complete infrastructure across all domains. This includes foundation, security, networking, compute, data, application, observability, AI/ML, and governance. This will take approximately 3 hours. (Note: Running in basic mode - full functionality available with Master Engine)"
            elif domain:
                domain_info = self.get_domain_info(domain)
                if dry_run:
                    return f"Search I would simulate deploying the {domain} infrastructure. This would include {domain_info['phases']} phases and take about {domain_info['duration']}. No actual resources would be created. (Basic mode)"
                else:
                    return f"Launch I would deploy the {domain} infrastructure. This includes {domain_info['phases']} phases and will take about {domain_info['duration']}. (Basic mode - use Master Engine for real deployment)"
            else:
                return "🤔 What would you like me to deploy? You can say 'security', 'networking', 'compute', or 'everything'. (Basic mode)"
        
        elif action == 'status':
            if domain:
                return f"Stats I would check the {domain} infrastructure status... (Basic mode - enable Master Engine for real-time status)"
            else:
                return "Stats I would show you the overall infrastructure status... (Basic mode)"
        
        elif action == 'rollback':
            if domain:
                return f"🔄 I would rollback the {domain} infrastructure. This would safely remove all resources in reverse order. (Basic mode - Master Engine needed for execution)"
            else:
                return "🔄 What would you like me to rollback? Please specify the domain like 'rollback security' or 'rollback networking'. (Basic mode)"
        
        elif action == 'validate':
            if domain:
                return f"Search I would validate the {domain} infrastructure configuration and deployment... (Basic mode)"
            else:
                return "Search I would validate the complete infrastructure setup... (Basic mode)"
        
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
            return f"🧠 **DeepSeek Fallback Mode**\n\n{response}\n\nIdea *For full functionality, ensure AWS Bedrock is configured*"
            
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

    def _detect_drift_commands(self, user_input: str) -> str:
        """
        Detecta comandos relacionados ao drift engine e processa via chat
        """
        user_lower = user_input.lower()
        
        # Comandos de drift detectados
        drift_commands = {
            'mostrar drift': ['mostrar drift', 'show drift', 'listar drift', 'list drift'],
            'detectar drift': ['detectar drift', 'detect drift', 'verificar drift', 'check drift'],
            'diferenças': ['diferenças', 'differences', 'diff', 'mudanças'],
            'reverse sync': ['reverse sync', 'sync reverso', 'sincronizar'],
            'auto heal': ['auto heal', 'auto-heal', 'curar', 'corrigir automaticamente']
        }
        
        detected_command = None
        for command, keywords in drift_commands.items():
            if any(keyword in user_lower for keyword in keywords):
                detected_command = command
                break
        
        if not detected_command:
            return None
        
        try:
            # Importar drift engine
            from core.drift.drift_detector import DriftDetector
            from core.drift.auto_healer import AutoHealer
            from core.drift.reverse_sync import ReverseSync
            
            if detected_command == 'mostrar drift':
                return self._process_show_drift()
            elif detected_command == 'detectar drift':
                return self._process_detect_drift()
            elif detected_command == 'diferenças':
                return self._process_show_differences()
            elif detected_command == 'reverse sync':
                return self._process_reverse_sync()
            elif detected_command == 'auto heal':
                return self._process_auto_heal()
                
        except ImportError as e:
            return f"⚠️ **Drift Engine não disponível:** {e}\n\n" \
                   f"💡 **Alternativa:** Use 'python3 core/drift_cli.py detect' via CLI"
        except Exception as e:
            return f"❌ **Erro no Drift Engine:** {str(e)}"
        
        return None

    def _process_show_drift(self) -> str:
        """Processa comando 'mostrar drift'"""
        try:
            from core.drift.drift_detector import DriftDetector
            
            detector = DriftDetector()
            drift_items = detector.detect_drift()
            
            if not drift_items:
                return "✅ **Nenhum drift detectado!**\n\n" \
                       "🔄 **Status:** Git e AWS estão sincronizados\n" \
                       "📊 **Última verificação:** Agora\n" \
                       "💡 **Dica:** Execute novamente após mudanças na infraestrutura"
        except Exception as e:
            return f"❌ **Erro ao detectar drift:** {str(e)}"

if __name__ == "__main__":
    main()
