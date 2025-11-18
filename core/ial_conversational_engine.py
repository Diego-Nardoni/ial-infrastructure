#!/usr/bin/env python3
"""
IAL Conversational Engine - Interface conversacional igual Amazon Q
Implementa capacidades de Query + Provisioning com contexto de conversa
"""

import json
from typing import Dict, List, Optional
from datetime import datetime

class ConversationContext:
    """Gerencia contexto e memória da conversa"""
    
    def __init__(self):
        self.history = []
        self.current_session = {
            'start_time': datetime.now(),
            'user_inputs': [],
            'responses': [],
            'context_data': {}
        }
        # Inicializar Context Engine (já tem MemoryManager + Embeddings)
        try:
            from .memory.context_engine import ContextEngine
            self.context_engine = ContextEngine()
            self.memory_manager = self.context_engine.memory
        except Exception as e:
            self.context_engine = None
            self.memory_manager = None
    
    def add_user_input(self, user_input: str):
        """Adiciona input do usuário ao contexto"""
        self.current_session['user_inputs'].append({
            'timestamp': datetime.now(),
            'input': user_input
        })
    
    def add_response(self, response: str):
        """Adiciona resposta ao contexto"""
        self.current_session['responses'].append({
            'timestamp': datetime.now(),
            'response': response
        })
    
    def get_recent_context(self, limit: int = 3) -> List[Dict]:
        """Retorna contexto recente da conversa"""
        return self.current_session['user_inputs'][-limit:]

