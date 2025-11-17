#!/usr/bin/env python3
"""
IAL Master Engine Integrated - Usando arquitetura existente robusta
Integra BedrockConversationEngine + Memory + Query/Provisioning engines
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import platform
import getpass

class IALMasterEngineIntegrated:
    """Master Engine usando componentes robustos existentes"""
    
    def __init__(self):
        # MCP Client
        from core.mcp_client import MCPClient
        self.mcp_client = MCPClient()
        
        # Engines especializados
        self.bedrock_engine = self._initialize_bedrock_engine()
        self.context_engine = self._initialize_context_engine()
        self.query_engine = self._initialize_query_engine()
        self.troubleshooting_engine = self._initialize_troubleshooting_engine()
        self.cost_optimization_engine = self._initialize_cost_optimization_engine()
        
        # Orquestradores existentes
        self.orchestrators = self._initialize_orchestrators()
        
        # Phase Discovery Tool - Integração com MCP GitHub Server
        from phase_discovery_tool import PhaseDiscoveryTool
        self.phase_discovery = PhaseDiscoveryTool(self.mcp_client)
        self.available_phases = []
        self.deployment_order = []
        
        # User ID do ContextEngine (persistente)
        self.user_id = self.context_engine.memory.user_id if self.context_engine else self._generate_user_id()
        self.current_session_id = None
        
        # Capacidades
        self.capabilities = {
            'conversational': True,
            'memory_persistent': True,
            'semantic_search': True,
            'query': True,
            'provisioning': True,
            'observability': True,
            'security': True,
            'troubleshooting': True,
            'cost_optimization': True,
            'phase_discovery': True
        }
    
    def _generate_user_id(self) -> str:
        """Gera ID único baseado em hostname + username"""
        hostname = platform.node()
        username = getpass.getuser()
        unique_string = f"{hostname}-{username}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    def _initialize_bedrock_engine(self):
        """Inicializar Bedrock Conversation Engine existente"""
        try:
            from lib.bedrock_conversation_engine import BedrockConversationEngine
            return BedrockConversationEngine()
        except ImportError as e:
            print(f"⚠️ BedrockConversationEngine não encontrado: {e}")
            return None
    
    def _initialize_context_engine(self):
        """Inicializar Context Engine otimizado"""
        try:
            from core.memory.context_engine_optimized import OptimizedContextEngine
            return OptimizedContextEngine()
        except ImportError as e:
            print(f"⚠️ OptimizedContextEngine não encontrado, usando fallback: {e}")
            try:
                from core.memory.context_engine import ContextEngine
                return ContextEngine()
            except ImportError:
                return None
    
    def _initialize_query_engine(self):
        """Inicializar Query Engine existente"""
        try:
            from core.ial_query_engine import QueryEngineIntegration
            return QueryEngineIntegration()
        except ImportError as e:
            print(f"⚠️ QueryEngine não encontrado: {e}")
            return None
    
    def _initialize_troubleshooting_engine(self):
        """Inicializar Troubleshooting Engine"""
        try:
            from .ial_troubleshooting_engine import TroubleshootingIntegration
            return TroubleshootingIntegration()
        except ImportError as e:
            print(f"⚠️ TroubleshootingEngine não encontrado: {e}")
            return None
    
    def _initialize_cost_optimization_engine(self):
        """Inicializar Cost Optimization Engine"""
        try:
            from .cost_optimization_engine import CostOptimizationIntegration
            return CostOptimizationIntegration()
        except ImportError as e:
            print(f"⚠️ CostOptimizationEngine não encontrado: {e}")
            return None
    
    def _initialize_orchestrators(self):
        """Inicializar orquestradores existentes"""
        orchestrators = {}
        
        # Step Functions Orchestrator
        try:
            from core.ial_orchestrator_stepfunctions import IALOrchestratorStepFunctions
            orchestrators['stepfunctions'] = IALOrchestratorStepFunctions()
        except ImportError:
            orchestrators['stepfunctions'] = None
        
        # MCP First Orchestrator
        try:
            from core.ial_orchestrator_mcp_first import IALOrchestratorMCPFirst
            orchestrators['mcp_first'] = IALOrchestratorMCPFirst()
        except ImportError:
            orchestrators['mcp_first'] = None
        
        # Python Orchestrator
        try:
            from core.ial_orchestrator import IALOrchestrator
            orchestrators['python'] = IALOrchestrator()
        except ImportError:
            orchestrators['python'] = None
        
        return orchestrators
    
    def _normalize_service_name(self, user_input: str) -> str:
        """Normaliza nomes de serviços com fuzzy matching para typos comuns"""
        # Mapa de typos comuns → serviço correto
        typo_map = {
            'dynamon': 'dynamodb',
            'dinamodb': 'dynamodb',
            'dynanodb': 'dynamodb',
            'lambada': 'lambda',
            'labda': 'lambda',
            'lamda': 'lambda',
            's33': 's3',
            'ec22': 'ec2',
        }
        
        # Substituir typos conhecidos (case insensitive)
        normalized = user_input
        for typo, correct in typo_map.items():
            import re
            normalized = re.sub(rf'\b{typo}\b', correct, normalized, flags=re.IGNORECASE)
        
        return normalized
    
    async def trigger_nl_intent_pipeline_sfn(self, nl_intent: str, monthly_budget: float = 500.0) -> Dict[str, Any]:
        """
        Trigger Step Functions NL Intent Pipeline
        
        Args:
            nl_intent: Intenção em linguagem natural
            monthly_budget: Budget mensal em USD
        
        Returns:
            {
                "execution_arn": str,
                "status": str,
                "message": str
            }
        """
        import boto3
        import json
        import uuid
        
        sfn = boto3.client('stepfunctions')
        
        # Get State Machine ARN
        state_machine_arn = f"arn:aws:states:{boto3.Session().region_name}:{boto3.client('sts').get_caller_identity()['Account']}:stateMachine:ial-nl-intent-pipeline"
        
        # Prepare input
        execution_input = {
            "nl_intent": nl_intent,
            "monthly_budget": monthly_budget,
            "correlation_id": str(uuid.uuid4())
        }
        
        # Start execution
        try:
            response = sfn.start_execution(
                stateMachineArn=state_machine_arn,
                input=json.dumps(execution_input)
            )
            
            return {
                "status": "started",
                "execution_arn": response['executionArn'],
                "message": f"✅ Pipeline iniciado! Acompanhe em: https://console.aws.amazon.com/states/home#/executions/details/{response['executionArn']}"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao iniciar pipeline: {str(e)}"
            }
    
    async def process_nl_intent_full_pipeline(self, nl_intent: str) -> Dict[str, Any]:
        """
        Pipeline completo: NL Intent → IAS → Cost → Phase Builder → GitOps
        
        Fluxo:
        1. IAS (Intent Validation Sandbox)
        2. Pre-YAML Cost Guardrails
        3. Phase Builder (YAML + DAG)
        4. GitHub PR
        5. Step Functions Pipeline
        """
        from core.ias_sandbox import IASandbox
        from core.cost_guardrails import CostGuardrails
        from core.intelligent_phase_builder import IntelligentPhaseBuilder
        from core.gitops_phase_manager import GitOpsPhaseManager
        import os
        
        print("🧠 Interpretando intenção...")
        
        # 1. IAS - Intent Validation Sandbox
        print("🔒 Validando segurança (IAS)...")
        ias = IASandbox()
        ias_result = ias.validate_intent(nl_intent)
        
        if not ias_result["safe"]:
            return {
                "status": "blocked",
                "reason": "security_risk",
                "message": ias_result["recommendation"],
                "risks": ias_result["risks"]
            }
        
        print(f"✅ IAS: {ias_result['recommendation']}")
        
        # 2. Pre-YAML Cost Guardrails
        print("💰 Estimando custos...")
        cost_guardrails = CostGuardrails(monthly_budget=500.0)
        cost_result = cost_guardrails.estimate_from_intent(nl_intent)
        
        if not cost_result["within_budget"]:
            return {
                "status": "blocked",
                "reason": "budget_exceeded",
                "message": f"Custo estimado ${cost_result['total_monthly_cost']:.2f}/mês excede budget de ${cost_result['monthly_budget']:.2f}/mês",
                "cost_breakdown": cost_result["estimates"],
                "alternatives": cost_result["alternatives"]
            }
        
        print(f"✅ Custo previsto: ~USD {cost_result['total_monthly_cost']:.2f}/mês (OK)")
        
        # 3. Phase Builder - Gera YAML
        print("📦 Gerando phase YAML...")
        phase_builder = IntelligentPhaseBuilder()
        phase_result = phase_builder.build_phase_from_intent(
            nl_intent,
            ias_result,
            cost_result
        )
        
        # Salvar YAML
        phase_file = f"{phase_result['phase_number']:02d}-{phase_result['phase_name']}.yaml"
        phase_path = os.path.join("/home/ial/phases", phase_file)
        
        with open(phase_path, 'w') as f:
            f.write(phase_result['yaml_content'])
        
        print(f"✅ Phase gerada: {phase_file}")
        
        # 4. Git commit + push
        print("📬 Criando Pull Request...")
        import subprocess
        subprocess.run(['git', 'add', phase_path], cwd="/home/ial", check=True)
        subprocess.run([
            'git', 'commit', '-m',
            f'feat: Add {phase_result["phase_name"]} phase\n\nGenerated from NL intent via IAL\nCost: ${cost_result["total_monthly_cost"]:.2f}/month'
        ], cwd="/home/ial", check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd="/home/ial", check=True)
        
        print("✅ Pull Request será aberto pelo GitHub Actions")
        
        return {
            "status": "success",
            "phase_file": phase_file,
            "phase_path": phase_path,
            "estimated_cost": cost_result["total_monthly_cost"],
            "dependencies": phase_result["dependencies"],
            "ias_validation": ias_result,
            "cost_breakdown": cost_result["estimates"],
            "next_steps": [
                "1. GitHub Actions validará o CloudFormation",
                "2. Pull Request será aberto automaticamente",
                "3. Aprove o PR para iniciar deployment",
                "4. Step Functions executará pipeline completo",
                "5. Recursos serão criados na AWS"
            ]
        }
    
    async def _enrich_prompt_with_rag(self, nl_intent: str) -> str:
        """
        Enriquece prompt com contexto RAG antes de chamar LLM
        
        Args:
            nl_intent: Intenção em linguagem natural
        
        Returns:
            Prompt enriquecido com contexto relevante
        """
        try:
            from services.rag.retriever import retrieve
            
            # Buscar contexto relevante (top 6 snippets)
            rag_results = retrieve(query=nl_intent, k=6, threshold=0.65)
            
            if not rag_results:
                return nl_intent
            
            # Construir contexto
            context_snippets = []
            for i, result in enumerate(rag_results, 1):
                snippet = result.get('text', result.get('content', ''))
                source = result.get('source', 'unknown')
                score = result.get('score', 0)
                
                context_snippets.append(f"[{i}] (score: {score:.2f}, source: {source})\n{snippet}")
            
            # Prompt enriquecido
            enriched_prompt = f"""CONTEXTO RELEVANTE (RAG):
{chr(10).join(context_snippets)}

