#!/usr/bin/env python3
"""
Master Engine Final - Integração CORE + USER Paths
Entrada única que decide entre Bootstrap CORE ou Pipeline USER
"""

import sys
import os
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

class MasterEngineFinal:
    def __init__(self):
        """Inicializar Resource Router e engines"""
        
        try:
            from core.resource_router import ResourceRouter
            self.resource_router = ResourceRouter()
        except ImportError as e:
            self.resource_router = None
        
        try:
            from core.cognitive_engine import CognitiveEngine
            self.cognitive_engine = CognitiveEngine()
        except ImportError as e:
            self.cognitive_engine = None
        
        try:
            from core.intelligent_mcp_router import IntelligentMCPRouter
            self.intelligent_router = IntelligentMCPRouter()
        except ImportError as e:
            self.intelligent_router = None
        
        try:
            from core.mcp_infrastructure_manager import MCPInfrastructureManager
            self.mcp_infrastructure_manager = MCPInfrastructureManager(self.intelligent_router)
        except ImportError as e:
            self.mcp_infrastructure_manager = None
    
    def process_request(self, nl_intent: str, config: Dict = None) -> Dict[str, Any]:
        """
        QUADRUPLE LOGIC: Conversational vs CORE resources vs RESOURCE QUERY vs USER resources
        """
        
        
        # LÓGICA 0: CONVERSATIONAL (saudações, perguntas gerais) - BEDROCK
        if self._is_conversational_request(nl_intent):
            return self.process_conversational_path(nl_intent)
        
        # LÓGICA 1: CORE RESOURCES (ialctl start) - EXECUÇÃO DIRETA
        if self._is_core_foundation_request(nl_intent):
            print("🏗️ CORE FOUNDATION REQUEST - Execução direta via MCP Infrastructure Manager")
            return self.process_core_foundation_path(nl_intent, config or {})
        
        # NOVA LÓGICA 2: RESOURCE QUERY (consulta recursos existentes) - BOTO3 DIRETO
        if self._is_resource_query_request(nl_intent):
            print("🔍 RESOURCE QUERY REQUEST - Consulta via boto3")
            return self.process_resource_query_path(nl_intent)
        
        # LÓGICA 3: USER RESOURCES (linguagem natural) - ROTEAMENTO HÍBRIDO
        print("👤 USER RESOURCE REQUEST - Roteamento híbrido")
        
        # Detectar se precisa de governança complexa
        needs_governance = self._needs_complex_governance(nl_intent)
        
        if needs_governance:
            print("🧠 Roteando para Cognitive Engine (governança complexa)")
            return self.process_cognitive_engine_path(nl_intent)
        else:
            print("⚡ Roteando para Intelligent MCP Router (execução direta)")
            return self.process_mcp_router_path(nl_intent)
    
    def _is_conversational_request(self, nl_intent: str) -> bool:
        """Detecta se é uma solicitação conversacional (não infraestrutura)"""
        
        # Saudações e conversação geral
        conversational_patterns = [
            'oi', 'olá', 'hello', 'hi', 'hey', 'iai', 'eai',
            'tudo bem', 'td bem', 'como vai', 'how are you', 'beleza',
            'bom dia', 'boa tarde', 'boa noite',
            'obrigado', 'thanks', 'thank you',
            'tchau', 'bye', 'goodbye',
            'ajuda', 'help', 'socorro',
            'o que você faz', 'what do you do',
            'quem é você', 'who are you',
            'como funciona', 'how does it work',
            'mano', 'cara', 'brother', 'parceiro'
        ]
        
        # Keywords de infraestrutura (se tem essas, NÃO é conversacional)
        infrastructure_keywords = [
            'deploy', 'create', 'setup', 'build', 'provision',
            'delete', 'remove', 'destroy', 'cleanup',
            'ecs', 'lambda', 'rds', 'elb', 'vpc', 's3', 'dynamodb',
            'infrastructure', 'architecture', 'serverless', 'container',
            'phase', 'stack', 'cluster', 'database', 'bucket'
        ]
        
        nl_lower = nl_intent.lower()
        
        # Se tem keywords de infraestrutura, NÃO é conversacional
        has_infrastructure = any(keyword in nl_lower for keyword in infrastructure_keywords)
        if has_infrastructure:
            return False
            
        # Se tem padrões conversacionais, É conversacional
        has_conversational = any(pattern in nl_lower for pattern in conversational_patterns)
        
        # Se é muito curto e não tem infraestrutura, provavelmente é conversacional
        is_short_and_simple = len(nl_intent.split()) <= 5 and not has_infrastructure
        
        return has_conversational or is_short_and_simple
    
    def process_conversational_path(self, nl_intent: str) -> Dict[str, Any]:
        """
        CONVERSATIONAL PATH: Resposta DIRETA via Bedrock
        """
        
        
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
            
            # Add temporal context if needed
            enhanced_input = self._add_temporal_context(nl_intent)
            
            # Prepare request body for Claude
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": enhanced_input
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
                bedrock_response = response_body['content'][0]['text']
                
                return {
                    'status': 'success',
                    'path': 'CONVERSATIONAL_PATH',
                    'execution_method': 'bedrock_direct',
                    'message': bedrock_response,
                    'response': bedrock_response
                }
            
        except Exception as e:
            print(f"⚠️ Bedrock error: {e}")
            
            # Fallback to simple response
            return {
                'status': 'success',
                'path': 'CONVERSATIONAL_PATH',
                'execution_method': 'simple_fallback',
                'message': self._get_simple_response(nl_intent),
                'response': self._get_simple_response(nl_intent)
            }
        
        return {
            'status': 'error',
            'path': 'CONVERSATIONAL_PATH',
            'message': 'Erro na conversação'
        }
    
    def _add_temporal_context(self, user_input: str) -> str:
        """Adiciona contexto temporal se necessário"""
        
        temporal_keywords = [
            'que dia', 'what day', 'que data', 'what date',
            'hoje', 'today', 'agora', 'now',
            'que horas', 'what time', 'hora atual', 'current time'
        ]
        
        user_lower = user_input.lower()
        needs_temporal = any(keyword in user_lower for keyword in temporal_keywords)
        
        if needs_temporal:
            from datetime import datetime
            
            now = datetime.now()
            
            weekdays_pt = {
                'Monday': 'segunda-feira', 'Tuesday': 'terça-feira', 
                'Wednesday': 'quarta-feira', 'Thursday': 'quinta-feira',
                'Friday': 'sexta-feira', 'Saturday': 'sábado', 'Sunday': 'domingo'
            }
            
            months_pt = {
                'January': 'janeiro', 'February': 'fevereiro', 'March': 'março',
                'April': 'abril', 'May': 'maio', 'June': 'junho',
                'July': 'julho', 'August': 'agosto', 'September': 'setembro',
                'October': 'outubro', 'November': 'novembro', 'December': 'dezembro'
            }
            
            weekday_pt = weekdays_pt.get(now.strftime('%A'), now.strftime('%A'))
            month_pt = months_pt.get(now.strftime('%B'), now.strftime('%B'))
            
            context = f"""CONTEXTO TEMPORAL:
Data atual: {now.strftime('%d')} de {month_pt} de {now.strftime('%Y')}
Dia da semana: {weekday_pt}
Horário: {now.strftime('%H:%M')} UTC

Pergunta do usuário: {user_input}"""
            
            return context
        
        return user_input
    
    def _get_simple_response(self, user_input: str) -> str:
        """Resposta simples quando Bedrock falha"""
        
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['oi', 'olá', 'hello', 'hi']):
            return "Olá! Tudo bem! Sou o assistente IAL. Como posso ajudá-lo hoje?"
        elif any(word in user_lower for word in ['tudo bem', 'como vai']):
            return "Tudo bem sim, obrigado! Como posso ajudá-lo com sua infraestrutura AWS?"
        elif any(word in user_lower for word in ['que dia', 'hoje']):
            from datetime import datetime
            now = datetime.now()
            return f"Hoje é {now.strftime('%d/%m/%Y')}, {now.strftime('%A')}."
        elif any(word in user_lower for word in ['obrigado', 'thanks']):
            return "De nada! Fico feliz em ajudar. Precisa de mais alguma coisa?"
        else:
            return "Olá! Sou o assistente IAL para infraestrutura AWS. Como posso ajudá-lo?"
    
    def process_conversation(self, user_input: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Entry point para conversação - roteamento DIRETO
        """
        
        # Usar process_request para roteamento inteligente
        result = self.process_request(user_input)
        
        # ADICIONADO: Formatação para resource queries
        if result.get('path') == 'RESOURCE_QUERY_PATH':
            return {
                'response': self._format_resource_query_response(result),
                'resource_query': True,
                'path': 'RESOURCE_QUERY_PATH'
            }
        
        # Se é conversacional, já tem a resposta direta
        if result.get('path') == 'CONVERSATIONAL_PATH':
            return {
                'response': result.get('response', result.get('message', 'Erro na conversação')),
                'conversational': True,
                'path': 'CONVERSATIONAL_PATH'
            }
        
        # Se é infraestrutura, processar normalmente
        return {
            'response': f"🤖 IaL: {result.get('message', 'Processado via ' + result.get('path', 'unknown'))}",
            'infrastructure_action': True,
            'action_type': result.get('path', 'unknown'),
            'details': result
        }
    
    def _is_core_foundation_request(self, nl_intent: str) -> bool:
        """Detecta se é solicitação de deploy da foundation CORE"""
        
        core_keywords = [
            'deploy complete ial foundation',
            'ial foundation infrastructure',
            'bootstrap ial',
            'start ial infrastructure',
            'deploy foundation',
            'foundation deployment'
        ]
        
        nl_lower = nl_intent.lower()
        return any(keyword in nl_lower for keyword in core_keywords)
    
    def process_core_foundation_path(self, nl_intent: str, config: Dict) -> Dict[str, Any]:
        """
        CORE FOUNDATION PATH: Deploy direto dos 42 componentes via MCP Infrastructure Manager
        """
        
        # NOVO: Verificar e instalar dependências críticas
        print("🔍 Verificando dependências do sistema...")
        self._check_and_install_dependencies()
        
        if not self.mcp_infrastructure_manager:
            return {
                'error': 'MCP Infrastructure Manager não disponível',
                'status': 'error',
                'path': 'CORE_FOUNDATION_PATH'
            }
        
        try:
            # Deploy direto via MCP Infrastructure Manager (42 componentes)
            import asyncio
            result = asyncio.run(
                self.mcp_infrastructure_manager.deploy_ial_infrastructure(config)
            )
            
            return {
                'status': 'success',
                'path': 'CORE_FOUNDATION_PATH',
                'execution_method': 'direct_mcp_infrastructure',
                'components_created': result.get('components_created', 42),
                'message': 'IAL Foundation deployed directly via MCP Infrastructure Manager',
                'details': result
            }
            
        except Exception as e:
            return {
                'error': f'MCP Infrastructure Manager error: {str(e)}',
                'status': 'error',
                'path': 'CORE_FOUNDATION_PATH'
            }
    
    def _needs_complex_governance(self, nl_intent: str) -> bool:
        """Determina se precisa de governança complexa via Cognitive Engine"""
        
        # Palavras-chave que indicam necessidade de governança
        governance_keywords = [
            'production', 'prod', 'critical', 'database', 'security',
            'compliance', 'audit', 'policy', 'budget', 'cost',
            'multi-tier', 'architecture', 'infrastructure'
        ]
        
        # Operações que sempre precisam de governança
        high_risk_operations = [
            'delete', 'destroy', 'remove', 'drop',
            'modify', 'change', 'update', 'alter'
        ]
        
        nl_lower = nl_intent.lower()
        
        # Se tem palavras de governança OU operações de alto risco
        has_governance_keywords = any(keyword in nl_lower for keyword in governance_keywords)
        has_high_risk_ops = any(op in nl_lower for op in high_risk_operations)
        
        return has_governance_keywords or has_high_risk_ops
    
    def process_mcp_router_path(self, nl_intent: str) -> Dict[str, Any]:
        """
        MCP ROUTER PATH: Execução direta via MCP servers
        """
        
        
        if not self.intelligent_router:
            return {
                'error': 'Intelligent MCP Router não disponível',
                'status': 'error',
                'path': 'MCP_ROUTER_PATH'
            }
        
        try:
            # Executar via Intelligent MCP Router
            import asyncio
            result = asyncio.run(
                self.intelligent_router.route_request(nl_intent)
            )
            
            return {
                'status': 'success',
                'path': 'MCP_ROUTER_PATH',
                'execution_method': 'direct_mcp',
                'mcps_used': result.get('mcps_executed', []),
                'message': 'Request executed directly via MCP servers',
                'result': result
            }
            
        except Exception as e:
            return {
                'error': f'MCP Router error: {str(e)}',
                'status': 'error',
                'path': 'MCP_ROUTER_PATH'
            }
    
    def process_cognitive_engine_path(self, nl_intent: str) -> Dict[str, Any]:
        """
        COGNITIVE ENGINE PATH: Todos os recursos via GitOps pipeline completo
        """
        
        
        if not self.cognitive_engine:
            return {
                'error': 'Cognitive Engine não disponível',
                'status': 'error',
                'path': 'COGNITIVE_ENGINE_PATH'
            }
        
        try:
            # PIPELINE COMPLETO: IAS → Cost → Phase Builder → GitHub → CI/CD → Audit
            result = self.cognitive_engine.process_intent(nl_intent)
            
            return {
                'status': 'success',
                'path': 'COGNITIVE_ENGINE_PATH',
                'pipeline_steps': result.get('pipeline_steps', []),
                'github_pr': result.get('github_pr_url'),
                'message': 'Request processed via complete GitOps pipeline',
                'result': result
            }
            
        except Exception as e:
            return {
                'error': f'Cognitive Engine error: {str(e)}',
                'status': 'error',
                'path': 'COGNITIVE_ENGINE_PATH'
            }
    
    def _is_deletion_request(self, nl_intent: str) -> bool:
        """Check if request is for deletion"""
        deletion_keywords = ['delete', 'remove', 'destroy', 'cleanup', 'exclude', 'drop']
        return any(keyword in nl_intent.lower() for keyword in deletion_keywords)
    
    def process_deletion_request(self, nl_intent: str) -> Dict[str, Any]:
        """Process deletion requests - phases or individual resources"""
        print("🗑️ Processando solicitação de exclusão")
        
        # Try phase deletion first
        phase_name = self._extract_phase_name(nl_intent)
        if phase_name:
            return self._process_phase_deletion(phase_name)
        
        # Try individual resource deletion
        resource_info = self._extract_resource_info(nl_intent)
        if resource_info:
            return self._process_resource_deletion(resource_info[1], resource_info[0])
        
        return {
            'error': 'Could not identify what to delete',
            'status': 'error',
            'suggestion': 'Specify "delete phase <name>" or "delete bucket <name>"'
        }
    
    def _process_phase_deletion(self, phase_name: str) -> Dict[str, Any]:
        """Process phase deletion"""
        try:
            from phase_deletion_manager import PhaseDeletionManager
            deletion_manager = PhaseDeletionManager()
            
            # Get phase info
            phase_info = deletion_manager.get_phase_info(phase_name)
            if not phase_info['resources']:
                return {
                    'error': f'Phase {phase_name} not found',
                    'status': 'error'
                }
            
            # Check if safe to delete
            if not phase_info['safe_to_delete']:
                return {
                    'error': f'Phase {phase_name} has dependencies',
                    'status': 'blocked',
                    'dependencies': phase_info['blocking_dependencies'],
                    'suggestion': 'Delete dependent phases first or use force option'
                }
            
            # Execute deletion
            result = deletion_manager.delete_phase(phase_name, force=False)
            
            if result['success']:
                return {
                    'status': 'success',
                    'action': 'phase_deletion',
                    'phase': phase_name,
                    'deleted_resources': result['deleted_resources'],
                    'message': f'Phase {phase_name} deleted successfully'
                }
            else:
                return {
                    'error': result['error'],
                    'status': 'error',
                    'phase': phase_name
                }
                
        except ImportError:
            return {
                'error': 'Phase deletion not available',
                'status': 'error',
                'suggestion': 'Phase deletion manager not installed'
            }
        except Exception as e:
            return {
                'error': f'Phase deletion failed: {str(e)}',
                'status': 'error'
            }
    
    def _process_resource_deletion(self, resource_id: str, resource_type: str) -> Dict[str, Any]:
        """Process individual resource deletion"""
        try:
            from resource_deletion_manager import ResourceDeletionManager
            deletion_manager = ResourceDeletionManager()
            
            print(f"🗑️ Deletando recurso individual: {resource_id} ({resource_type})")
            
            # Execute deletion with complete cleanup
            result = deletion_manager.delete_resource(resource_id, force=False)
            
            if result['success']:
                return {
                    'status': 'success',
                    'action': 'resource_deletion',
                    'resource': resource_id,
                    'type': result['type'],
                    'cleanup_performed': result['cleanup_performed'],
                    'dependencies_removed': result['dependencies_removed'],
                    'message': f'{resource_type.upper()} {resource_id} deleted with complete cleanup'
                }
            else:
                return {
                    'error': result['error'],
                    'status': 'error',
                    'resource': resource_id,
                    'suggestion': result.get('suggestion', 'Check resource exists and permissions')
                }
                
        except ImportError:
            return {
                'error': 'Resource deletion not available',
                'status': 'error',
                'suggestion': 'Resource deletion manager not installed'
            }
        except Exception as e:
            return {
                'error': f'Resource deletion failed: {str(e)}',
                'status': 'error'
            }
    
    def _extract_phase_name(self, nl_intent: str) -> Optional[str]:
        """Extract phase name from natural language"""
        import re
        
        # Common patterns for phases
        phase_patterns = [
            r'delete\s+phase\s+(\w+)',
            r'remove\s+phase\s+(\w+)',
            r'destroy\s+phase\s+(\w+)',
            r'phase\s+(\w+)\s+delete',
            r'(\w+)\s+phase.*delete'
        ]
        
        for pattern in phase_patterns:
            match = re.search(pattern, nl_intent.lower())
            if match:
                return match.group(1)
        
        return None
    
    def _extract_resource_info(self, nl_intent: str) -> Optional[Tuple[str, str]]:
        """Extract resource type and name from natural language"""
        import re
        
        # Resource patterns: (type, identifier_pattern)
        resource_patterns = [
            (r'bucket\s+([a-z0-9\-]+)', 's3'),
            (r'lambda\s+([a-zA-Z0-9\-_]+)', 'lambda'),
            (r'function\s+([a-zA-Z0-9\-_]+)', 'lambda'),
            (r'table\s+([a-zA-Z0-9\-_.]+)', 'dynamodb'),
            (r'database\s+([a-zA-Z0-9\-]+)', 'rds'),
            (r'instance\s+([a-zA-Z0-9\-]+)', 'ec2')
        ]
        
        for pattern, resource_type in resource_patterns:
            match = re.search(pattern, nl_intent.lower())
            if match:
                return (resource_type, match.group(1))
        
        return None
    
    def process_core_path(self, nl_intent: str, config: Dict) -> Dict[str, Any]:
        """
        CORE PATH: Bootstrap CORE resources via MCP Infrastructure Manager
        """
        
        
        if not self.mcp_infrastructure_manager:
            return {
                'error': 'MCP Infrastructure Manager não disponível',
                'status': 'error',
                'path': 'CORE_PATH'
            }
        
        try:
            # Deploy via MCP Infrastructure Manager (42 componentes)
            import asyncio
            result = asyncio.run(
                self.mcp_infrastructure_manager.deploy_ial_infrastructure(config)
            )
            
            return {
                'status': 'success',
                'path': 'CORE_PATH',
                'method': 'mcp_infrastructure_manager',
                'components_created': result.get('deployment_summary', {}).get('foundation_components', 0),
                'details': result,
                'processing_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ CORE PATH error: {str(e)}")
            return {
                'status': 'error',
                'path': 'CORE_PATH',
                'error': str(e),
                'method': 'mcp_infrastructure_manager'
            }
    
    def process_user_path(self, nl_intent: str) -> Dict[str, Any]:
        """
        USER PATH: Arquitetura de referência completa via Cognitive Engine
        """
        
        
        if not self.cognitive_engine:
            return {
                'error': 'Cognitive Engine não disponível',
                'status': 'error',
                'path': 'USER_PATH'
            }
        
        try:
            # Pipeline completo: NL → IAS → Cost → Phase Builder → GitHub PR → CI/CD → Audit → Auto-Heal
            result = self.cognitive_engine.process_user_request(nl_intent)
            
            result['path'] = 'USER_PATH'
            return result
            
        except Exception as e:
            print(f"❌ USER PATH error: {str(e)}")
            return {
                'status': 'error',
                'path': 'USER_PATH',
                'error': str(e),
                'method': 'cognitive_engine'
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Verificar status do sistema"""
        
        return {
            'master_engine': 'active',
            'resource_router': self.resource_router is not None,
            'cognitive_engine': self.cognitive_engine is not None,
            'mcp_infrastructure_manager': self.mcp_infrastructure_manager is not None,
            'timestamp': datetime.now().isoformat()
        }
    
    def _is_resource_query_request(self, nl_intent: str) -> bool:
        """Detecta solicitações de consulta de recursos"""
        query_patterns = [
            'quais tabelas', 'what tables', 'list tables', 'show tables',
            'quais buckets', 'list buckets', 'show buckets', 'list s3', 'liste todos os buckets',
            'quais instancias', 'list instances', 'show instances', 'show ec2', 'liste todas as instancias',
            'recursos existentes', 'existing resources', 'list lambda', 'show lambda', 'liste todos'
        ]
        
        nl_lower = nl_intent.lower()
        return any(pattern in nl_lower for pattern in query_patterns)

    def process_resource_query_path(self, nl_intent: str) -> Dict[str, Any]:
        """RESOURCE QUERY PATH: Consulta recursos existentes via boto3"""
        
        try:
            # Detectar tipo de recurso
            resource_type = self._detect_resource_type(nl_intent)
            
            # Executar consulta
            if resource_type == 'dynamodb':
                resources = self._list_dynamodb_tables()
            elif resource_type == 's3':
                resources = self._list_s3_buckets()
            elif resource_type == 'ec2':
                resources = self._list_ec2_instances()
            elif resource_type == 'lambda':
                resources = self._list_lambda_functions()
            else:
                resources = self._list_all_resources()
            
            return {
                'status': 'success',
                'path': 'RESOURCE_QUERY_PATH',
                'resource_type': resource_type,
                'resources': resources,
                'count': len(resources),
                'message': f'Encontrados {len(resources)} recursos do tipo {resource_type}',
                'response': f"📋 **{resource_type.upper()} Resources**\n\n{chr(10).join(resources) if resources else 'Nenhum recurso encontrado'}\n\n✅ Total: {len(resources)} recursos"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'path': 'RESOURCE_QUERY_PATH',
                'error': str(e),
                'message': 'Erro ao consultar recursos AWS',
                'response': f"❌ **Erro na Consulta**\n\n{str(e)}\n\n💡 Verifique suas credenciais AWS e tente novamente."
            }

    def _detect_resource_type(self, nl_intent: str) -> str:
        """Detecta tipo de recurso na consulta"""
        nl_lower = nl_intent.lower()
        
        if any(word in nl_lower for word in ['dynamodb', 'tabelas', 'tables']):
            return 'dynamodb'
        elif any(word in nl_lower for word in ['s3', 'buckets', 'bucket']):
            return 's3'
        elif any(word in nl_lower for word in ['ec2', 'instancias', 'instances']):
            return 'ec2'
        elif any(word in nl_lower for word in ['lambda', 'functions', 'funcoes']):
            return 'lambda'
        else:
            return 'all'

    def _list_dynamodb_tables(self) -> List[Dict]:
        """Lista tabelas DynamoDB"""
        import boto3
        dynamodb = boto3.client('dynamodb')
        
        response = dynamodb.list_tables()
        tables = []
        
        for table_name in response['TableNames']:
            try:
                table_info = dynamodb.describe_table(TableName=table_name)
                tables.append({
                    'name': table_name,
                    'status': table_info['Table']['TableStatus'],
                    'items': table_info['Table'].get('ItemCount', 0),
                    'size_bytes': table_info['Table'].get('TableSizeBytes', 0),
                    'created': table_info['Table']['CreationDateTime'].isoformat()
                })
            except:
                tables.append({'name': table_name, 'status': 'unknown'})
        
        return tables

    def _list_s3_buckets(self) -> List[Dict]:
        """Lista buckets S3"""
        import boto3
        s3 = boto3.client('s3')
        
        response = s3.list_buckets()
        buckets = []
        
        for bucket in response['Buckets']:
            buckets.append({
                'name': bucket['Name'],
                'created': bucket['CreationDate'].isoformat()
            })
        
        return buckets

    def _list_ec2_instances(self) -> List[Dict]:
        """Lista instâncias EC2"""
        import boto3
        ec2 = boto3.client('ec2')
        
        response = ec2.describe_instances()
        instances = []
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'id': instance['InstanceId'],
                    'type': instance['InstanceType'],
                    'state': instance['State']['Name'],
                    'launch_time': instance['LaunchTime'].isoformat()
                })
        
        return instances

    def _list_lambda_functions(self) -> List[Dict]:
        """Lista funções Lambda"""
        import boto3
        lambda_client = boto3.client('lambda')
        
        response = lambda_client.list_functions()
        functions = []
        
        for func in response['Functions']:
            functions.append({
                'name': func['FunctionName'],
                'runtime': func['Runtime'],
                'size': func['CodeSize'],
                'modified': func['LastModified']
            })
        
        return functions

    def _list_all_resources(self) -> List[Dict]:
        """Lista resumo de todos os recursos"""
        resources = []
        
        try:
            dynamodb_count = len(self._list_dynamodb_tables())
            resources.append({'type': 'DynamoDB Tables', 'count': dynamodb_count})
        except:
            pass
        
        try:
            s3_count = len(self._list_s3_buckets())
            resources.append({'type': 'S3 Buckets', 'count': s3_count})
        except:
            pass
        
        try:
            ec2_count = len(self._list_ec2_instances())
            resources.append({'type': 'EC2 Instances', 'count': ec2_count})
        except:
            pass
        
        try:
            lambda_count = len(self._list_lambda_functions())
            resources.append({'type': 'Lambda Functions', 'count': lambda_count})
        except:
            pass
        
        return resources
    
    def _format_resource_query_response(self, result: Dict) -> str:
        """Formata resposta de consulta de recursos"""
        
        if result.get('status') != 'success':
            return f"❌ {result.get('message', 'Erro ao consultar recursos')}"
        
        resource_type = result.get('resource_type', 'recursos')
        resources = result.get('resources', [])
        count = result.get('count', 0)
        
        if count == 0:
            return f"📋 Nenhum recurso do tipo {resource_type} encontrado na sua conta AWS."
        
        response_parts = [
            f"📋 **{count} {resource_type.upper()} encontrados na sua conta AWS:**",
            ""
        ]
        
        # Formatação específica por tipo
        if resource_type == 'dynamodb':
            for table in resources[:10]:  # Limitar a 10
                status_emoji = "✅" if table.get('status') == 'ACTIVE' else "⚠️"
                response_parts.append(
                    f"{status_emoji} **{table['name']}** - {table.get('status', 'unknown')} "
                    f"({table.get('items', 0)} itens)"
                )
        
        elif resource_type == 's3':
            for bucket in resources[:10]:
                response_parts.append(f"🪣 **{bucket['name']}** - Criado em {bucket['created'][:10]}")
        
        elif resource_type == 'ec2':
            for instance in resources[:10]:
                state_emoji = "🟢" if instance.get('state') == 'running' else "🔴"
                response_parts.append(
                    f"{state_emoji} **{instance['id']}** ({instance.get('type', 'unknown')}) - "
                    f"{instance.get('state', 'unknown')}"
                )
        
        elif resource_type == 'lambda':
            for func in resources[:10]:
                response_parts.append(
                    f"⚡ **{func['name']}** - {func.get('runtime', 'unknown')} "
                    f"({func.get('size', 0)} bytes)"
                )
        
        elif resource_type == 'all':
            for resource in resources:
                response_parts.append(f"📊 **{resource['type']}**: {resource['count']}")
        
        if len(resources) > 10:
            response_parts.append(f"\n... e mais {len(resources) - 10} recursos")
        
        response_parts.append(f"\n💡 **Total**: {count} recursos encontrados")
        
        return "\n".join(response_parts)
    
    def _check_and_install_dependencies(self):
        """Verifica e instala dependências críticas do sistema"""
        import subprocess
        import sys
        import shutil
        
        print("🔍 Verificando dependências críticas...")
        
        # 1. Dependências Python ESSENCIAIS
        python_deps = ['aiohttp', 'boto3', 'psutil', 'pyyaml', 'requests']
        for dep in python_deps:
            try:
                __import__(dep)
                print(f"✅ Python: {dep}")
            except ImportError:
                print(f"⚠️ Instalando {dep}...")
                self._install_python_package(dep)
        
        # 2. AWS CLI
        if shutil.which('aws'):
            print("✅ AWS CLI disponível")
        else:
            print("⚠️ AWS CLI não encontrado, instalando...")
            self._install_aws_cli()
        
        # 3. Node.js (necessário para CDK)
        if shutil.which('node'):
            print("✅ Node.js disponível")
        else:
            print("⚠️ Node.js não encontrado, instalando...")
            self._install_nodejs()
        
        # 4. AWS CDK
        if shutil.which('cdk'):
            print("✅ AWS CDK disponível")
        else:
            print("⚠️ AWS CDK não encontrado, instalando...")
            self._install_aws_cdk()
        
        print("🔧 Todas as dependências verificadas")

    def _install_python_package(self, package):
        """Instala pacote Python via apt ou pip"""
        import subprocess
        import sys
        
        # Mapeamento correto: módulo Python -> nome do pacote apt
        package_mapping = {
            'aiohttp': 'python3-aiohttp',
            'boto3': 'python3-boto3', 
            'psutil': 'python3-psutil',
            'openai': 'python3-openai',
            'pyyaml': 'python3-yaml',  # CORREÇÃO: pyyaml -> python3-yaml
            'requests': 'python3-requests'
        }
        
        apt_package = package_mapping.get(package, f'python3-{package}')
        
        try:
            subprocess.run(['apt', 'install', '-y', apt_package], 
                         check=True, capture_output=True)
            print(f"✅ {package} instalado via apt ({apt_package})")
        except:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package, '--break-system-packages'], 
                             check=True, capture_output=True)
                print(f"✅ {package} instalado via pip")
            except Exception as e:
                print(f"❌ Falha ao instalar {package}: {e}")

    def _install_aws_cli(self):
        """Instala AWS CLI v2"""
        import subprocess
        
        try:
            # Método oficial AWS CLI v2
            subprocess.run(['curl', 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip', '-o', '/tmp/awscliv2.zip'], check=True)
            subprocess.run(['unzip', '-q', '/tmp/awscliv2.zip', '-d', '/tmp/'], check=True)
            subprocess.run(['/tmp/aws/install'], check=True)
            print("✅ AWS CLI v2 instalado")
        except Exception as e:
            print(f"❌ Falha ao instalar AWS CLI: {e}")
            print("💡 Execute manualmente: curl + install AWS CLI v2")

    def _install_nodejs(self):
        """Instala Node.js via NodeSource"""
        import subprocess
        
        try:
            # NodeSource oficial (LTS)
            subprocess.run(['curl', '-fsSL', 'https://deb.nodesource.com/setup_lts.x', '|', 'bash', '-'], 
                         shell=True, check=True)
            subprocess.run(['apt', 'install', '-y', 'nodejs'], check=True)
            print("✅ Node.js LTS instalado")
        except Exception as e:
            print(f"❌ Falha ao instalar Node.js: {e}")
            print("💡 Execute manualmente: apt install nodejs npm")

    def _install_aws_cdk(self):
        """Instala AWS CDK via npm"""
        import subprocess
        
        try:
            subprocess.run(['npm', 'install', '-g', 'aws-cdk'], check=True)
            print("✅ AWS CDK instalado globalmente")
        except Exception as e:
            print(f"❌ Falha ao instalar CDK: {e}")
            print("💡 Execute manualmente: npm install -g aws-cdk")
