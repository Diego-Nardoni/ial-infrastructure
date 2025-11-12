#!/usr/bin/env python3
"""
IAL Master Engine Complete - Engine unificado Query + Provisioning + Observabilidade
Interface conversacional completa igual Amazon Q com todas as capacidades
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

class IALMasterEngineComplete:
    """Engine completo: Query + Provisioning + Conversational + Observability"""
    
    def __init__(self):
        # Engines especializados
        self.query_engine = self._initialize_query_engine()
        self.conversational_engine = self._initialize_conversational_engine()
        self.cloudwatch_analyzer = self._initialize_cloudwatch_analyzer()
        self.security_analyzer = self._initialize_security_analyzer()
        self.response_formatter = self._initialize_response_formatter()
        
        # Orquestradores (fallback chain)
        self.stepfunctions_orchestrator = self._initialize_stepfunctions_orchestrator()
        self.mcp_first_orchestrator = self._initialize_mcp_first_orchestrator()
        self.python_orchestrator = self._initialize_python_orchestrator()
        
        # Contexto de conversa
        self.conversation_context = self._initialize_conversation_context()
        
        # Capacidades ativas
        self.capabilities = {
            'query': True,
            'provisioning': True,
            'observability': True,
            'security': True,
            'troubleshooting': True,
            'cost_optimization': True
        }
    
    def _initialize_query_engine(self):
        """Inicializar Query Engine"""
        try:
            from .ial_query_engine import QueryEngineIntegration
            return QueryEngineIntegration()
        except ImportError:
            print("⚠️ Query Engine não encontrado, usando simulação")
            return None
    
    def _initialize_conversational_engine(self):
        """Inicializar Conversational Engine"""
        try:
            from .ial_conversational_engine import IALConversationalEngine
            return IALConversationalEngine()
        except ImportError:
            print("⚠️ Conversational Engine não encontrado")
            return None
    
    def _initialize_cloudwatch_analyzer(self):
        """Inicializar CloudWatch Analyzer"""
        try:
            from .cloudwatch_analyzer import CloudWatchIntegration
            return CloudWatchIntegration()
        except ImportError:
            print("⚠️ CloudWatch Analyzer não encontrado")
            return None
    
    def _initialize_security_analyzer(self):
        """Inicializar Security Analyzer"""
        try:
            from .security_analyzer import SecurityIntegration
            return SecurityIntegration()
        except ImportError:
            print("⚠️ Security Analyzer não encontrado")
            return None
    
    def _initialize_response_formatter(self):
        """Inicializar Response Formatter"""
        try:
            from .response_formatter import ResponseFormatterIntegration
            return ResponseFormatterIntegration()
        except ImportError:
            print("⚠️ Response Formatter não encontrado")
            return None
    
    def _initialize_stepfunctions_orchestrator(self):
        """Inicializar Step Functions Orchestrator"""
        try:
            from .ial_orchestrator_stepfunctions import IALOrchestratorStepFunctions
            return IALOrchestratorStepFunctions()
        except ImportError:
            return None
    
    def _initialize_mcp_first_orchestrator(self):
        """Inicializar MCP-First Orchestrator"""
        try:
            from .ial_orchestrator_mcp_first import IALOrchestratorMCPFirst
            return IALOrchestratorMCPFirst()
        except ImportError:
            return None
    
    def _initialize_python_orchestrator(self):
        """Inicializar Python Orchestrator"""
        try:
            from .ial_orchestrator import IALOrchestrator
            return IALOrchestrator()
        except ImportError:
            return None
    
    def _initialize_conversation_context(self):
        """Inicializar contexto de conversa"""
        try:
            from .ial_conversational_engine import ConversationContext
            return ConversationContext()
        except ImportError:
            return None
    
    async def process_user_input(self, user_input: str) -> str:
        """Interface principal - processar input do usuário (igual Amazon Q)"""
        
        # 1. Manter contexto da conversa
        if self.conversation_context:
            self.conversation_context.add_user_input(user_input)
        
        # 2. Classificar intenção avançada
        intent_classification = await self._classify_advanced_intent(user_input)
        
        # 3. Processar baseado na intenção
        try:
            if intent_classification["type"] == "query":
                result = await self._process_query_intent(user_input, intent_classification)
            elif intent_classification["type"] == "provisioning":
                result = await self._process_provisioning_intent(user_input, intent_classification)
            elif intent_classification["type"] == "observability":
                result = await self._process_observability_intent(user_input, intent_classification)
            elif intent_classification["type"] == "security":
                result = await self._process_security_intent(user_input, intent_classification)
            elif intent_classification["type"] == "troubleshooting":
                result = await self._process_troubleshooting_intent(user_input, intent_classification)
            elif intent_classification["type"] == "cost_optimization":
                result = await self._process_cost_optimization_intent(user_input, intent_classification)
            else:
                result = await self._process_help_intent(user_input)
            
            # 4. Formatar resposta estilo Amazon Q
            formatted_response = self._format_amazon_q_response(result, intent_classification)
            
            # 5. Adicionar sugestões contextuais
            formatted_response += self._generate_contextual_suggestions(user_input, intent_classification, result)
            
            # 6. Salvar no contexto
            if self.conversation_context:
                self.conversation_context.add_response(formatted_response)
            
            return formatted_response
            
        except Exception as e:
            error_response = f"❌ **Erro interno:** {str(e)}\n\n💡 **Tente:** Reformular a pergunta ou usar comandos mais específicos."
            return error_response
    
    async def _classify_advanced_intent(self, user_input: str) -> Dict:
        """Classificação avançada de intenções"""
        
        user_lower = user_input.lower()
        
        # Padrões de intenção mais específicos
        intent_patterns = {
            "query": {
                "keywords": ["liste", "quantos", "quantas", "mostrar", "ver", "status", "describe"],
                "confidence": 0.0
            },
            "provisioning": {
                "keywords": ["criar", "quero", "preciso", "deploy", "provisionar", "create", "setup"],
                "confidence": 0.0
            },
            "observability": {
                "keywords": ["performance", "métricas", "cpu", "memória", "disk", "monitor", "logs", "análise"],
                "confidence": 0.0
            },
            "security": {
                "keywords": ["segurança", "login", "brute force", "ameaça", "cloudtrail", "audit", "security"],
                "confidence": 0.0
            },
            "troubleshooting": {
                "keywords": ["problema", "erro", "lento", "falha", "debug", "não funciona", "issue"],
                "confidence": 0.0
            },
            "cost_optimization": {
                "keywords": ["custo", "cost", "economia", "otimizar", "billing", "price", "savings"],
                "confidence": 0.0
            }
        }
        
        # Calcular confiança para cada intenção
        for intent_type, pattern in intent_patterns.items():
            matches = sum(1 for keyword in pattern["keywords"] if keyword in user_lower)
            pattern["confidence"] = matches / len(pattern["keywords"])
        
        # Encontrar intenção com maior confiança
        best_intent = max(intent_patterns.items(), key=lambda x: x[1]["confidence"])
        
        # Se confiança muito baixa, classificar como help
        if best_intent[1]["confidence"] < 0.1:
            return {"type": "help", "confidence": 0.0, "subtype": "general"}
        
        # Detectar subtipo baseado em contexto
        subtype = self._detect_intent_subtype(user_lower, best_intent[0])
        
        return {
            "type": best_intent[0],
            "confidence": best_intent[1]["confidence"],
            "subtype": subtype,
            "original_input": user_input
        }
    
    def _detect_intent_subtype(self, user_lower: str, intent_type: str) -> str:
        """Detectar subtipo da intenção"""
        
        if intent_type == "query":
            if any(keyword in user_lower for keyword in ["bucket", "s3"]):
                return "s3_query"
            elif any(keyword in user_lower for keyword in ["ec2", "instance"]):
                return "ec2_query"
            elif any(keyword in user_lower for keyword in ["cost", "custo"]):
                return "cost_query"
            else:
                return "general_query"
        
        elif intent_type == "observability":
            if any(keyword in user_lower for keyword in ["cpu", "memory", "performance"]):
                return "performance_analysis"
            elif any(keyword in user_lower for keyword in ["logs", "error", "exception"]):
                return "log_analysis"
            else:
                return "general_monitoring"
        
        elif intent_type == "security":
            if any(keyword in user_lower for keyword in ["login", "brute force"]):
                return "login_security"
            elif any(keyword in user_lower for keyword in ["privilege", "iam"]):
                return "privilege_analysis"
            else:
                return "general_security"
        
        return "general"
    
    async def _process_query_intent(self, user_input: str, intent: Dict) -> Dict:
        """Processar intenção de query"""
        
        if self.query_engine:
            if hasattr(self.query_engine, 'process_query_sync'):
                return self.query_engine.process_query_sync(user_input)
            else:
                return await self.query_engine.process_query_async(user_input)
        else:
            return {"type": "error", "message": "Query engine não disponível"}
    
    async def _process_provisioning_intent(self, user_input: str, intent: Dict) -> Dict:
        """Processar intenção de provisioning"""
        
        # Usar cadeia de fallback para provisioning
        try:
            # 1. TENTAR Step Functions primeiro
            if self.stepfunctions_orchestrator:
                result = await self._execute_async_orchestrator(
                    self.stepfunctions_orchestrator, user_input
                )
                if result.get("status") != "error":
                    return result
        except Exception as e:
            print(f"⚠️ Step Functions falhou: {e}")
        
        try:
            # 2. TENTAR MCP-first
            if self.mcp_first_orchestrator:
                result = await self._execute_async_orchestrator(
                    self.mcp_first_orchestrator, user_input
                )
                if result.get("status") != "error":
                    return result
        except Exception as e:
            print(f"⚠️ MCP-first falhou: {e}")
        
        try:
            # 3. FALLBACK Python
            if self.python_orchestrator:
                result = await self._execute_async_orchestrator(
                    self.python_orchestrator, user_input
                )
                return result
        except Exception as e:
            print(f"⚠️ Python orchestrator falhou: {e}")
        
        return {
            "type": "provisioning_error",
            "message": "Todos os orquestradores de provisioning falharam",
            "status": "error"
        }
    
    async def _process_observability_intent(self, user_input: str, intent: Dict) -> Dict:
        """Processar intenção de observabilidade"""
        
        if self.cloudwatch_analyzer:
            return await self.cloudwatch_analyzer.process_monitoring_query(user_input)
        else:
            return {"type": "error", "message": "CloudWatch analyzer não disponível"}
    
    async def _process_security_intent(self, user_input: str, intent: Dict) -> Dict:
        """Processar intenção de segurança"""
        
        if self.security_analyzer:
            return await self.security_analyzer.process_security_query(user_input)
        else:
            return {"type": "error", "message": "Security analyzer não disponível"}
    
    async def _process_troubleshooting_intent(self, user_input: str, intent: Dict) -> Dict:
        """Processar intenção de troubleshooting"""
        
        # Troubleshooting combina observabilidade + query
        if "lento" in user_input.lower() or "performance" in user_input.lower():
            if self.cloudwatch_analyzer:
                return await self.cloudwatch_analyzer.process_monitoring_query(user_input)
        
        elif "erro" in user_input.lower() or "falha" in user_input.lower():
            if self.cloudwatch_analyzer:
                return await self.cloudwatch_analyzer.process_monitoring_query("logs error")
        
        # Fallback para query geral
        return await self._process_query_intent(user_input, intent)
    
    async def _process_cost_optimization_intent(self, user_input: str, intent: Dict) -> Dict:
        """Processar intenção de otimização de custos"""
        
        if self.cloudwatch_analyzer:
            return await self.cloudwatch_analyzer.process_monitoring_query("cost anomaly")
        else:
            return await self._process_query_intent(user_input, intent)
    
    async def _process_help_intent(self, user_input: str) -> Dict:
        """Processar intenção de ajuda"""
        
        return {
            "type": "help",
            "message": "IAL Assistant - Como posso ajudar?",
            "capabilities": self.capabilities,
            "examples": {
                "query": ["liste todos os buckets", "quantas EC2 eu tenho", "qual o custo atual"],
                "provisioning": ["quero ECS com Redis", "criar VPC privada", "deploy serverless"],
                "observability": ["análise de performance", "verificar logs de erro", "métricas CPU"],
                "security": ["análise de login", "verificar ameaças", "audit cloudtrail"],
                "troubleshooting": ["por que está lento?", "debug aplicação", "problema de conexão"],
                "cost_optimization": ["como reduzir custos?", "otimizar recursos", "anomalias de custo"]
            }
        }
    
    async def _execute_async_orchestrator(self, orchestrator, user_input: str) -> Dict:
        """Executar orquestrador de forma assíncrona"""
        
        # Se o orquestrador tem método assíncrono, usar
        if hasattr(orchestrator, 'process_nl_intent_async'):
            return await orchestrator.process_nl_intent_async(user_input)
        # Senão, executar de forma síncrona
        elif hasattr(orchestrator, 'process_nl_intent'):
            return orchestrator.process_nl_intent(user_input)
        else:
            return {"status": "error", "message": "Orquestrador não implementado"}
    
    def _format_amazon_q_response(self, result: Dict, intent: Dict) -> str:
        """Formatar resposta no estilo Amazon Q"""
        
        if self.response_formatter:
            return self.response_formatter.format_response(result)
        else:
            # Formatação simples de fallback
            return self._format_simple_response(result, intent)
    
    def _format_simple_response(self, result: Dict, intent: Dict) -> str:
        """Formatação simples (fallback)"""
        
        result_type = result.get("type", "unknown")
        
        if result_type == "help":
            return f"""🤖 **IAL Assistant - Como posso ajudar?**