---

INTENÇÃO DO USUÁRIO:
{nl_intent}

Use o contexto acima para gerar uma resposta precisa e baseada em documentação real."""
            
            return enriched_prompt
        
        except Exception as e:
            print(f"⚠️ RAG não disponível: {e}")
            return nl_intent
    
    async def _detect_and_process_phase_commands(self, user_input: str) -> Optional[str]:
        """Detecta e processa comandos relacionados a fases"""
        
        # Comandos de listagem de fases
        if any(keyword in user_input.lower() for keyword in [
            "list phases", "show phases", "available phases", "fases disponíveis", 
            "listar fases", "mostrar fases", "quais fases"
        ]):
            if not self.available_phases:
                await self.initialize_phase_discovery()
            
            if self.available_phases:
                response = "📋 **Fases Disponíveis:**\n\n"
                for phase in self.available_phases:
                    response += f"• **{phase['phase_id']}** - {phase['phase_name']}\n"
                    response += f"  └─ {phase['template_count']} templates disponíveis\n\n"
                
                response += f"**Total:** {len(self.available_phases)} fases com {sum(p['template_count'] for p in self.available_phases)} templates"
                return response
            else:
                return "⚠️ Não foi possível descobrir as fases disponíveis. Verifique a configuração do MCP GitHub Server."
        
        # Comandos de detalhes de fase específica
        import re
        phase_detail_match = re.search(r'(?:show|describe|details?|info)\s+(?:phase\s+)?(\d{2}-[\w-]+)', user_input.lower())
        if phase_detail_match:
            phase_id = phase_detail_match.group(1)
            
            if not self.available_phases:
                await self.initialize_phase_discovery()
            
            phase_info = next((p for p in self.available_phases if p['phase_id'] == phase_id), None)
            if phase_info:
                response = f"📄 **Fase {phase_info['phase_id']}** - {phase_info['phase_name']}\n\n"
                response += f"**Templates disponíveis ({phase_info['template_count']}):**\n"
                for template in phase_info['templates']:
                    response += f"• {template}\n"
                return response
            else:
                return f"❌ Fase '{phase_id}' não encontrada. Use 'list phases' para ver fases disponíveis."
        
        # Comandos de ordem de deployment
        if any(keyword in user_input.lower() for keyword in [
            "deployment order", "deploy order", "ordem de deploy", "sequência de deploy"
        ]):
            if not self.deployment_order:
                await self.initialize_phase_discovery()
            
            if self.deployment_order:
                response = "🚀 **Ordem Recomendada de Deployment:**\n\n"
                for i, phase_id in enumerate(self.deployment_order, 1):
                    phase_info = next((p for p in self.available_phases if p['phase_id'] == phase_id), None)
                    phase_name = phase_info['phase_name'] if phase_info else phase_id
                    response += f"{i}. **{phase_id}** - {phase_name}\n"
                return response
            else:
                return "⚠️ Não foi possível determinar a ordem de deployment."
        
        return None
    
    async def _detect_and_trigger_creation_intent(self, user_input: str) -> Optional[str]:
        """
        Detecta intenções de criação de infraestrutura e trigger Step Functions
        
        Args:
            user_input: Input do usuário
            
        Returns:
            Response string se intenção detectada, None caso contrário
        """
        # Keywords que indicam intenção de criação
        creation_keywords = [
            'quero', 'criar', 'provisionar', 'deploy', 'preciso', 'gostaria',
            'create', 'provision', 'deploy', 'need', 'want', 'setup'
        ]
        
        # Keywords de infraestrutura AWS
        infra_keywords = [
            'bucket', 's3', 'ec2', 'instance', 'rds', 'database', 'lambda',
            'vpc', 'subnet', 'security group', 'load balancer', 'alb', 'nlb',
            'cloudfront', 'route53', 'iam', 'role', 'policy', 'dynamodb',
            'elasticache', 'redis', 'memcached', 'sqs', 'sns', 'api gateway'
        ]
        
        user_lower = user_input.lower()
        
        # Verificar se há intenção de criação + infraestrutura
        has_creation = any(keyword in user_lower for keyword in creation_keywords)
        has_infra = any(keyword in user_lower for keyword in infra_keywords)
        
        if has_creation and has_infra:
            print(f"🚀 Intenção de criação detectada: {user_input}")
            
            try:
                # Trigger Step Functions pipeline
                result = await self._trigger_nl_intent_pipeline_sfn(
                    nl_intent=user_input,
                    monthly_budget=500.0
                )
                
                if result.get('status') == 'started':
                    execution_arn = result.get('execution_arn', 'unknown')
                    execution_name = execution_arn.split(':')[-1] if execution_arn != 'unknown' else 'unknown'
                    
                    return f"""✅ **Pipeline de Infraestrutura Iniciado!**