class QueryEngine:
    """Engine para consultas AWS via MCP servers - Wrapper para IALQueryEngine"""
    
    def __init__(self):
        # Usar o engine real implementado
        try:
            from .ial_query_engine import QueryEngineIntegration
            self.real_engine = QueryEngineIntegration()
            self.use_real_engine = True
        except ImportError:
            print("⚠️ IALQueryEngine não encontrado, usando simulação")
            self.use_real_engine = False
            self.mcp_clients = {
                'aws_resources': 'mcp-aws-resources',
                'cost_explorer': 'mcp-cost-explorer', 
                'cloudwatch': 'mcp-cloudwatch',
                'cloudtrail': 'mcp-cloudtrail'
            }
    
    def process_via_mcp(self, query: str) -> Dict:
        """Processar queries via MCP servers"""
        
        if self.use_real_engine:
            # Usar engine real com MCP servers
            return self.real_engine.process_query_sync(query)
        else:
            # Fallback para simulação
            return self._process_simulated_query(query)
    
    def _process_simulated_query(self, query: str) -> Dict:
        """Processar query simulada (fallback)"""
        query_lower = query.lower()
        
        if 'bucket' in query_lower or 's3' in query_lower:
            return self._query_s3_buckets()
        elif 'ec2' in query_lower or 'instanc' in query_lower:
            return self._query_ec2_instances()
        elif 'cloudtrail' in query_lower or 'log' in query_lower:
            return self._query_cloudtrail_logs(query)
        elif 'custo' in query_lower or 'cost' in query_lower:
            return self._query_current_costs()
        elif 'cloudwatch' in query_lower or 'metric' in query_lower:
            return self._query_cloudwatch_metrics(query)
        else:
            return self._query_general_resources(query)
    
    def _query_s3_buckets(self) -> Dict:
        """Liste buckets S3 via MCP"""
        # Simulação - seria chamada MCP real
        return {
            'type': 's3_buckets',
            'total': 6,
            'buckets': [
                {'name': 'ial-terraform-state', 'region': 'us-east-1', 'size': '2.1GB', 'cost': '$0.05'},
                {'name': 'ial-artifacts-prod', 'region': 'us-east-1', 'size': '15.3GB', 'cost': '$0.35'},
                {'name': 'ial-logs-backup', 'region': 'us-east-1', 'size': '45.2GB', 'cost': '$1.04'},
                {'name': 'ial-data-lake', 'region': 'us-east-1', 'size': '128.7GB', 'cost': '$2.96'},
                {'name': 'ial-static-assets', 'region': 'us-east-1', 'size': '8.9GB', 'cost': '$0.20'},
                {'name': 'ial-backup-cross-region', 'region': 'us-west-2', 'size': '67.4GB', 'cost': '$1.55'}
            ],
            'total_cost': '$6.15'
        }
    
    def _query_ec2_instances(self) -> Dict:
        """Liste instâncias EC2 via MCP"""
        return {
            'type': 'ec2_instances',
            'total': 8,
            'prod_count': 4,
            'staging_count': 4,
            'production': [
                {'id': 'i-0123456789abcdef0', 'type': 't3.large', 'state': 'running', 'cost': '$61.32'},
                {'id': 'i-0987654321fedcba0', 'type': 't3.medium', 'state': 'running', 'cost': '$30.66'},
                {'id': 'i-0abcdef123456789', 'type': 't3.large', 'state': 'running', 'cost': '$61.32'},
                {'id': 'i-0fedcba987654321', 'type': 't3.small', 'state': 'running', 'cost': '$15.33'}
            ],
            'staging': [
                {'id': 'i-0111222333444555', 'type': 't3.micro', 'state': 'running', 'cost': '$7.67'},
                {'id': 'i-0555444333222111', 'type': 't3.micro', 'state': 'stopped', 'cost': '$0.00'},
                {'id': 'i-0666777888999000', 'type': 't3.small', 'state': 'running', 'cost': '$15.33'},
                {'id': 'i-0000999888777666', 'type': 't3.micro', 'state': 'running', 'cost': '$7.67'}
            ],
            'total_cost': '$199.30',
            'alerts': ['dev-sandbox idle há 3 dias', 'staging-02 stopped mas com EBS attached']
        }
    
    def _query_cloudtrail_logs(self, query: str) -> Dict:
        """Logs CloudTrail via MCP"""
        if 'login' in query.lower():
            return {
                'type': 'cloudtrail_security',
                'event_type': 'failed_logins',
                'threats_detected': 23,
                'suspicious_ips': ['1.2.3.4', '5.6.7.8'],
                'affected_users': ['admin@company.com', 'root'],
                'time_window': '24 hours',
                'security_score': 65,
                'immediate_actions': [
                    'Bloquear IP 1.2.3.4 no Security Group',
                    'Resetar senha do usuário admin@company',
                    'Habilitar MFA se não estiver ativo'
                ]
            }
        return {'type': 'cloudtrail_general', 'events': []}
    
    def _query_current_costs(self) -> Dict:
        """Custos atuais via MCP Cost Explorer"""
        return {
            'type': 'cost_analysis',
            'current_month': '$245.67',
            'last_month': '$198.43',
            'trend': 'increasing',
            'top_services': [
                {'service': 'EC2', 'cost': '$199.30', 'percentage': 81.1},
                {'service': 'S3', 'cost': '$6.15', 'percentage': 2.5},
                {'service': 'CloudWatch', 'cost': '$12.45', 'percentage': 5.1},
                {'service': 'VPC', 'cost': '$8.90', 'percentage': 3.6},
                {'service': 'Others', 'cost': '$18.87', 'percentage': 7.7}
            ],
            'optimization_opportunities': [
                {'type': 'rightsizing', 'potential_savings': '$45.20', 'description': 'Reserved Instances para prod'},
                {'type': 'storage', 'potential_savings': '$12.50', 'description': 'S3 objects elegíveis para IA'},
                {'type': 'idle_resources', 'potential_savings': '$15.18', 'description': 'dev-sandbox idle há 3 dias'}
            ]
        }
    
    def _query_cloudwatch_metrics(self, query: str) -> Dict:
        """Métricas CloudWatch via MCP"""
        return {
            'type': 'cloudwatch_metrics',
            'metric_type': 'cpu_utilization',
            'instances': [
                {'id': 'i-0123456789abcdef0', 'avg_cpu': 85.2, 'status': 'high'},
                {'id': 'i-0987654321fedcba0', 'avg_cpu': 45.1, 'status': 'normal'},
                {'id': 'i-0abcdef123456789', 'avg_cpu': 12.3, 'status': 'low'}
            ],
            'recommendations': ['Scale up prod-web-01 para t3.large', 'Adicionar auto-scaling group']
        }
    
    def _query_general_resources(self, query: str) -> Dict:
        """Query geral de recursos"""
        return {
            'type': 'general_query',
            'message': f'Processando query: {query}',
            'suggestions': ['Seja mais específico sobre o recurso', 'Tente: "liste buckets" ou "quantas EC2"']
        }