**📊 Consultas:**
• liste todos os buckets
• quantas EC2 eu tenho  
• qual o custo atual

**🚀 Provisioning:**
• quero ECS com Redis
• criar VPC privada
• deploy serverless

**📈 Observabilidade:**
• análise de performance
• verificar logs de erro
• métricas CPU

**🛡️ Segurança:**
• análise de login
• verificar ameaças
• audit cloudtrail

Digite sua pergunta!"""
        
        elif result_type == "error":
            return f"❌ **Erro:** {result.get('message', 'Erro desconhecido')}"
        
        else:
            return f"📊 **Resultado:** {result.get('message', 'Processado com sucesso')}"
    
    def _generate_contextual_suggestions(self, user_input: str, intent: Dict, result: Dict) -> str:
        """Gerar sugestões contextuais inteligentes"""
        
        if self.response_formatter:
            return self.response_formatter.format_contextual_suggestions(user_input, intent["type"])
        else:
            # Sugestões simples de fallback
            return self._generate_simple_suggestions(intent["type"])
    
    def _generate_simple_suggestions(self, intent_type: str) -> str:
        """Gerar sugestões simples (fallback)"""
        
        suggestions_map = {
            "query": [
                "• Quer ver detalhes de um recurso específico?",
                "• Precisa de análise de custos?",
                "• Quer configurar monitoramento?"
            ],
            "provisioning": [
                "• Quer acompanhar o progresso?",
                "• Precisa ajustar configurações?",
                "• Quer configurar alertas?"
            ],
            "observability": [
                "• Quer configurar alertas automáticos?",
                "• Precisa de análise histórica?",
                "• Quer otimizar performance?"
            ],
            "security": [
                "• Quer implementar as recomendações?",
                "• Precisa de relatório detalhado?",
                "• Quer configurar alertas de segurança?"
            ]
        }
        
        suggestions = suggestions_map.get(intent_type, ["• Como posso ajudar mais?"])
        return f"\n\n💡 **Sugestões:**\n" + "\n".join(suggestions)
    
    def get_capabilities_status(self) -> Dict:
        """Obter status das capacidades do sistema"""
        
        return {
            "capabilities": self.capabilities,
            "engines_status": {
                "query_engine": self.query_engine is not None,
                "conversational_engine": self.conversational_engine is not None,
                "cloudwatch_analyzer": self.cloudwatch_analyzer is not None,
                "security_analyzer": self.security_analyzer is not None,
                "response_formatter": self.response_formatter is not None
            },
            "orchestrators_status": {
                "stepfunctions": self.stepfunctions_orchestrator is not None,
                "mcp_first": self.mcp_first_orchestrator is not None,
                "python": self.python_orchestrator is not None
            },
            "conversation_context": self.conversation_context is not None
        }

# Interface CLI para testes
class IALMasterCLI:
    """Interface CLI para o Master Engine"""
    
    def __init__(self):
        self.engine = IALMasterEngineComplete()
    
    async def run_interactive_mode(self):
        """Executar modo interativo"""
        
        print("🤖 IAL Master Engine - Modo Interativo")
        print("Digite 'quit' para sair, 'status' para ver capacidades\n")
        
        # Mostrar status inicial
        status = self.engine.get_capabilities_status()
        active_engines = sum(1 for engine in status["engines_status"].values() if engine)
        print(f"✅ {active_engines}/5 engines ativos")
        
        while True:
            try:
                user_input = input("IAL> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'sair']:
                    print("👋 Até logo!")
                    break
                
                if user_input.lower() == 'status':
                    self._show_status()
                    continue
                
                if user_input:
                    response = await self.engine.process_user_input(user_input)
                    print(f"\n{response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def _show_status(self):
        """Mostrar status do sistema"""
        
        status = self.engine.get_capabilities_status()
        
        print("\n📊 **Status do Sistema:**")
        print(f"• Query Engine: {'✅' if status['engines_status']['query_engine'] else '❌'}")
        print(f"• Conversational Engine: {'✅' if status['engines_status']['conversational_engine'] else '❌'}")
        print(f"• CloudWatch Analyzer: {'✅' if status['engines_status']['cloudwatch_analyzer'] else '❌'}")
        print(f"• Security Analyzer: {'✅' if status['engines_status']['security_analyzer'] else '❌'}")
        print(f"• Response Formatter: {'✅' if status['engines_status']['response_formatter'] else '❌'}")
        
        print(f"\n🔄 **Orquestradores:**")
        print(f"• Step Functions: {'✅' if status['orchestrators_status']['stepfunctions'] else '❌'}")
        print(f"• MCP-First: {'✅' if status['orchestrators_status']['mcp_first'] else '❌'}")
        print(f"• Python: {'✅' if status['orchestrators_status']['python'] else '❌'}")

# Função principal
async def main():
    """Função principal"""
    cli = IALMasterCLI()
    await cli.run_interactive_mode()

if __name__ == "__main__":
    asyncio.run(main())