🎯 **Solicitação:** {user_input}

🚀 **Pipeline IAL NL Intent:** INICIADO
📋 **Execution:** {execution_name}
💰 **Budget:** $500/mês
🔗 **ARN:** {execution_arn}

**Próximos Passos:**
1. 🔒 Validação de segurança (IAS)
2. 💰 Estimativa de custos
3. 🏗️ Geração CloudFormation (Enhanced MCP)
4. 📝 Commit Git + PR
5. ⏳ Aguardar aprovação
6. 🚀 Deploy automático
7. ✅ Verificação pós-deploy

**Acompanhe em:**
AWS Console → Step Functions → {execution_name}

**Status em tempo real:**
```bash
aws stepfunctions describe-execution --execution-arn {execution_arn}
```

O pipeline está rodando em background. Você receberá notificações sobre o progresso!"""
                
                else:
                    return f"❌ Falha ao iniciar pipeline: {result.get('error', 'Erro desconhecido')}"
                    
            except Exception as e:
                return f"❌ Erro ao processar intenção de criação: {str(e)}"
        
        return None  # Não é intenção de criação
    
    async def _trigger_nl_intent_pipeline_sfn(self, nl_intent: str, monthly_budget: float = 500.0) -> Dict[str, Any]:
        """
        Trigger Step Functions NL Intent Pipeline
        
        Args:
            nl_intent: Intenção em linguagem natural
            monthly_budget: Budget mensal em USD
            
        Returns:
            Dict com status e execution_arn
        """
        try:
            import boto3
            import time
            
            sfn = boto3.client('stepfunctions', region_name='us-east-1')
            
            # Input para Step Functions
            execution_input = {
                "nl_intent": nl_intent,
                "natural_language_request": nl_intent,
                "monthly_budget": monthly_budget,
                "user_context": {
                    "user_id": self.user_id,
                    "session_id": self.current_session_id or f"session-{int(time.time())}",
                    "triggered_via": "ialctl-auto-detection"
                }
            }
            
            # Nome único para execução
            execution_name = f"ialctl-auto-{int(time.time())}"
            
            # Iniciar execução
            response = sfn.start_execution(
                stateMachineArn="arn:aws:states:us-east-1:221082174220:stateMachine:ial-nl-intent-pipeline",
                name=execution_name,
                input=json.dumps(execution_input)
            )
            
            return {
                'status': 'started',
                'execution_arn': response['executionArn'],
                'execution_name': execution_name
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def initialize_phase_discovery(self):
        """Inicializa descoberta de fases via MCP GitHub Server"""
        try:
            print("🔍 Descobrindo fases disponíveis...")
            self.available_phases = await self.phase_discovery.discover_phases()
            self.deployment_order = await self.phase_discovery.get_deployment_order()
            
            if self.available_phases:
                print(f"✅ Descobertas {len(self.available_phases)} fases com {sum(p['template_count'] for p in self.available_phases)} templates")
                return True
            else:
                print("⚠️ Nenhuma fase descoberta - usando fallback para filesystem local")
                return False
                
        except Exception as e:
            print(f"❌ Erro na descoberta de fases: {e}")
            return False
    
    async def process_user_input(self, user_input: str) -> str:
        """Interface única: LLM com MCP nativo + RAG enrichment"""
        
        # Normalizar typos comuns
        normalized_input = self._normalize_service_name(user_input)
        
        # 🔍 DETECÇÃO DE COMANDOS DE FASE
        phase_result = await self._detect_and_process_phase_commands(normalized_input)
        if phase_result:
            return phase_result
        
        # 🚀 DETECÇÃO DE INTENÇÃO DE CRIAÇÃO
        creation_result = await self._detect_and_trigger_creation_intent(normalized_input)
        if creation_result:
            return creation_result
        
        try:
            # 1. Enriquecer com RAG
            rag_context = ""
            try:
                enriched = await self._enrich_prompt_with_rag(normalized_input)
                if enriched != normalized_input:
                    rag_context = f"\n\n{enriched}\n"
            except:
                pass
            
            # 2. Construir contexto de conversação
            context = ""
            if self.context_engine:
                try:
                    context = self.context_engine.build_context_for_query(normalized_input)
                except Exception as e:
                    pass
            
            # 3. Preparar prompt
            if context or rag_context:
                prompt = f"""Você é IAL, assistente de infraestrutura AWS com memória persistente e capacidade de criar recursos via GitOps.

