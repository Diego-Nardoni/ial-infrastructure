"""
Conversational Clarification Engine
Detecta requisitos ambíguos e faz perguntas de clarificação antes da geração de templates
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ClarificationQuestion:
    question: str
    options: List[str]
    required: bool = True
    context: str = ""

@dataclass
class RequirementAnalysis:
    service_type: str
    ambiguities: List[str]
    questions: List[ClarificationQuestion]
    confidence: float
    ready_to_generate: bool = False

class ConversationalClarificationEngine:
    def __init__(self):
        self.clarification_rules = {
            'database': {
                'keywords': ['database', 'db', 'banco', 'dados', 'storage', 'persistir'],
                'questions': [
                    ClarificationQuestion(
                        question="Você prefere RDS (relacional) ou DynamoDB (NoSQL)?",
                        options=["RDS", "DynamoDB", "Ambos para comparar"],
                        context="RDS é melhor para dados relacionais complexos, DynamoDB para alta performance e escalabilidade"
                    ),
                    ClarificationQuestion(
                        question="Qual é o volume esperado de dados?",
                        options=["< 100GB", "100GB - 1TB", "> 1TB", "Não sei ainda"],
                        context="Isso afeta o tipo de instância e configurações de storage"
                    ),
                    ClarificationQuestion(
                        question="Precisa de alta disponibilidade (Multi-AZ)?",
                        options=["Sim, crítico", "Não, desenvolvimento", "Talvez, produção"],
                        context="Multi-AZ aumenta disponibilidade mas dobra o custo"
                    ),
                    ClarificationQuestion(
                        question="A API será chamada de fora da VPC?",
                        options=["Sim, internet pública", "Não, apenas interno", "Ambos"],
                        context="Isso afeta configurações de security groups e subnets"
                    )
                ]
            },
            'api': {
                'keywords': ['api', 'endpoint', 'rest', 'graphql', 'lambda', 'gateway'],
                'questions': [
                    ClarificationQuestion(
                        question="Que tipo de API você quer criar?",
                        options=["REST API", "GraphQL", "WebSocket", "Não sei"],
                        context="Cada tipo tem diferentes configurações no API Gateway"
                    ),
                    ClarificationQuestion(
                        question="Qual será o volume de requisições?",
                        options=["< 1000/dia", "1000-100k/dia", "> 100k/dia"],
                        context="Isso afeta throttling, caching e pricing"
                    ),
                    ClarificationQuestion(
                        question="Precisa de autenticação?",
                        options=["Sim, JWT", "Sim, API Key", "Não", "OAuth"],
                        context="Define configurações de authorizers no API Gateway"
                    )
                ]
            },
            'storage': {
                'keywords': ['storage', 'bucket', 's3', 'arquivo', 'file', 'upload'],
                'questions': [
                    ClarificationQuestion(
                        question="Que tipo de arquivos você vai armazenar?",
                        options=["Documentos", "Imagens/Vídeos", "Logs", "Backups"],
                        context="Diferentes tipos precisam de diferentes lifecycle policies"
                    ),
                    ClarificationQuestion(
                        question="Os arquivos são públicos ou privados?",
                        options=["Públicos", "Privados", "Mistos"],
                        context="Isso afeta configurações de bucket policy e ACLs"
                    )
                ]
            }
        }
        
        self.session_context = {}  # Armazena contexto de conversas ativas
    
    def analyze_requirements(self, user_input: str, session_id: str = "default") -> RequirementAnalysis:
        """Analisa requisitos e identifica ambiguidades"""
        user_input_lower = user_input.lower()
        
        # Detectar tipo de serviço principal
        detected_services = []
        for service_type, config in self.clarification_rules.items():
            if any(keyword in user_input_lower for keyword in config['keywords']):
                detected_services.append(service_type)
        
        if not detected_services:
            return RequirementAnalysis(
                service_type="unknown",
                ambiguities=["Não foi possível identificar o tipo de serviço"],
                questions=[],
                confidence=0.0
            )
        
        # Usar o primeiro serviço detectado (pode ser melhorado)
        primary_service = detected_services[0]
        config = self.clarification_rules[primary_service]
        
        # Analisar ambiguidades
        ambiguities = self._detect_ambiguities(user_input, primary_service)
        
        # Gerar perguntas baseadas nas ambiguidades
        questions = self._generate_questions(primary_service, ambiguities, user_input)
        
        confidence = self._calculate_confidence(user_input, primary_service)
        
        return RequirementAnalysis(
            service_type=primary_service,
            ambiguities=ambiguities,
            questions=questions,
            confidence=confidence,
            ready_to_generate=(confidence > 0.8 and len(questions) == 0)
        )
    
    def _detect_ambiguities(self, user_input: str, service_type: str) -> List[str]:
        """Detecta ambiguidades específicas no input"""
        ambiguities = []
        user_input_lower = user_input.lower()
        
        if service_type == 'database':
            if not any(db_type in user_input_lower for db_type in ['rds', 'dynamodb', 'relacional', 'nosql']):
                ambiguities.append("Tipo de banco não especificado")
            
            if not any(size in user_input_lower for size in ['pequeno', 'médio', 'grande', 'gb', 'tb']):
                ambiguities.append("Volume de dados não especificado")
            
            if 'latência' in user_input_lower or 'performance' in user_input_lower:
                if not any(ha in user_input_lower for ha in ['multi-az', 'disponibilidade', 'ha']):
                    ambiguities.append("Requisitos de alta disponibilidade não claros")
        
        elif service_type == 'api':
            if not any(api_type in user_input_lower for api_type in ['rest', 'graphql', 'websocket']):
                ambiguities.append("Tipo de API não especificado")
        
        return ambiguities
    
    def _generate_questions(self, service_type: str, ambiguities: List[str], user_input: str) -> List[ClarificationQuestion]:
        """Gera perguntas baseadas nas ambiguidades detectadas"""
        config = self.clarification_rules[service_type]
        questions = []
        
        # Para database, sempre fazer perguntas principais se houver ambiguidades
        if service_type == 'database' and ambiguities:
            questions = config['questions'][:3]  # Primeiras 3 perguntas mais importantes
        
        elif service_type == 'api' and ambiguities:
            questions = config['questions'][:2]  # Primeiras 2 perguntas
        
        elif service_type == 'storage' and ambiguities:
            questions = config['questions']
        
        return questions
    
    def _calculate_confidence(self, user_input: str, service_type: str) -> float:
        """Calcula confiança baseada na especificidade do input"""
        user_input_lower = user_input.lower()
        confidence = 0.5  # Base confidence
        
        # Aumenta confiança para inputs mais específicos
        specific_terms = {
            'database': ['rds', 'dynamodb', 'mysql', 'postgres', 'nosql', 'relacional'],
            'api': ['rest', 'graphql', 'lambda', 'api gateway'],
            'storage': ['s3', 'bucket', 'efs', 'fsx']
        }
        
        if service_type in specific_terms:
            matches = sum(1 for term in specific_terms[service_type] if term in user_input_lower)
            confidence += matches * 0.2
        
        return min(confidence, 1.0)
    
    def format_clarification_response(self, analysis: RequirementAnalysis) -> str:
        """Formata resposta com perguntas de clarificação"""
        if analysis.ready_to_generate:
            return f"✅ Requisitos claros! Gerando templates para {analysis.service_type}..."
        
        response = f"🤔 **Preciso de mais informações sobre seu {analysis.service_type}:**\n\n"
        
        for i, question in enumerate(analysis.questions, 1):
            response += f"**{i}. {question.question}**\n"
            for j, option in enumerate(question.options, 1):
                response += f"   {j}) {option}\n"
            if question.context:
                response += f"   💡 *{question.context}*\n"
            response += "\n"
        
        response += "📝 **Responda com os números das opções (ex: 1, 2, 1) ou descreva suas preferências.**"
        
        return response
    
    def process_clarification_response(self, user_response: str, session_id: str = "default") -> Dict[str, Any]:
        """Processa resposta do usuário às perguntas de clarificação"""
        # Implementação simplificada - pode ser expandida
        return {
            'status': 'clarified',
            'ready_to_generate': True,
            'refined_requirements': user_response
        }
