#!/usr/bin/env python3
"""
LLM Clarification Engine - REAL LLM + MCP Implementation
"""

import asyncio
from typing import Dict, List, Any, Optional
import json
import re

class LLMClarificationEngine:
    """Engine para análise inteligente de requisitos usando LLM + MCP REAL"""
    
    def __init__(self, llm_provider, mcp_orchestrator):
        self.llm_provider = llm_provider
        self.mcp_orchestrator = mcp_orchestrator
    
    async def analyze_and_clarify(self, user_request: str) -> Dict[str, Any]:
        """Usa LLM REAL para analisar requisitos e gerar perguntas inteligentes"""
        
        # BYPASS: Comandos específicos que não precisam clarificação
        if self._has_sufficient_details(user_request):
            return {
                'status': 'ready_to_generate',
                'confidence': 0.9,
                'reasoning': 'Command has sufficient details for generation'
            }
        
        # PRIMEIRO: Verificar se é uma resposta a pergunta anterior
        if self._is_answer_to_question(user_request):
            return {
                'status': 'ready_to_generate',
                'confidence': 0.8,
                'reasoning': 'User provided answer to clarification question'
            }
        
        # USAR LLM REAL para análise inteligente
        try:
            print("🧠 Using REAL LLM for analysis...")
            analysis = await self._analyze_with_real_llm(user_request)
            
            if analysis.get('status') == 'needs_clarification':
                # Gerar perguntas inteligentes via LLM+MCP REAL
                questions = await self._generate_real_intelligent_questions(user_request, analysis)
                
                if questions:
                    formatted_response = self._format_clarification_questions(questions, user_request)
                    return {
                        'status': 'needs_clarification',
                        'response': formatted_response,
                        'questions': questions,
                        'confidence': analysis.get('confidence', 0.7),
                        'reasoning': 'REAL LLM+MCP analysis completed',
                        'llm_used': True
                    }
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ REAL LLM failed: {e}, using intelligent fallback")
            return await self._intelligent_fallback_analysis(user_request)
    
    async def _analyze_with_real_llm(self, user_request: str) -> Dict[str, Any]:
        """Análise REAL usando Bedrock com prompt engineering otimizado"""
        
        # PROMPT ENGINEERING ESPECÍFICO PARA BEDROCK
        bedrock_prompt = f"""
Você é um especialista AWS que analisa requisitos de infraestrutura.

TAREFA: Analise se este requisito precisa de clarificação adicional.

REQUISITO: "{user_request}"

CRITÉRIOS:
- Se faltam detalhes técnicos específicos → needs_clarification
- Se tem informações suficientes para implementar → ready_to_generate

RESPONDA EXATAMENTE neste formato JSON:
{{
    "status": "needs_clarification",
    "confidence": 0.8,
    "reasoning": "Faltam detalhes sobre tipo de banco e volume",
    "missing_details": ["database_type", "performance_requirements", "scaling_needs"]
}}

OU

{{
    "status": "ready_to_generate",
    "confidence": 0.9,
    "reasoning": "Requisito tem detalhes suficientes"
}}

ANÁLISE:
"""
        
        try:
            # Usar LLM Provider REAL
            llm_response = await self.llm_provider.generate_response(bedrock_prompt)
            
            # PARSING ROBUSTO da resposta
            analysis = self._parse_llm_response(llm_response)
            
            print(f"✅ REAL LLM Analysis: {analysis.get('status')} (confidence: {analysis.get('confidence')})")
            return analysis
            
        except Exception as e:
            print(f"⚠️ LLM analysis error: {e}")
            raise e
    
    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse robusto da resposta do LLM com múltiplos fallbacks"""
        
        try:
            # Tentar parsing direto se for string JSON
            if isinstance(llm_response, str) and llm_response.strip().startswith('{'):
                return json.loads(llm_response)
            
            # Se for dict do LLM Provider, extrair texto
            if isinstance(llm_response, dict):
                text = llm_response.get('response', llm_response.get('processed_text', str(llm_response)))
            else:
                text = str(llm_response)
            
            # Extrair JSON da resposta usando regex
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            
            # Fallback: análise baseada em keywords
            return self._keyword_based_analysis(text)
            
        except Exception as e:
            print(f"⚠️ Parse error: {e}, using keyword analysis")
            return self._keyword_based_analysis(str(llm_response))
    
    def _keyword_based_analysis(self, text: str) -> Dict[str, Any]:
        """Análise baseada em keywords quando JSON parsing falha"""
        
        text_lower = text.lower()
        
        # Indicadores de que precisa clarificação
        needs_clarification_indicators = [
            'needs_clarification', 'precisa', 'falta', 'missing', 'unclear',
            'specify', 'details', 'more information'
        ]
        
        # Indicadores de que está pronto
        ready_indicators = [
            'ready_to_generate', 'sufficient', 'complete', 'clear',
            'enough information', 'ready'
        ]
        
        if any(indicator in text_lower for indicator in needs_clarification_indicators):
            return {
                'status': 'needs_clarification',
                'confidence': 0.6,
                'reasoning': 'LLM indicated clarification needed (keyword analysis)'
            }
        elif any(indicator in text_lower for indicator in ready_indicators):
            return {
                'status': 'ready_to_generate',
                'confidence': 0.7,
                'reasoning': 'LLM indicated ready to generate (keyword analysis)'
            }
        else:
            # Default: assume needs clarification for safety
            return {
                'status': 'needs_clarification',
                'confidence': 0.5,
                'reasoning': 'Unclear LLM response, defaulting to clarification'
            }
    
    async def _generate_real_intelligent_questions(self, user_request: str, analysis: Dict) -> List[Dict[str, Any]]:
        """Gera perguntas REAIS usando LLM + MCP consultation"""
        
        questions = []
        
        # 1. WORKLOAD_NAME sempre hardcoded (necessário para organização)
        questions.append({
            'question': 'Qual o nome do workload/projeto?',
            'context': 'Usado para organizar arquivos em /phases/workloads/{nome}',
            'options': ['Nome personalizado (ex: api-backend)', 'Gerar automaticamente', 'Usar estrutura atual (99-misc)'],
            'source': 'hardcoded'
        })
        
        # 2. DETECTAR SERVIÇO PRINCIPAL
        primary_service = self._detect_primary_service(user_request)
        print(f"🎯 Primary service detected: {primary_service}")
        
        # 3. CONSULTAR MCP SERVER REAL para contexto específico
        mcp_context = await self._get_real_mcp_context(primary_service)
        print(f"📡 MCP context obtained: {len(mcp_context)} chars")
        
        # 4. USAR LLM REAL para gerar perguntas contextuais
        llm_questions = await self._generate_llm_questions_real(user_request, primary_service, mcp_context, analysis)
        questions.extend(llm_questions)
        
        return questions[:3]  # Máximo 3 perguntas
    
    async def _get_real_mcp_context(self, service: str) -> str:
        """Consulta MCP Server REAL para obter contexto específico do serviço"""
        
        # Mapeamento de serviços para MCPs específicos REAIS
        service_mcp_mapping = {
            'rds': 'aws-rds-mcp',
            'dynamodb': 'aws-dynamodb-mcp', 
            'ecs': 'awslabs.ecs-mcp-server',
            's3': 'aws-s3-mcp',
            'lambda': 'aws-lambda-mcp',
            'elasticache': 'awslabs.elasticache-mcp-server',
            'vpc': 'aws-vpc-mcp',
            'ec2': 'aws-ec2-mcp'
        }
        
        mcp_server = service_mcp_mapping.get(service, 'aws-general-mcp')
        
        try:
            print(f"📡 Querying MCP server: {mcp_server} for {service}")
            
            # Consultar MCP REAL
            context = await self.mcp_orchestrator.query_mcp_for_service_options(mcp_server, service)
            
            # Se contexto muito genérico, enriquecer com conhecimento específico
            if len(context) < 100:
                context = self._enrich_service_context(service, context)
            
            return context
                
        except Exception as e:
            print(f"⚠️ MCP query error: {e}")
            return self._get_fallback_service_context(service)
    
    def _enrich_service_context(self, service: str, basic_context: str) -> str:
        """Enriquece contexto básico com conhecimento específico do serviço"""
        
        enriched_contexts = {
            'rds': f"{basic_context}\n\nRDS Options: MySQL (5.7, 8.0), PostgreSQL (13, 14, 15), Aurora MySQL, Aurora PostgreSQL. Multi-AZ for HA, Read Replicas for scaling. Instance types: db.t3.micro (dev), db.r5.large (prod).",
            
            'dynamodb': f"{basic_context}\n\nDynamoDB: NoSQL serverless, pay-per-request or provisioned capacity. Global Tables for multi-region. On-Demand for unpredictable workloads, Provisioned for consistent traffic.",
            
            'ecs': f"{basic_context}\n\nECS Options: Fargate (serverless containers) or EC2 (managed instances). Fargate: no server management, higher cost. EC2: more control, lower cost. ALB for load balancing.",
            
            's3': f"{basic_context}\n\nS3 Storage Classes: Standard (frequent access), IA (infrequent), Glacier (archive). Static website hosting with CloudFront CDN. Versioning and lifecycle policies available.",
            
            'lambda': f"{basic_context}\n\nLambda: Serverless functions, 15min max runtime. Memory: 128MB-10GB. Runtimes: Python 3.11, Node.js 18, Java 17. Triggers: API Gateway, S3, DynamoDB, EventBridge.",
            
            'elasticache': f"{basic_context}\n\nElastiCache: Redis (data structures, persistence) or Memcached (simple caching). Redis Cluster for scaling. Multi-AZ for HA. Node types: cache.t3.micro (dev), cache.r6g.large (prod)."
        }
        
        return enriched_contexts.get(service, f"{basic_context}\n\nAWS {service} service with multiple configuration options available.")
    
    def _get_fallback_service_context(self, service: str) -> str:
        """Contexto fallback quando MCP falha"""
        
        fallback_contexts = {
            'rds': 'RDS: Managed relational databases (MySQL, PostgreSQL, Aurora). Choose Multi-AZ for high availability, Read Replicas for read scaling.',
            'dynamodb': 'DynamoDB: NoSQL serverless database. On-Demand pricing for variable workloads, Provisioned for predictable traffic.',
            'ecs': 'ECS: Container orchestration. Fargate for serverless containers, EC2 for more control and lower costs.',
            's3': 'S3: Object storage with multiple storage classes. Can host static websites with CloudFront for global distribution.',
            'lambda': 'Lambda: Serverless compute for event-driven applications. Multiple runtime options and trigger sources.',
            'elasticache': 'ElastiCache: In-memory caching with Redis or Memcached. Redis for advanced features, Memcached for simple caching.'
        }
        
        return fallback_contexts.get(service, f'AWS {service} service with configurable options for different use cases.')
    
    async def _generate_llm_questions_real(self, user_request: str, primary_service: str, mcp_context: str, analysis: Dict) -> List[Dict[str, Any]]:
        """Usa LLM REAL para gerar perguntas específicas e inteligentes"""
        
        # PROMPT ENGINEERING OTIMIZADO PARA BEDROCK
        llm_prompt = f"""