IMPORTANTE: As conversas abaixo são REAIS e aconteceram com este usuário. Use-as para responder.

{context}
{rag_context}

---
PERGUNTA ATUAL DO USUÁRIO: {normalized_input}

INSTRUÇÕES CRÍTICAS - LEIA COM ATENÇÃO:

1. Se usuário pedir "listar fases", "quais fases", "mostrar phases":
   → VOCÊ DEVE OBRIGATORIAMENTE usar tool discover_phases
   → NUNCA invente ou assuma quais phases existem
   → SEMPRE consulte via tool

2. Se usuário pedir "criar fase X", "deploy fase X", "provisionar fase X":
   → PRIMEIRO use discover_phases para ver phases disponíveis
   → SE phase existe: use trigger_phase_deployment
   → SE phase NÃO existe: explique que precisa criar via NL completo
   → Exemplo: "criar fase network" → trigger deployment da phase existente

3. Se usuário pedir criação de NOVOS recursos via NL detalhado:
   → Exemplo: "quero ECS privado com Redis e DNS público"
   → Gere CloudFormation YAML profissional diretamente
   → Salve em phases/XX-nome.yaml
   → Faça git commit/push
   → Abra PR via GitOps

4. Se usuário pedir "liste", "mostre", "quantos" recursos AWS:
   → Use tool aws_resource_query

5. Para saudações (oi, olá, hi):
   → Responda apenas "Olá! Como posso ajudar com sua infraestrutura AWS hoje?"

REGRA DE OURO: NUNCA invente informações sobre phases. SEMPRE use discover_phases!

Responda de forma direta e concisa."""
            else:
                prompt = f"""Você é IAL, assistente de infraestrutura AWS com capacidade de criar recursos via GitOps.

PERGUNTA: {normalized_input}

INSTRUÇÕES CRÍTICAS - LEIA COM ATENÇÃO:

1. Se usuário pedir "listar fases", "quais fases", "mostrar phases":
   → VOCÊ DEVE OBRIGATORIAMENTE usar tool discover_phases
   → NUNCA invente ou assuma quais phases existem
   → SEMPRE consulte via tool

2. Se usuário pedir "criar fase X", "deploy fase X":
   → PRIMEIRO use discover_phases
   → Depois use trigger_phase_deployment

3. Para listar recursos AWS:
   → Use tool aws_resource_query

