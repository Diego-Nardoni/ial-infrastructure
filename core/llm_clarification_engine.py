"""
LLM-Powered Clarification Engine
Usa LLM + MCP para detectar requisitos faltantes e fazer perguntas inteligentes
"""

import json
from typing import Dict, List, Any, Optional

class LLMClarificationEngine:
    def __init__(self, llm_provider, mcp_orchestrator):
        self.llm_provider = llm_provider
        self.mcp_orchestrator = mcp_orchestrator
        
        self.clarification_prompt = """
Você é um especialista AWS que ajuda usuários a especificar requisitos de infraestrutura.

TAREFA: Analisar a solicitação do usuário e identificar informações faltantes críticas.

REGRAS:
1. Se a solicitação está COMPLETA e específica → retorne {"needs_clarification": false}
2. Se faltam informações CRÍTICAS → retorne {"needs_clarification": true, "questions": [...]}
3. Faça NO MÁXIMO 3 perguntas mais importantes
4. Perguntas devem ser específicas e técnicas
5. Inclua opções quando apropriado

EXEMPLOS:
- "crie um bucket s3" → COMPLETO (bucket básico é suficiente)
- "crie uma ecs" → INCOMPLETO (falta task definition, networking, etc.)
- "preciso de database" → INCOMPLETO (tipo, tamanho, uso, etc.)

FORMATO DE RESPOSTA:
{{
  "needs_clarification": true,
  "confidence": 0.5,
  "questions": [
    {{
      "question": "Pergunta específica?",
      "context": "Por que essa informação é importante",
      "options": ["Opção 1", "Opção 2", "Opção 3"]
    }}
  ],
  "reasoning": "Por que essas perguntas são necessárias"
}}

SOLICITAÇÃO DO USUÁRIO: {user_request}
"""

    async def analyze_and_clarify(self, user_request: str) -> Dict[str, Any]:
        """Usa LLM para analisar requisitos e gerar perguntas inteligentes"""
        
        print(f"🔍 DEBUG LLM: Analisando requisito: {user_request}")
        
        # Verificar se LLM provider está disponível
        if not self.llm_provider:
            print(f"⚠️ LLM provider não disponível, usando fallback MCP")
            return await self._fallback_mcp_analysis(user_request)
        
        # Usar LLM para análise inteligente
        print(f"🔍 DEBUG LLM: Preparando prompt...")
        try:
            prompt = self.clarification_prompt.format(user_request=user_request)
            print(f"🔍 DEBUG LLM: Prompt preparado, tamanho: {len(prompt)} chars")
        except Exception as prompt_error:
            print(f"⚠️ Erro ao formatar prompt: {prompt_error}, usando fallback MCP")
            return await self._fallback_mcp_analysis(user_request)
        
        print(f"🔍 DEBUG LLM: Entrando no try block...")
        try:
            print(f"🔍 DEBUG LLM: Enviando para LLM...")
            
            # Implementar timeout robusto para evitar travamento
            import asyncio
            try:
                llm_response = await asyncio.wait_for(
                    self.llm_provider.process_natural_language_async(prompt),
                    timeout=15.0  # 15 segundos timeout
                )
                print(f"🔍 DEBUG LLM: Resposta recebida: {type(llm_response)}")
            except asyncio.TimeoutError:
                print(f"⚠️ LLM timeout após 15s, usando fallback MCP")
                return await self._fallback_mcp_analysis(user_request)
            except Exception as llm_error:
                print(f"⚠️ Erro específico do LLM: {llm_error}, usando fallback MCP")
                return await self._fallback_mcp_analysis(user_request)
            
            # Parse da resposta LLM com error handling robusto
            try:
                if isinstance(llm_response, str):
                    # Tentar extrair JSON da resposta se estiver em markdown ou texto
                    import re
                    json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                    else:
                        # Se não encontrar JSON, usar fallback MCP
                        print(f"🔍 DEBUG LLM: Resposta não contém JSON válido, usando fallback MCP")
                        return await self._fallback_mcp_analysis(user_request)
                else:
                    analysis = llm_response
                    
                print(f"🔍 DEBUG LLM: Análise parseada: {analysis.get('needs_clarification')}")
                
            except (json.JSONDecodeError, KeyError, AttributeError) as parse_error:
                print(f"⚠️ Erro no parsing da resposta LLM: {parse_error}, usando fallback MCP")
                return await self._fallback_mcp_analysis(user_request)
            
            # Se não precisa clarificação, retorna direto
            if not analysis.get('needs_clarification', False):
                print(f"🔍 DEBUG LLM: Requisitos suficientes, prosseguindo")
                return {
                    'status': 'ready_to_generate',
                    'confidence': analysis.get('confidence', 0.8),
                    'reasoning': analysis.get('reasoning', 'Requisitos suficientes')
                }
            
            # Se precisa clarificação, formatar perguntas
            questions = analysis.get('questions', [])
            if not questions:
                print(f"🔍 DEBUG LLM: LLM não gerou perguntas, usando fallback MCP")
                # Fallback se LLM não gerou perguntas
                return await self._fallback_mcp_analysis(user_request)
            
            print(f"🔍 DEBUG LLM: Formatando {len(questions)} perguntas")
            formatted_response = self._format_clarification_questions(questions, user_request)
            
            return {
                'status': 'needs_clarification',
                'response': formatted_response,
                'questions': questions,
                'confidence': analysis.get('confidence', 0.3),
                'reasoning': analysis.get('reasoning', 'Informações adicionais necessárias')
            }
            
        except Exception as e:
            print(f"⚠️ Erro geral na análise LLM: {e}")
            print(f"🔍 DEBUG LLM: Usando fallback MCP por erro geral")
            # Fallback para análise MCP - NUNCA FALHA
            return await self._fallback_mcp_analysis(user_request)
    
    async def _fallback_mcp_analysis(self, user_request: str) -> Dict[str, Any]:
        """Fallback usando MCP para análise quando LLM falha - ENTERPRISE GRADE"""
        try:
            print(f"🔍 DEBUG MCP: Iniciando análise MCP para: {user_request}")
            
            # Usar MCP para detectar serviços e gaps
            mcp_analysis = await self.mcp_orchestrator.analyze_requirements(user_request)
            print(f"🔍 DEBUG MCP: Análise MCP completa: {mcp_analysis.get('complete')}")
            print(f"🔍 DEBUG MCP: Serviços detectados: {mcp_analysis.get('detected_services')}")
            print(f"🔍 DEBUG MCP: Informações faltantes: {mcp_analysis.get('missing_info')}")
            
            if mcp_analysis.get('complete', False):
                print(f"🔍 DEBUG MCP: Requisitos completos, prosseguindo com geração")
                return {
                    'status': 'ready_to_generate',
                    'confidence': mcp_analysis.get('confidence', 0.7),
                    'reasoning': 'MCP analysis indicates complete requirements'
                }
            
            # Gerar perguntas baseadas em gaps do MCP
            gaps = mcp_analysis.get('missing_info', [])
            primary_service = mcp_analysis.get('primary_service', 'unknown')
            
            if not gaps:
                print(f"🔍 DEBUG MCP: Nenhum gap detectado, prosseguindo com geração")
                return {
                    'status': 'ready_to_generate',
                    'confidence': 0.6,
                    'reasoning': 'No specific gaps detected by MCP'
                }
            
            print(f"🔍 DEBUG MCP: Gerando perguntas para {len(gaps)} gaps")
            questions = self._generate_questions_from_gaps(gaps, primary_service, user_request)
            
            if not questions:
                print(f"🔍 DEBUG MCP: Nenhuma pergunta gerada, prosseguindo com geração")
                return {
                    'status': 'ready_to_generate',
                    'confidence': 0.5,
                    'reasoning': 'MCP could not generate specific questions'
                }
            
            print(f"🔍 DEBUG MCP: Formatando {len(questions)} perguntas")
            formatted_response = self._format_clarification_questions(questions, user_request)
            
            return {
                'status': 'needs_clarification',
                'response': formatted_response,
                'questions': questions,
                'confidence': mcp_analysis.get('confidence', 0.5),
                'reasoning': f'MCP detected missing information for {primary_service}: {gaps}',
                'mcp_analysis': mcp_analysis
            }
            
        except Exception as e:
            print(f"⚠️ Erro no fallback MCP: {e}")
            print(f"🔍 DEBUG MCP: Erro crítico, usando último fallback")
            # Último fallback - NUNCA FALHA, sempre permite prosseguir
            return {
                'status': 'ready_to_generate',
                'confidence': 0.4,
                'reasoning': f'Emergency fallback - proceeding with available information. Error: {str(e)}'
            }
    
    def _generate_questions_from_gaps(self, gaps: List[str], primary_service: str, user_request: str) -> List[Dict[str, Any]]:
        """Gera perguntas baseadas nos gaps identificados pelo MCP"""
        questions = []
        
        # Mapeamento de gaps para perguntas por serviço
        service_gap_questions = {
            'ecs': {
                'task_definition': {
                    'question': 'Qual aplicação você quer containerizar?',
                    'context': 'Preciso saber a imagem Docker, CPU, memória e portas',
                    'options': ['Aplicação web (nginx/apache)', 'API backend (node/python)', 'Worker/batch job', 'Microserviço customizado']
                },
                'networking': {
                    'question': 'Como será o acesso de rede?',
                    'context': 'Define se usa VPC pública, privada ou load balancer',
                    'options': ['Público com ALB', 'Privado (VPC)', 'Sem acesso externo']
                },
                'scaling': {
                    'question': 'Quantas instâncias você precisa?',
                    'context': 'Define configurações de auto scaling',
                    'options': ['1 instância (desenvolvimento)', '2-5 instâncias (produção)', 'Auto scaling baseado em CPU']
                }
            },
            'rds': {
                'database_engine': {
                    'question': 'Qual engine de banco você prefere?',
                    'context': 'Cada engine tem características diferentes',
                    'options': ['MySQL (compatibilidade)', 'PostgreSQL (recursos avançados)', 'Aurora (performance)']
                },
                'instance_size': {
                    'question': 'Qual o tamanho esperado do banco?',
                    'context': 'Define tipo de instância e storage',
                    'options': ['Pequeno (db.t3.micro)', 'Médio (db.t3.small)', 'Grande (db.m5.large)']
                },
                'availability': {
                    'question': 'Precisa de alta disponibilidade?',
                    'context': 'Multi-AZ aumenta disponibilidade mas dobra o custo',
                    'options': ['Sim, crítico (Multi-AZ)', 'Não, desenvolvimento (Single-AZ)', 'Backup apenas']
                }
            },
            'lambda': {
                'runtime': {
                    'question': 'Qual linguagem você vai usar?',
                    'context': 'Define o runtime environment',
                    'options': ['Python 3.11', 'Node.js 18', 'Java 17', 'Go 1.x']
                },
                'performance_config': {
                    'question': 'Qual performance você precisa?',
                    'context': 'Define memória, timeout e concorrência',
                    'options': ['Baixa (128MB, 3s)', 'Média (512MB, 15s)', 'Alta (3GB, 15min)']
                }
            }
        }
        
        # Perguntas genéricas para gaps não mapeados
        generic_questions = {
            'instance_type': {
                'question': 'Qual tipo de instância você precisa?',
                'context': 'Isso afeta performance e custo',
                'options': ['t3.micro (desenvolvimento)', 't3.small (teste)', 'm5.large (produção)']
            },
            'networking': {
                'question': 'Como será o acesso de rede?',
                'context': 'Define configurações de VPC e security groups',
                'options': ['Público (internet)', 'Privado (VPC)', 'Híbrido']
            },
            'storage': {
                'question': 'Que tipo de storage você precisa?',
                'context': 'Diferentes tipos têm diferentes performance e custos',
                'options': ['GP3 (geral)', 'IO2 (alta performance)', 'ST1 (throughput)']
            }
        }
        
        # Usar perguntas específicas do serviço se disponível
        service_questions = service_gap_questions.get(primary_service, {})
        
        for gap in gaps[:3]:  # Máximo 3 perguntas
            if gap in service_questions:
                questions.append(service_questions[gap])
            elif gap in generic_questions:
                questions.append(generic_questions[gap])
            else:
                # Pergunta genérica para gaps não mapeados
                questions.append({
                    'question': f'Você pode especificar mais detalhes sobre {gap.replace("_", " ")}?',
                    'context': 'Essa informação é necessária para gerar a configuração correta',
                    'options': []
                })
        
        return questions
    
    def _format_clarification_questions(self, questions: List[Dict[str, Any]], user_request: str) -> str:
        """Formata perguntas para exibição ao usuário"""
        response = f"🤔 **Preciso de mais detalhes sobre: '{user_request}'**\n\n"
        
        for i, q in enumerate(questions, 1):
            response += f"**{i}. {q['question']}**\n"
            
            if 'options' in q and q['options']:
                for j, option in enumerate(q['options'], 1):
                    response += f"   {j}) {option}\n"
            
            if 'context' in q and q['context']:
                response += f"   💡 *{q['context']}*\n"
            
            response += "\n"
        
        response += "📝 **Responda com detalhes ou números das opções para prosseguir.**"
        
        return response
    
    async def process_clarification_response(self, user_response: str, original_request: str) -> Dict[str, Any]:
        """Processa resposta do usuário e combina com requisito original"""
        
        # Usar LLM para combinar requisito original + clarificações
        combine_prompt = f"""
Combine o requisito original com as clarificações do usuário em um requisito completo e específico.

REQUISITO ORIGINAL: {original_request}
CLARIFICAÇÕES: {user_response}

TAREFA: Criar um requisito único, completo e específico que pode ser usado para gerar templates AWS.

FORMATO: Retorne apenas o requisito combinado, claro e técnico.
"""
        
        try:
            combined_requirement = await self.llm_provider.process_natural_language_async(combine_prompt)
            
            return {
                'status': 'clarified',
                'combined_requirement': combined_requirement,
                'ready_to_generate': True
            }
            
        except Exception as e:
            print(f"⚠️ Erro ao combinar requisitos: {e}")
            # Fallback simples
            return {
                'status': 'clarified',
                'combined_requirement': f"{original_request}. Detalhes adicionais: {user_response}",
                'ready_to_generate': True
            }