class IALConversationalEngine:
    """Engine conversacional principal - Interface igual Amazon Q"""
    
    def __init__(self):
        self.query_engine = QueryEngine()
        self.conversation_context = ConversationContext()
        
        # Inicializar context_engine
        self.context_engine = None
        try:
            from .memory.context_engine import ContextEngine
            self.context_engine = ContextEngine()
        except ImportError:
            pass
        
        # Importar engines existentes (fallback)
        try:
            from .ial_orchestrator_stepfunctions import IALOrchestratorStepFunctions
            from .ial_orchestrator_mcp_first import IALOrchestratorMCPFirst
            from .ial_orchestrator import IALOrchestrator
            
            self.stepfunctions_orchestrator = IALOrchestratorStepFunctions()
            self.mcp_first_orchestrator = IALOrchestratorMCPFirst()
            self.python_orchestrator = IALOrchestrator()
        except ImportError:
            self.stepfunctions_orchestrator = None
            self.mcp_first_orchestrator = None
            self.python_orchestrator = None
    
    def process_conversational_input(self, user_input: str) -> str:
        """Interface conversacional principal"""
        
        # 1. Construir contexto semântico relevante (SEMPRE)
        context = ""
        if self.context_engine:
            try:
                context = self.context_engine.build_context_for_query(user_input)
            except Exception as e:
                pass  # Silenciar
        
        # 2. Manter contexto da conversa local
        self.conversation_context.add_user_input(user_input)
        
        # 3. Preparar input enriquecido com contexto (LLM decide se usa)
        enriched_input = user_input
        if context:
            enriched_input = f"""Histórico de conversas anteriores:
{context}

---
Pergunta atual do usuário: {user_input}"""
        
        # 4. Detectar tipo de intenção
        intent_type = self._classify_intent(user_input)
        
        # 5. Processar baseado no tipo
        if intent_type == "query":
            result = self.query_engine.process_via_mcp(enriched_input)
            response = self._format_query_response(result)
            
        elif intent_type == "provisioning":
            if self._has_provisioning_engines():
                result = self._execute_provisioning_chain(enriched_input)
                response = self._format_provisioning_response(result)
            else:
                response = "🚧 Provisioning engines não disponíveis. Modo query-only ativo."
                
        elif intent_type == "troubleshooting":
            result = self.query_engine.process_via_mcp(enriched_input)
            response = self._format_troubleshooting_response(result)
        
        else:
            response = self._format_help_response()
        
        # 6. Adicionar sugestões contextuais
        response += self._generate_contextual_suggestions(user_input, intent_type)
        
        # 7. Salvar interação completa (user + assistant) com embeddings
        if self.context_engine:
            try:
                self.context_engine.save_interaction(user_input, response)
            except Exception:
                pass  # Silenciar
        
        # 8. Salvar no contexto local
        self.conversation_context.add_response(response)
        
        return response
    
    def _classify_intent(self, user_input: str) -> str:
        """Detectar tipo de intenção"""
        
        query_keywords = ['liste', 'quantos', 'quantas', 'verificar', 'logs', 'status', 'custo', 'cost', 'show', 'describe']
        provisioning_keywords = ['criar', 'quero', 'preciso', 'deploy', 'provisionar', 'create']
        troubleshooting_keywords = ['problema', 'erro', 'lento', 'falha', 'não funciona', 'debug']
        
        user_lower = user_input.lower()
        
        if any(keyword in user_lower for keyword in query_keywords):
            return "query"
        elif any(keyword in user_lower for keyword in provisioning_keywords):
            return "provisioning"
        elif any(keyword in user_lower for keyword in troubleshooting_keywords):
            return "troubleshooting"
        else:
            return "unknown"
    
    def _has_provisioning_engines(self) -> bool:
        """Verifica se engines de provisioning estão disponíveis"""
        return (self.stepfunctions_orchestrator is not None or 
                self.mcp_first_orchestrator is not None or 
                self.python_orchestrator is not None)
    
    def _execute_provisioning_chain(self, user_input: str) -> Dict:
        """Cadeia de fallback para provisioning"""
        
        try:
            # 1. TENTAR Step Functions primeiro
            if self.stepfunctions_orchestrator:
                return self.stepfunctions_orchestrator.process_nl_intent(user_input)
        except Exception as e:
            print(f"⚠️ Step Functions falhou: {e}")
            
            try:
                # 2. TENTAR MCP-first
                if self.mcp_first_orchestrator:
                    return self.mcp_first_orchestrator.process_nl_intent(user_input)
            except Exception as e:
                print(f"⚠️ MCP-first falhou: {e}")
                
                # 3. FALLBACK Python
                if self.python_orchestrator:
                    return self.python_orchestrator.process_nl_intent(user_input)
        
        return {"error": "Todos os orquestradores falharam", "status": "error"}
    
    def _format_query_response(self, result: Dict) -> str:
        """Formatar resposta de query igual Amazon Q"""
        
        # Usar formatter avançado se disponível
        try:
            from .response_formatter import ResponseFormatterIntegration
            formatter = ResponseFormatterIntegration()
            return formatter.format_response(result)
        except ImportError:
            # Fallback para formatação simples
            return self._format_simple_response(result)
    
    def _format_simple_response(self, result: Dict) -> str:
        """Formatação simples (fallback)"""
        if result['type'] == 's3_buckets':
            return self._format_s3_response(result)
        elif result['type'] == 'ec2_instances':
            return self._format_ec2_response(result)
        elif result['type'] == 'cloudtrail_security':
            return self._format_security_response(result)
        elif result['type'] == 'cost_analysis':
            return self._format_cost_response(result)
        elif result['type'] == 'cloudwatch_metrics':
            return self._format_metrics_response(result)
        else:
            return f"📊 **Resultado:** {result.get('message', 'Query processada')}"
    
    def _format_s3_response(self, result: Dict) -> str:
        """Formatar resposta S3 igual Amazon Q"""
        
        bucket_rows = ""
        for bucket in result['buckets']:
            bucket_rows += f"│ {bucket['name']:<19} │ {bucket['region']:<8} │ {bucket['size']:<7} │ {bucket['cost']:<12} │\n"
        
        return f"""📦 **Buckets S3 encontrados ({result['total']} total):**

┌─────────────────────┬──────────┬─────────┬──────────────┐
│ Nome                │ Região   │ Tamanho │ Custo/mês    │
├─────────────────────┼──────────┼─────────┼──────────────┤
{bucket_rows}└─────────────────────┴──────────┴─────────┴──────────────┘

💰 **Custo total:** {result['total_cost']}/mês"""
    
    def _format_ec2_response(self, result: Dict) -> str:
        """Formatar resposta EC2 igual Amazon Q"""
        
        prod_list = "\n".join([f"• {inst['id']} ({inst['type']}) - {inst['cost']}/mês" for inst in result['production']])
        staging_list = "\n".join([f"• {inst['id']} ({inst['type']}) - {inst['cost']}/mês" for inst in result['staging']])
        alerts_list = "\n".join([f"• {alert}" for alert in result['alerts']])
        
        return f"""🖥️ **Instâncias EC2 ativas ({result['total']} total):**

**🟢 Produção ({result['prod_count']} instâncias):**
{prod_list}

**🟡 Staging ({result['staging_count']} instâncias):**
{staging_list}

💰 **Custo total:** ${result['total_cost']}/mês

⚠️ **Alertas:**
{alerts_list}"""
    
    def _format_security_response(self, result: Dict) -> str:
        """Formatar análise de segurança igual Amazon Q"""
        
        actions_list = "\n".join([f"• {action}" for action in result['immediate_actions']])
        
        return f"""🚨 **Análise de Segurança CloudTrail:**

🛡️ **Security Score:** {result['security_score']}/100

**❌ Ameaças detectadas ({result['threats_detected']} eventos):**
• IPs suspeitos: {', '.join(result['suspicious_ips'])}
• Usuários afetados: {', '.join(result['affected_users'])}
• Janela de tempo: {result['time_window']}

🔍 **Análise de padrões:**
• IP 1.2.3.4: 15 tentativas em 2 minutos (possível brute force)
• Usuário admin@company: 23 falhas consecutivas
• Origem: Não reconhecida (fora da rede corporativa)

🛡️ **Ações imediatas recomendadas:**
{actions_list}"""
    
    def _format_cost_response(self, result: Dict) -> str:
        """Formatar análise de custos igual Amazon Q"""
        
        services_list = "\n".join([f"• {svc['service']}: ${svc['cost']} ({svc['percentage']}%)" for svc in result['top_services']])
        savings_list = "\n".join([f"• {opt['description']} → Economia: ${opt['potential_savings']}/mês" for opt in result['optimization_opportunities']])
        
        return f"""💰 **Análise de Custos AWS:**

📊 **Resumo atual:**
• Este mês: ${result['current_month']}
• Mês anterior: ${result['last_month']}
• Tendência: {result['trend']} 📈

**💸 Top serviços por custo:**
{services_list}

**🎯 Oportunidades de otimização:**
{savings_list}

**💡 Economia total potencial: ${sum(float(opt['potential_savings'].replace('$', '')) for opt in result['optimization_opportunities']):.2f}/mês**"""
    
    def _format_metrics_response(self, result: Dict) -> str:
        """Formatar métricas CloudWatch"""
        
        instances_list = "\n".join([f"• {inst['id']}: {inst['avg_cpu']}% CPU ({inst['status']})" for inst in result['instances']])
        recommendations_list = "\n".join([f"• {rec}" for rec in result['recommendations']])
        
        return f"""📊 **Métricas CloudWatch - CPU Utilization:**

**🖥️ Instâncias analisadas:**
{instances_list}

**💡 Recomendações:**
{recommendations_list}"""
    
    def _format_provisioning_response(self, result: Dict) -> str:
        """Formatar resposta de provisioning igual Amazon Q"""
        
        if result.get('status') == 'error':
            return f"❌ **Erro no provisioning:** {result.get('error', 'Erro desconhecido')}"
        
        return f"""🧠 **Interpretando sua intenção:**
• Serviço: {result.get('detected_services', 'N/A')}
• Configuração: {result.get('configuration', 'N/A')}
• Região: {result.get('region', 'us-east-1')}

✅ **Provisioning iniciado com sucesso!**

📬 **Próximos passos:**
• Gerando YAML files...
• Criando Pull Request no GitHub...
• Pipeline CI/CD será executado automaticamente"""
    
    def _format_troubleshooting_response(self, result: Dict) -> str:
        """Formatar resposta de troubleshooting"""
        
        if result['type'] == 'cloudwatch_metrics':
            return f"""🔍 **Análise de Performance:**

{self._format_metrics_response(result)}

🛠️ **Diagnóstico:**
• Problema identificado: CPU alta em algumas instâncias
• Impacto: Performance degradada da aplicação
• Solução recomendada: Scale up ou auto-scaling"""
        
        return "🔍 **Troubleshooting em andamento...** Analisando logs e métricas."
    
    def _format_help_response(self) -> str:
        """Resposta de ajuda"""
        
        return """🤖 **IAL Assistant - Como posso ajudar?**

**📊 Consultas (Query):**
• "liste todos os buckets"
• "quantas EC2 eu tenho"
• "verifique logs cloudtrail"
• "qual o custo atual"

**🚀 Provisioning:**
• "quero ECS com Redis"
• "criar VPC privada"
• "deploy aplicação serverless"

**🔍 Troubleshooting:**
• "por que está lento?"
• "problema de login"
• "debug performance"

Digite sua pergunta ou comando!"""
    
    def _generate_contextual_suggestions(self, user_input: str, intent_type: str) -> str:
        """Gerar sugestões contextuais baseadas na conversa"""
        
        # Usar formatter avançado se disponível
        try:
            from .response_formatter import ResponseFormatterIntegration
            formatter = ResponseFormatterIntegration()
            return formatter.format_contextual_suggestions(user_input, intent_type)
        except ImportError:
            # Fallback para sugestões simples
            return self._generate_simple_suggestions(user_input, intent_type)
    
    def _generate_simple_suggestions(self, user_input: str, intent_type: str) -> str:
        """Gerar sugestões simples (fallback)"""
        suggestions = []
        
        if intent_type == "query":
            if 'bucket' in user_input.lower():
                suggestions.extend([
                    "• Quer configurar lifecycle policies para otimizar custos?",
                    "• Precisa analisar padrões de acesso aos objetos?",
                    "• Quer configurar replicação cross-region?"
                ])
            elif 'ec2' in user_input.lower():
                suggestions.extend([
                    "• Quer analisar utilização de CPU/memória?",
                    "• Precisa configurar auto-scaling?",
                    "• Quer otimizar custos com Reserved Instances?"
                ])
            elif 'custo' in user_input.lower():
                suggestions.extend([
                    "• Quer implementar as otimizações sugeridas?",
                    "• Precisa configurar alertas de budget?",
                    "• Quer análise detalhada por projeto?"
                ])
        
        elif intent_type == "provisioning":
            suggestions.extend([
                "• Quer acompanhar o progresso do deploy?",
                "• Precisa ajustar alguma configuração?",
                "• Quer configurar monitoramento para os recursos?"
            ])
        
        if suggestions:
            return f"\n\n💡 **Sugestões:**\n" + "\n".join(suggestions)
        
        return ""

# Interface CLI para testes
if __name__ == "__main__":
    engine = IALConversationalEngine()
    
    print("🤖 IAL Conversational Engine - Modo Teste")
    print("Digite 'quit' para sair\n")
    
    while True:
        user_input = input("IAL> ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'sair']:
            print("👋 Até logo!")
            break
        
        if user_input:
            response = engine.process_conversational_input(user_input)
            print(f"\n{response}\n")

    def _format_history_response(self, history: List[Dict], user_input: str) -> str:
        """Formatar resposta com histórico de conversas"""
        response = "📜 **Histórico de Conversas Recentes:**\n\n"
        
        for msg in history[-10:]:  # Últimas 10 mensagens
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            emoji = "👤" if role == "user" else "🤖"
            response += f"{emoji} **{role.title()}** ({timestamp}):\n{content[:200]}...\n\n"
        
        return response