REGRA DE OURO: NUNCA invente informações sobre phases. SEMPRE use discover_phases!
- Use a tool aws_resource_query APENAS quando o usuário pedir explicitamente para listar/consultar recursos
- Responda de forma direta e concisa."""
            
            # 3. PRIMÁRIO: Bedrock Converse com MCP nativo
            try:
                assistant_response = await self._invoke_bedrock_converse_mcp(prompt, normalized_input)
            except Exception as e:
                print(f"⚠️ Erro no Bedrock: {e}")
                # FALLBACK: Tools hard-coded com CLI
                try:
                    assistant_response = await self._invoke_with_cli_fallback(prompt, normalized_input)
                except Exception as e2:
                    print(f"❌ Erro no fallback: {e2}")
                    assistant_response = f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"
            
            # 4. Salvar interação (usar input original para histórico)
            if self.context_engine and assistant_response:
                try:
                    self.context_engine.save_interaction(
                        user_input,
                        assistant_response,
                        {'model': 'claude-3-sonnet-mcp'}
                    )
                except Exception as e:
                    print(f"⚠️ Erro ao salvar contexto: {e}")
            
            return assistant_response if assistant_response else "Desculpe, não consegui processar sua solicitação."
            
        except Exception as e:
            return f"❌ Erro: {str(e)}"
    
    async def _invoke_bedrock_converse_mcp(self, prompt: str, user_input: str) -> str:
        """PRIMÁRIO: Bedrock Converse API com tool calling"""
        import boto3
        
        bedrock = boto3.client('bedrock-runtime')
        
        # Tools no formato Converse API
        tools = [{
            "toolSpec": {
                "name": "discover_phases",
                "description": "Descobre phases disponíveis via Git. SEMPRE use quando usuário pedir listar fases.",
                "inputSchema": {"json": {"type": "object", "properties": {}}}
            }
        }, {
            "toolSpec": {
                "name": "trigger_phase_deployment",
                "description": "Trigger deployment de phase via GitOps.",
                "inputSchema": {"json": {"type": "object", "properties": {"phase_name": {"type": "string"}}, "required": ["phase_name"]}}
            }
        }, {
            "toolSpec": {
                "name": "aws_resource_query",
                "description": "Consulta recursos AWS",
                "inputSchema": {"json": {"type": "object", "properties": {"service": {"type": "string"}, "query": {"type": "string"}}, "required": ["service", "query"]}}
            }
        }]
        
        # Converse API
        response = bedrock.converse(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            toolConfig={"tools": tools}
        )
        
        if response.get('stopReason') == 'tool_use':
            tool_use = response['output']['message']['content'][0]
            tool_name = tool_use['toolUse']['name']
            tool_input = tool_use['toolUse']['input']
            tool_use_id = tool_use['toolUse']['toolUseId']
            
            # Executar tool
            if tool_name == 'discover_phases':
                tool_result = await self._execute_discover_phases()
            elif tool_name == 'trigger_phase_deployment':
                tool_result = await self._execute_trigger_deployment(tool_input.get('phase_name'))
            elif tool_name == 'aws_resource_query':
                tool_result = await self._execute_mcp_query(tool_input.get('service'), tool_input.get('query'))
            else:
                tool_result = {'error': f'Tool {tool_name} não suportada'}
            
            # Segunda chamada
            import json
            response2 = bedrock.converse(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                messages=[
                    {"role": "user", "content": [{"text": prompt}]},
                    response['output']['message'],
                    {"role": "user", "content": [{"toolResult": {"toolUseId": tool_use_id, "content": [{"json": tool_result}]}}]}
                ],
                toolConfig={"tools": tools}
            )
            return response2['output']['message']['content'][0]['text']
        
        return response['output']['message']['content'][0]['text']

    async def _execute_discover_phases(self) -> dict:
        """Descobre phases disponíveis via Git"""
        from core.gitops_phase_manager import GitOpsPhaseManager
        
        try:
            manager = GitOpsPhaseManager()
            phases = manager.discover_phases()
            
            # Agrupar por domínio para resposta mais concisa
            by_domain = {}
            for p in phases:
                domain = p['domain']
                if domain not in by_domain:
                    by_domain[domain] = []
                by_domain[domain].append(p['name'])
            
            return {
                "status": "success",
                "total_phases": len(phases),
                "domains": len(by_domain),
                "phases_by_domain": by_domain,
                "summary": f"{len(phases)} phases em {len(by_domain)} domínios"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _execute_trigger_deployment(self, phase_name: str) -> dict:
        """Trigger deployment de phase via GitOps"""
        from core.gitops_phase_manager import GitOpsPhaseManager
        
        try:
            manager = GitOpsPhaseManager()
            result = manager.trigger_deployment(phase_name)
            return result
        except Exception as e:
            import traceback
            return {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _execute_cost_query(self, period: str) -> dict:
        """Executar query de custos via AWS Cost Explorer CLI"""
        from datetime import datetime, timedelta
        import subprocess
        import json
        
        # Calcular datas
        today = datetime.now()
        if period == 'last_month':
            end = today.replace(day=1)
            start = (end - timedelta(days=1)).replace(day=1)
        else:  # current_month
            start = today.replace(day=1)
            end = today
        
        start_str = start.strftime('%Y-%m-%d')
        end_str = end.strftime('%Y-%m-%d')
        
        # Comando Cost Explorer
        command = [
            'aws', 'ce', 'get-cost-and-usage',
            '--time-period', f'Start={start_str},End={end_str}',
            '--granularity', 'MONTHLY',
            '--metrics', 'BlendedCost',
            '--group-by', 'Type=DIMENSION,Key=SERVICE',
            '--output', 'json'
        ]
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {'success': True, 'data': data}
            else:
                return {'error': result.stderr}
                
        except Exception as e:
            return {'error': str(e)}
    
    async def _execute_mcp_query(self, service: str, query: str) -> dict:
        """Executar query via AWS CLI"""
        
        # Mapear serviço para comando AWS CLI
        service_map = {
            's3': 'aws s3api list-buckets',
            'ec2': 'aws ec2 describe-instances --query "Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name]" --output json',
            'lambda': 'aws lambda list-functions',
            'kms': 'aws kms list-keys',
            'rds': 'aws rds describe-db-instances',
            'dynamodb': 'aws dynamodb list-tables',
            'stepfunctions': 'aws stepfunctions list-state-machines',
            'ecs': 'aws ecs list-clusters',
            'eks': 'aws eks list-clusters',
            'cloudformation': 'aws cloudformation list-stacks'
        }
        
        command = service_map.get(service.lower())
        if not command:
            return {'error': f'Serviço {service} não suportado'}
        
        try:
            import subprocess
            import json
            
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {'success': True, 'data': data}
            else:
                return {'error': result.stderr}
                
        except Exception as e:
            return {'error': str(e)}
    
    async def _invoke_with_cli_fallback(self, prompt: str, user_input: str) -> str:
        """FALLBACK: Tools hard-coded com AWS CLI"""
        
        try:
            # 1. Construir contexto
            context = ""
            if self.context_engine:
                try:
                    context = self.context_engine.build_context_for_query(user_input)
                except Exception as e:
                    pass
            
            # 2. Preparar prompt
            if context:
                prompt = f"""Você é IAL, assistente de infraestrutura AWS com memória persistente.