Você é um especialista AWS. Gere 2 perguntas específicas para completar este requisito de infraestrutura.

REQUISITO: {user_request}
SERVIÇO PRINCIPAL: {primary_service}
CONTEXTO MCP: {mcp_context}

GERE perguntas que ajudem a escolher entre opções REAIS do AWS {primary_service}:
- Perguntas específicas com opções técnicas reais
- Contexto sobre trade-offs (custo/performance/complexidade)
- Opções práticas baseadas no contexto MCP

FORMATO EXATO (JSON válido):
[
  {{
    "question": "Pergunta específica sobre {primary_service}?",
    "context": "Explicação técnica do trade-off",
    "options": ["Opção 1 real", "Opção 2 real", "Opção 3 real"]
  }},
  {{
    "question": "Segunda pergunta específica?",
    "context": "Contexto técnico",
    "options": ["Opção A", "Opção B", "Opção C"]
  }}
]

PERGUNTAS:
"""

        try:
            print("🧠 Generating questions with REAL LLM...")
            llm_response = await self.llm_provider.generate_response(llm_prompt)
            
            # Parse resposta do LLM
            questions = self._parse_llm_questions(llm_response)
            
            if questions:
                print(f"✅ Generated {len(questions)} intelligent questions via LLM")
                for q in questions:
                    q['source'] = 'llm_mcp'
                return questions
            else:
                print("⚠️ LLM questions parsing failed, using intelligent fallback")
                return self._get_intelligent_fallback_questions(primary_service)
                
        except Exception as e:
            print(f"⚠️ LLM questions error: {e}")
            return self._get_intelligent_fallback_questions(primary_service)
    
    def _parse_llm_questions(self, llm_response: str) -> List[Dict[str, Any]]:
        """Parse robusto das perguntas geradas pelo LLM"""
        
        try:
            # Se for dict do LLM Provider, extrair texto
            if isinstance(llm_response, dict):
                text = llm_response.get('response', llm_response.get('processed_text', str(llm_response)))
            else:
                text = str(llm_response)
            
            # Tentar extrair array JSON
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                questions = json.loads(json_str)
                
                # Validar estrutura das perguntas
                valid_questions = []
                for q in questions:
                    if isinstance(q, dict) and 'question' in q:
                        valid_questions.append({
                            'question': q.get('question', ''),
                            'context': q.get('context', ''),
                            'options': q.get('options', [])
                        })
                
                return valid_questions
            
            return []
            
        except Exception as e:
            print(f"⚠️ Questions parse error: {e}")
            return []
    
    def _get_intelligent_fallback_questions(self, service: str) -> List[Dict[str, Any]]:
        """Perguntas fallback inteligentes por serviço quando LLM falha"""
        
        intelligent_fallbacks = {
            'rds': [
                {
                    'question': 'Você prefere RDS (gerenciado) ou DynamoDB (NoSQL)?',
                    'context': 'RDS é melhor para dados relacionais com ACID, DynamoDB para alta escala e performance',
                    'options': ['RDS MySQL/PostgreSQL', 'RDS Aurora (recomendado)', 'DynamoDB NoSQL']
                },
                {
                    'question': 'Precisa de alta disponibilidade (Multi-AZ)?',
                    'context': 'Multi-AZ duplica custos mas garante 99.95% uptime com failover automático',
                    'options': ['Sim, Multi-AZ (produção)', 'Não, Single-AZ (desenvolvimento)', 'Read Replicas apenas']
                }
            ],
            'ecs': [
                {
                    'question': 'Você prefere Fargate (serverless) ou EC2 (controle total)?',
                    'context': 'Fargate é mais simples e sem gerenciamento, EC2 oferece mais controle e menor custo',
                    'options': ['Fargate (recomendado)', 'EC2 com Auto Scaling', 'EC2 Spot para economia']
                },
                {
                    'question': 'Como será o acesso externo?',
                    'context': 'ALB para HTTP/HTTPS, NLB para TCP/UDP, sem load balancer para interno apenas',
                    'options': ['Application Load Balancer (HTTP)', 'Network Load Balancer (TCP)', 'Sem acesso externo']
                }
            ],
            's3': [
                {
                    'question': 'Precisa de website estático ou apenas storage?',
                    'context': 'S3 pode hospedar sites com CloudFront para CDN global e melhor performance',
                    'options': ['Website estático + CloudFront', 'Storage de arquivos apenas', 'Ambos']
                },
                {
                    'question': 'Qual classe de storage você precisa?',
                    'context': 'Standard para acesso frequente, IA para infrequente, Glacier para arquivo',
                    'options': ['Standard (acesso frequente)', 'Intelligent-Tiering (automático)', 'Infrequent Access (economia)']
                }
            ],
            'lambda': [
                {
                    'question': 'Qual runtime você vai usar?',
                    'context': 'Diferentes runtimes têm diferentes performance e cold start times',
                    'options': ['Python 3.11 (recomendado)', 'Node.js 18', 'Java 17']
                },
                {
                    'question': 'Qual será o trigger principal?',
                    'context': 'Diferentes triggers têm diferentes configurações e limites',
                    'options': ['API Gateway (REST API)', 'EventBridge (eventos)', 'S3 (upload de arquivos)']
                }
            ],
            'elasticache': [
                {
                    'question': 'Você prefere Redis ou Memcached?',
                    'context': 'Redis tem mais features (persistência, estruturas), Memcached é mais simples',
                    'options': ['Redis (recomendado)', 'Memcached (simples)', 'Redis Cluster (escala)']
                }
            ]
        }
        
        return intelligent_fallbacks.get(service, [
            {
                'question': f'Qual configuração você precisa para {service}?',
                'context': f'Diferentes configurações de {service} têm diferentes trade-offs',
                'options': ['Configuração básica', 'Configuração de produção', 'Configuração customizada']
            }
        ])
    
    def _detect_primary_service(self, user_request: str) -> str:
        """Detecta o serviço principal do requisito com melhor precisão"""
        request_lower = user_request.lower()
        
        # Mapeamento mais específico
        service_keywords = {
            'rds': ['banco de dados', 'database', 'mysql', 'postgresql', 'rds', 'relacional', 'sql'],
            'dynamodb': ['nosql', 'dynamodb', 'chave-valor', 'key-value', 'document'],
            'ecs': ['container', 'docker', 'ecs', 'fargate', 'containerizar'],
            's3': ['storage', 'arquivo', 'bucket', 's3', 'website', 'static'],
            'lambda': ['serverless', 'função', 'lambda', 'event', 'trigger'],
            'elasticache': ['cache', 'redis', 'memcached', 'elasticache', 'caching'],
            'vpc': ['rede', 'network', 'vpc', 'subnet', 'networking'],
            'ec2': ['instancia', 'instance', 'ec2', 'virtual machine', 'vm']
        }
        
        # Score por serviço
        service_scores = {}
        for service, keywords in service_keywords.items():
            score = sum(1 for keyword in keywords if keyword in request_lower)
            if score > 0:
                service_scores[service] = score
        
        # Retornar serviço com maior score
        if service_scores:
            return max(service_scores, key=service_scores.get)
        
        return 'general'
    
    async def _intelligent_fallback_analysis(self, user_request: str) -> Dict[str, Any]:
        """Fallback inteligente quando LLM falha completamente"""
        try:
            # Análise básica de gaps
            questions = await self._generate_real_intelligent_questions(user_request, {'status': 'needs_clarification'})
            
            if questions:
                formatted_response = self._format_clarification_questions(questions, user_request)
                return {
                    'status': 'needs_clarification',
                    'response': formatted_response,
                    'questions': questions,
                    'confidence': 0.6,
                    'reasoning': 'Intelligent fallback analysis with MCP context',
                    'llm_used': False
                }
            
        except Exception as e:
            print(f"⚠️ Intelligent fallback error: {e}")
        
        # Último fallback - sempre permite prosseguir
        return {
            'status': 'ready_to_generate',
            'confidence': 0.4,
            'reasoning': 'Emergency fallback - proceeding with available information'
        }
    
    def _format_clarification_questions(self, questions: List[Dict[str, Any]], user_request: str) -> str:
        """Formata perguntas de clarificação para o usuário"""
        
        # Salvar perguntas na sessão conversacional
        try:
            from core.conversation_state_manager import ConversationStateManager
            conversation_manager = ConversationStateManager()
            session_id = conversation_manager.start_session()
            conversation_manager.add_clarification_questions(session_id, questions)
            print(f"📝 Added {len(questions)} questions to session {session_id}")
        except Exception as e:
            print(f"⚠️ Erro saving questions: {e}")
        
        # Formatar resposta com indicador de fonte
        llm_used = any(q.get('source') == 'llm_mcp' for q in questions)
        source_indicator = "🧠 LLM+MCP" if llm_used else "🤖 Intelligent Fallback"
        
        response = f"🤔 **Preciso de mais detalhes sobre: '{user_request}'** ({source_indicator})\n\n"
        
        for i, q in enumerate(questions, 1):
            response += f"**{i}. {q['question']}**\n"
            if q.get('context'):
                response += f"💡 *{q['context']}*\n"
            if q.get('options'):
                for j, option in enumerate(q['options'], 1):
                    response += f"   {j}. {option}\n"
            response += "\n"
        
        response += "📝 **Responda com detalhes ou números das opções para prosseguir.**"
        
        return response
    
    def _is_answer_to_question(self, request: str) -> bool:
        """Check if request is an answer to a previous clarification question"""
        request_lower = request.lower()
        
        # Answer patterns expandidos
        answer_patterns = [
            'sim', 'não', 'yes', 'no', 'rds', 'dynamodb', 'redis', 'memcached',
            'multi-az', 'single-az', 'público', 'privado', 'vpc', 'internet',
            'fargate', 'ec2', 'lambda', 'mysql', 'postgresql', 'aurora',
            't3.', 't2.', 'm5.', 'c5.', 'r5.', # instance types
            'gb', 'tb', 'mb', # storage sizes
            '1', '2', '3', '4', '5', # option numbers
            'standard', 'infrequent', 'glacier', 'cloudfront'
        ]
        
        # Check if request contains answer-like patterns
        return any(pattern in request_lower for pattern in answer_patterns)
    
    def _has_sufficient_details(self, request: str) -> bool:
        """Check if request has sufficient details to bypass clarification"""
        request_lower = request.lower()
        
        # APENAS comandos MUITO específicos com TODOS os detalhes necessários
        ultra_specific_patterns = [
            # RDS com engine e configuração específica
            ('rds' in request_lower and ('mysql' in request_lower or 'postgresql' in request_lower) and 
             ('multi-az' in request_lower or 'single-az' in request_lower)),
            
            # DynamoDB com configuração específica
            ('dynamodb' in request_lower and ('on-demand' in request_lower or 'provisioned' in request_lower)),
            
            # ECS com Fargate/EC2 específico
            ('ecs' in request_lower and ('fargate' in request_lower or 'ec2' in request_lower) and
             'alb' in request_lower),
            
            # Lambda com runtime específico
            ('lambda' in request_lower and ('python' in request_lower or 'node' in request_lower) and 
             ('api gateway' in request_lower or 'eventbridge' in request_lower)),
        ]
        
        return any(pattern for pattern in ultra_specific_patterns)
