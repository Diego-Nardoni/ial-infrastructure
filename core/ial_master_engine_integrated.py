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
            'cost_optimization': True
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
        """Inicializar Context Engine existente"""
        try:
            from core.memory.context_engine import ContextEngine
            return ContextEngine()
        except ImportError as e:
            print(f"⚠️ ContextEngine não encontrado: {e}")
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
    
    async def process_user_input(self, user_input: str) -> str:
        """Interface única: LLM com MCP nativo"""
        
        # Normalizar typos comuns
        normalized_input = self._normalize_service_name(user_input)
        
        try:
            # 1. Construir contexto
            context = ""
            if self.context_engine:
                try:
                    context = self.context_engine.build_context_for_query(normalized_input)
                except Exception as e:
                    pass
            
            # 2. Preparar prompt
            if context:
                prompt = f"""Você é IAL, assistente de infraestrutura AWS com memória persistente e capacidade de criar recursos via GitOps.

IMPORTANTE: As conversas abaixo são REAIS e aconteceram com este usuário. Use-as para responder.

{context}

---
PERGUNTA ATUAL DO USUÁRIO: {normalized_input}

INSTRUÇÕES CRÍTICAS - LEIA COM ATENÇÃO:

1. Se usuário pedir "crie", "criar", "provisione", "deploy" + qualquer recurso AWS:
   → VOCÊ DEVE usar a tool create_infrastructure_phase
   → Exemplos: "crie network", "crie vpc", "crie bucket", "crie eks"
   → NÃO explique como fazer manualmente
   → USE A TOOL para gerar o YAML automaticamente

2. Se usuário pedir "liste", "mostre", "quantos":
   → Use tool aws_resource_query

3. Para saudações (oi, olá, hi):
   → Responda apenas "Olá! Como posso ajudar com sua infraestrutura AWS hoje?"

4. Para perguntas gerais sobre AWS:
   → Responda normalmente sem usar tools

VOCÊ TEM PODER DE CRIAR RECURSOS! Use a tool create_infrastructure_phase quando solicitado.

Responda de forma direta e concisa."""
            else:
                prompt = f"""Você é IAL, assistente de infraestrutura AWS com capacidade de criar recursos via GitOps.

PERGUNTA: {normalized_input}

INSTRUÇÕES CRÍTICAS - LEIA COM ATENÇÃO:

1. Se usuário pedir "crie", "criar", "provisione", "deploy" + qualquer recurso AWS:
   → VOCÊ DEVE usar a tool create_infrastructure_phase
   → Exemplos: "crie network", "crie vpc", "crie bucket", "crie eks"
   → NÃO explique como fazer manualmente
   → USE A TOOL para gerar o YAML automaticamente

2. Se usuário pedir "liste", "mostre", "quantos":
   → Use tool aws_resource_query

3. Para saudações (oi, olá, hi):
   → Responda apenas "Olá! Como posso ajudar com sua infraestrutura AWS hoje?"

VOCÊ TEM PODER DE CRIAR RECURSOS! Use a tool create_infrastructure_phase quando solicitado.
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
        """PRIMÁRIO: Bedrock com MCP tool calling"""
        import boto3
        import json
        
        bedrock = boto3.client('bedrock-runtime')
        
        # Definir tools AWS
        tools = [{
            "name": "aws_resource_query",
            "description": "Consulta recursos AWS de qualquer serviço (S3, EC2, Lambda, KMS, RDS, DynamoDB, etc)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Serviço AWS (s3, ec2, lambda, kms, rds, dynamodb, stepfunctions, ecs, eks, cloudformation)"
                    },
                    "query": {
                        "type": "string",
                        "description": "O que listar/consultar"
                    }
                },
                "required": ["service", "query"]
            }
        }, {
            "name": "aws_cost_query",
            "description": "Consulta custos AWS via Cost Explorer. Use para obter custos mensais por serviço.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Período: 'last_month' ou 'current_month'"
                    }
                },
                "required": ["period"]
            }
        }, {
            "name": "create_infrastructure_phase",
            "description": "Cria uma phase YAML para provisionar infraestrutura AWS via GitOps. Use quando usuário pedir 'crie', 'criar', 'provisione', 'deploy'.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "phase_number": {
                        "type": "integer",
                        "description": "Número da phase (ex: 20 para network, 30 para compute)"
                    },
                    "resource_type": {
                        "type": "string",
                        "description": "Tipo do recurso: VPC, S3, EKS, RDS, Lambda, EC2, ECS"
                    },
                    "resource_name": {
                        "type": "string",
                        "description": "Nome do recurso (ex: ial-production-vpc)"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Propriedades específicas do recurso (CIDR, tamanho, etc)"
                    }
                },
                "required": ["phase_number", "resource_type", "resource_name"]
            }
        }]
        
        # Primeira chamada
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
        
        # Verificar se Claude quer usar tool
        if result.get('stop_reason') == 'tool_use':
            tool_use = next((c for c in result['content'] if c.get('type') == 'tool_use'), None)
            
            if tool_use:
                tool_name = tool_use['name']
                tool_input = tool_use['input']
                
                # Executar tool apropriada
                if tool_name == 'aws_resource_query':
                    mcp_result = await self._execute_mcp_query(
                        tool_input.get('service'),
                        tool_input.get('query')
                    )
                elif tool_name == 'aws_cost_query':
                    mcp_result = await self._execute_cost_query(
                        tool_input.get('period', 'current_month')
                    )
                elif tool_name == 'create_infrastructure_phase':
                    mcp_result = await self._execute_phase_creation(
                        tool_input.get('phase_number'),
                        tool_input.get('resource_type'),
                        tool_input.get('resource_name'),
                        tool_input.get('properties', {})
                    )
                else:
                    mcp_result = {'error': f'Tool {tool_name} não suportada'}
                
                # Segunda chamada com resultado
                response2 = bedrock.invoke_model(
                    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 2000,
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": result['content']},
                            {"role": "user", "content": [{
                                "type": "tool_result",
                                "tool_use_id": tool_use['id'],
                                "content": json.dumps(mcp_result)
                            }]}
                        ],
                        "tools": tools
                    })
                )
                
                result2 = json.loads(response2['body'].read())
                return next((c['text'] for c in result2['content'] if c.get('type') == 'text'), "")
        
        # Resposta direta
        return next((c['text'] for c in result['content'] if c.get('type') == 'text'), "")
    
    async def _execute_phase_creation(self, phase_number: int, resource_type: str, resource_name: str, properties: dict) -> dict:
        """Cria phase YAML para infraestrutura"""
        from core.phase_creator_tool import create_infrastructure_phase
        
        try:
            result = create_infrastructure_phase(
                phase_number=phase_number,
                resource_type=resource_type,
                resource_name=resource_name,
                properties=properties
            )
            return {
                "status": "success",
                "message": f"Phase {result['filename']} criada com sucesso!",
                "filepath": result['filepath'],
                "next_steps": [
                    "1. Revise o YAML gerado",
                    "2. Faça commit: git add phases/ && git commit -m 'Add network phase'",
                    "3. Push: git push origin main",
                    "4. GitHub Actions criará Pull Request automaticamente",
                    "5. Aprove o PR para provisionar na AWS"
                ]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
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