IMPORTANTE: As conversas abaixo são REAIS e aconteceram com este usuário. Use-as para responder.

{context}

---
PERGUNTA ATUAL DO USUÁRIO: {user_input}

Responda usando o histórico acima. Se precisar consultar AWS, use as tools disponíveis."""
            else:
                prompt = user_input
            
            # 3. Definir tools disponíveis (MCP servers)
            tools = [
                {
                    "name": "list_s3_buckets",
                    "description": "Lista todos os buckets S3 da conta AWS",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "list_ec2_instances",
                    "description": "Lista todas as instâncias EC2",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "list_step_functions",
                    "description": "Lista todas as state machines do AWS Step Functions",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "list_lambda_functions",
                    "description": "Lista todas as funções Lambda",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "list_dynamodb_tables",
                    "description": "Lista todas as tabelas DynamoDB",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            ]
            
            # 4. Invocar Bedrock com tools
            import boto3
            import json
            bedrock = boto3.client('bedrock-runtime')
            
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "messages": [{"role": "user", "content": prompt}],
                    "tools": tools
                })
            )
            
            result = json.loads(response['body'].read())
            
            # 5. Processar resposta (pode ter tool calls)
            if result.get('stop_reason') == 'tool_use':
                # Claude quer usar uma tool
                tool_use = next((c for c in result['content'] if c.get('type') == 'tool_use'), None)
                if tool_use:
                    tool_name = tool_use['name']
                    
                    # Executar tool
                    tool_result = await self._execute_tool(tool_name, tool_use.get('input', {}))
                    
                    # Segunda chamada com resultado
                    response2 = bedrock.invoke_model(
                        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                        body=json.dumps({
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 2000,
                            "messages": [
                                {"role": "user", "content": prompt},
                                {"role": "assistant", "content": result['content']},
                                {"role": "user", "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use['id'],
                                        "content": json.dumps(tool_result)
                                    }
                                ]}
                            ],
                            "tools": tools
                        })
                    )
                    
                    result = json.loads(response2['body'].read())
            
            assistant_response = next((c['text'] for c in result['content'] if c.get('type') == 'text'), "")
            
            # 6. Salvar interação
            if self.context_engine:
                self.context_engine.save_interaction(
                    user_input,
                    assistant_response,
                    {'model': 'claude-3-sonnet', 'usage': result.get('usage', {})}
                )
            
            return assistant_response
            
        except Exception as e:
            return f"❌ Erro: {str(e)}"
    
    async def _execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        """Executar tool via MCP servers (dados reais AWS)"""
        
        # Usar MCP First Orchestrator
        mcp_orch = self.orchestrators.get('mcp_first')
        if not mcp_orch:
            return {"success": False, "error": "MCP não disponível"}
        
        try:
            # Mapear tool para query
            query_map = {
                "list_s3_buckets": "Liste todos os buckets S3",
                "list_ec2_instances": "Liste todas as instâncias EC2",
                "list_step_functions": "Liste todas as state machines",
                "list_lambda_functions": "Liste todas as funções Lambda",
                "list_dynamodb_tables": "Liste todas as tabelas DynamoDB"
            }
            
            query = query_map.get(tool_name)
            if not query:
                return {"success": False, "error": f"Tool {tool_name} não implementada"}
            
            result = await mcp_orch.execute_with_mcp(query)
            return {"success": True, "data": result}
            
        except Exception as e:
            return {"success": False, "error": f"Erro: {str(e)}"}
    
    async def _classify_intent(self, user_input: str) -> Dict:
        """Classificar intenção do usuário"""
        
        user_lower = user_input.lower()
        
        # Padrões de memória/histórico (prioridade máxima)
        memory_patterns = [
            'última conversa', 'ultimo papo', 'lembra', 'falamos', 
            'discutimos', 'anterior', 'passado', 'histórico'
        ]
        
        # Padrões de query específicos
        query_patterns = [
            'liste', 'quantos', 'quantas', 'mostrar', 'ver', 'status', 
            'describe', 'bucket', 'ec2', 'custo', 'cost'
        ]
        
        # Padrões de provisioning específicos
        provisioning_patterns = [
            'criar', 'quero', 'preciso', 'deploy', 'provisionar', 
            'create', 'setup', 'infrastructure'
        ]
        
        # Padrões de troubleshooting específicos
        troubleshooting_patterns = [
            'problema', 'erro', 'lento', 'falha', 'debug', 'não funciona',
            'slow', 'error', 'issue', 'timeout', 'connection'
        ]
        
        # Padrões de cost optimization específicos
        cost_optimization_patterns = [
            'reduzir custo', 'otimizar', 'economia', 'savings', 'expensive',
            'billing alto', 'cost optimization', 'rightsizing'
        ]
        
        # Verificar memória primeiro (prioridade)
        if any(pattern in user_lower for pattern in memory_patterns):
            return {'type': 'conversational', 'confidence': 0.9}
        
        if any(pattern in user_lower for pattern in query_patterns):
            return {'type': 'query', 'confidence': 0.8}
        elif any(pattern in user_lower for pattern in provisioning_patterns):
            return {'type': 'provisioning', 'confidence': 0.8}
        elif any(pattern in user_lower for pattern in troubleshooting_patterns):
            return {'type': 'troubleshooting', 'confidence': 0.8}
        elif any(pattern in user_lower for pattern in cost_optimization_patterns):
            return {'type': 'cost_optimization', 'confidence': 0.8}
        else:
            return {'type': 'conversational', 'confidence': 0.6}
    
    async def _process_conversational_intent(self, user_input: str) -> str:
        """Processar via Bedrock com contexto do ContextEngine"""
        
        try:
            # Construir contexto semântico do ContextEngine
            context = ""
            if self.context_engine:
                try:
                    context = self.context_engine.build_context_for_query(user_input)
                except Exception as e:
                    pass
            
            # Preparar prompt com contexto
            prompt = user_input
            if context:
                prompt = f"""Contexto das conversas anteriores:
{context}

---
Pergunta atual: {user_input}"""
            
            # Invocar Bedrock
            import boto3
            import json
            bedrock = boto3.client('bedrock-runtime')
            
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            assistant_response = result['content'][0]['text']
            
            # Salvar interação no ContextEngine
            if self.context_engine:
                self.context_engine.save_interaction(
                    user_input,
                    assistant_response,
                    {'model_used': 'claude-3-sonnet', 'usage': result.get('usage', {})}
                )
            
            return assistant_response
            
        except Exception as e:
            return f"❌ Erro no Bedrock: {str(e)}"
    
    async def _process_query_intent(self, user_input: str) -> str:
        """Processar query via Query Engine + Bedrock para formatação"""
        
        if not self.query_engine:
            return "❌ Query Engine não disponível"
        
        try:
            # 1. Executar query (sempre sync)
            query_result = self.query_engine.process_query_sync(user_input)
            
            # 2. Usar Bedrock para formatação inteligente
            if self.bedrock_engine and query_result:
                formatted_prompt = f"""O usuário perguntou: "{user_input}"

Dados obtidos:
{json.dumps(query_result, indent=2)}

Formate estes dados de forma clara e conversacional, usando tabelas quando apropriado e adicionando insights úteis."""
                
                bedrock_result = self.bedrock_engine.process_conversation(
                    user_input=formatted_prompt,
                    user_id=self.user_id,
                    session_id=self.current_session_id
                )
                
                self.current_session_id = bedrock_result['session_id']
                return bedrock_result['response']
            
            # Fallback para formatação simples
            return self._format_query_result_simple(query_result)
            
        except Exception as e:
            return f"❌ Erro na query: {str(e)}"
    
    async def _process_provisioning_intent(self, user_input: str) -> str:
        """Processar provisioning via orquestradores + Bedrock"""
        
        try:
            # 1. Tentar orquestradores em ordem de prioridade
            provisioning_result = None
            
            for orchestrator_name in ['stepfunctions', 'mcp_first', 'python']:
                orchestrator = self.orchestrators.get(orchestrator_name)
                if orchestrator:
                    try:
                        if hasattr(orchestrator, 'process_nl_intent_async'):
                            provisioning_result = await orchestrator.process_nl_intent_async(user_input)
                        elif hasattr(orchestrator, 'process_nl_intent'):
                            provisioning_result = orchestrator.process_nl_intent(user_input)
                        
                        if provisioning_result and provisioning_result.get('status') != 'error':
                            break
                    except Exception as e:
                        print(f"⚠️ {orchestrator_name} falhou: {e}")
                        continue
            
            # 2. Usar Bedrock para formatação da resposta
            if self.bedrock_engine:
                if provisioning_result:
                    formatted_prompt = f"""O usuário solicitou: "{user_input}"

Resultado do provisioning:
{json.dumps(provisioning_result, indent=2)}

Formate esta resposta de forma conversacional, explicando o que foi feito e próximos passos."""
                else:
                    formatted_prompt = f"""O usuário solicitou provisioning: "{user_input}"

Infelizmente, todos os orquestradores falharam. Explique de forma amigável que houve um problema técnico e sugira alternativas ou próximos passos."""
                
                bedrock_result = self.bedrock_engine.process_conversation(
                    user_input=formatted_prompt,
                    user_id=self.user_id,
                    session_id=self.current_session_id
                )
                
                self.current_session_id = bedrock_result['session_id']
                return bedrock_result['response']
            
            # Fallback sem Bedrock
            if provisioning_result:
                return f"✅ **Provisioning iniciado:** {provisioning_result.get('message', 'Sucesso')}"
            else:
                return "❌ **Erro:** Todos os orquestradores de provisioning falharam"
                
        except Exception as e:
            return f"❌ Erro no provisioning: {str(e)}"
    
    async def _process_troubleshooting_intent(self, user_input: str) -> str:
        """Processar troubleshooting via Troubleshooting Engine + Bedrock"""
        
        if not self.troubleshooting_engine:
            return "❌ Troubleshooting Engine não disponível"
        
        try:
            # Executar diagnóstico
            troubleshooting_result = await self.troubleshooting_engine.process_troubleshooting_request(
                user_input, self.user_id
            )
            
            # Usar Bedrock para formatação se disponível
            if self.bedrock_engine and troubleshooting_result:
                formatted_prompt = f"""O usuário relatou: "{user_input}"

Diagnóstico técnico realizado:
{json.dumps(troubleshooting_result, indent=2)}

Formate este diagnóstico de forma conversacional e acionável, explicando o problema e próximos passos de forma clara."""
                
                bedrock_result = self.bedrock_engine.process_conversation(
                    user_input=formatted_prompt,
                    user_id=self.user_id,
                    session_id=self.current_session_id
                )
                
                self.current_session_id = bedrock_result['session_id']
                return bedrock_result['response']
            
            # Fallback sem Bedrock
            return troubleshooting_result.get('diagnosis', 'Diagnóstico realizado')
            
        except Exception as e:
            return f"❌ Erro no troubleshooting: {str(e)}"
    
    async def _process_cost_optimization_intent(self, user_input: str) -> str:
        """Processar cost optimization via Cost Optimization Engine + Bedrock"""
        
        if not self.cost_optimization_engine:
            return "❌ Cost Optimization Engine não disponível"
        
        try:
            # Executar análise de otimização
            optimization_result = await self.cost_optimization_engine.process_cost_optimization_request(
                user_input, self.user_id
            )
            
            # Retornar relatório inteligente (já formatado via Bedrock)
            return optimization_result.get('intelligent_report', 'Análise de otimização concluída')
            
        except Exception as e:
            return f"❌ Erro na otimização de custos: {str(e)}"
    
    def _format_query_result_simple(self, result: Dict) -> str:
        """Formatação simples de query (fallback)"""
        
        result_type = result.get('type', 'unknown')
        
        if result_type == 's3_buckets':
            buckets = result.get('buckets', [])
            if buckets:
                bucket_list = "\n".join([f"• {b.get('name', '')} ({b.get('size', '')}, {b.get('cost', '')})" for b in buckets[:5]])
                return f"📦 **Buckets S3 ({result.get('total', 0)} total):**\n{bucket_list}"
        
        elif result_type == 'ec2_instances':
            total = result.get('total', 0)
            cost = result.get('total_cost', '0')
            return f"🖥️ **Instâncias EC2:** {total} ativas (${cost}/mês)"
        
        elif result_type == 'cost_analysis':
            current = result.get('current_month', '0')
            return f"💰 **Custo atual:** ${current} este mês"
        
        return f"📊 **Resultado:** {result.get('message', 'Query processada')}"
    
    def get_system_status(self) -> Dict:
        """Status do sistema integrado"""
        
        return {
            'user_id': self.user_id,
            'session_id': self.current_session_id,
            'capabilities': self.capabilities,
            'engines_status': {
                'bedrock_conversation': self.bedrock_engine is not None,
                'context_engine': self.context_engine is not None,
                'query_engine': self.query_engine is not None
            },
            'orchestrators_status': {
                name: orch is not None 
                for name, orch in self.orchestrators.items()
            },
            'memory_stats': self._get_memory_stats()
        }
    
    def _get_memory_stats(self) -> Dict:
        """Estatísticas de memória"""
        
        if self.context_engine and hasattr(self.context_engine, 'memory'):
            try:
                return self.context_engine.memory.get_user_stats()
            except:
                pass
        
        return {'status': 'Memory stats not available'}
    
    def clear_session(self):
        """Limpar sessão atual"""
        
        if self.context_engine:
            self.context_engine.clear_session_context()
        
        self.current_session_id = None
        print("🧹 Sessão limpa")

# Interface CLI integrada
class IALCLIIntegrated:
    """CLI usando Master Engine integrado"""
    
    def __init__(self):
        self.engine = IALMasterEngineIntegrated()
    
    async def run_interactive_mode(self):
        """Modo interativo com engines robustos"""
        
        print("🤖 **IAL Assistant - Arquitetura Integrada**")
        print("Usando: Bedrock + DynamoDB + Context Engine + MCP Servers")
        
        # Status inicial
        status = self.engine.get_system_status()
        active_engines = sum(1 for engine in status["engines_status"].values() if engine)
        active_orchestrators = sum(1 for orch in status["orchestrators_status"].values() if orch)
        
        print(f"📊 **Sistema:** {active_engines}/3 engines, {active_orchestrators}/3 orquestradores")
        print(f"👤 **User ID:** {status['user_id']}")
        print("Digite 'help', 'status' ou 'clear' para comandos especiais\n")
        
        while True:
            try:
                user_input = input("IAL> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'sair']:
                    print("👋 Até logo!")
                    break
                
                if user_input.lower() == 'status':
                    self._show_detailed_status()
                    continue
                
                if user_input.lower() == 'clear':
                    self.engine.clear_session()
                    continue
                
                if user_input.lower() in ['help', 'ajuda']:
                    self._show_help()
                    continue
                
                if user_input:
                    response = await self.engine.process_user_input(user_input)
                    print(f"\n{response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def _show_detailed_status(self):
        """Mostrar status detalhado"""
        
        status = self.engine.get_system_status()
        
        print("\n📊 **Status do Sistema Integrado:**")
        print(f"👤 **User ID:** {status['user_id']}")
        print(f"🔗 **Session ID:** {status.get('session_id', 'Nova sessão')}")
        
        print("\n🧠 **Engines Robustos:**")
        engines = status["engines_status"]
        print(f"• Bedrock Conversation: {'✅' if engines['bedrock_conversation'] else '❌'}")
        print(f"• Context Engine: {'✅' if engines['context_engine'] else '❌'}")
        print(f"• Query Engine: {'✅' if engines['query_engine'] else '❌'}")
        
        print("\n🔄 **Orquestradores:**")
        orchestrators = status["orchestrators_status"]
        for name, active in orchestrators.items():
            print(f"• {name}: {'✅' if active else '❌'}")
        
        print("\n💾 **Memória:**")
        memory_stats = status.get('memory_stats', {})
        if 'total_messages' in memory_stats:
            print(f"• Total mensagens: {memory_stats['total_messages']}")
            print(f"• Sessões: {memory_stats['sessions']}")
        else:
            print(f"• Status: {memory_stats.get('status', 'N/A')}")
    
    def _show_help(self):
        """Mostrar ajuda"""
        
        print("""
🤖 **IAL Assistant - Guia Integrado**

**💬 CONVERSAÇÃO NATURAL:**
• "Olá, preciso de ajuda"
• "Como está meu ambiente AWS?"
• "Explique o que é ECS"

**📊 CONSULTAS:**
• "liste todos os buckets"
• "quantas EC2 eu tenho"
• "qual o custo atual"

**🚀 PROVISIONING:**
• "quero ECS com Redis"
• "criar VPC privada"
• "deploy aplicação serverless"

**⚙️ COMANDOS:**
• "status" - Status do sistema
• "clear" - Limpar sessão
• "help" - Esta ajuda
• "quit" - Sair

💡 **Diferencial:** Memória persistente + Bedrock + Contexto inteligente
""")

# Função principal
async def main():
    """Função principal integrada"""
    cli = IALCLIIntegrated()
    await cli.run_interactive_mode()

if __name__ == "__main__":
    asyncio.run(main())
