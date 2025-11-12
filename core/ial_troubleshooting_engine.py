#!/usr/bin/env python3
"""
IAL Troubleshooting Engine - Diagnóstico inteligente de problemas
Combina CloudWatch + CloudTrail + Bedrock para troubleshooting avançado
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class IALTroubleshootingEngine:
    """Engine de troubleshooting inteligente"""
    
    def __init__(self):
        # Engines especializados
        self.cloudwatch_analyzer = self._initialize_cloudwatch_analyzer()
        self.security_analyzer = self._initialize_security_analyzer()
        self.bedrock_engine = self._initialize_bedrock_engine()
        
        # Padrões de problemas conhecidos
        self.problem_patterns = {
            'performance': {
                'keywords': ['lento', 'slow', 'performance', 'latência', 'timeout'],
                'analysis_type': 'performance_deep_dive'
            },
            'connectivity': {
                'keywords': ['conexão', 'connection', 'network', 'não conecta', 'unreachable'],
                'analysis_type': 'network_analysis'
            },
            'authentication': {
                'keywords': ['login', 'auth', 'permission', 'access denied', 'unauthorized'],
                'analysis_type': 'security_analysis'
            },
            'application_errors': {
                'keywords': ['erro', 'error', 'exception', 'crash', 'falha', 'failure'],
                'analysis_type': 'application_analysis'
            },
            'cost_anomaly': {
                'keywords': ['custo alto', 'billing', 'expensive', 'cost spike'],
                'analysis_type': 'cost_analysis'
            }
        }
    
    def _initialize_cloudwatch_analyzer(self):
        """Inicializar CloudWatch Analyzer"""
        try:
            from .cloudwatch_analyzer import CloudWatchIntegration
            return CloudWatchIntegration()
        except ImportError:
            return None
    
    def _initialize_security_analyzer(self):
        """Inicializar Security Analyzer"""
        try:
            from .security_analyzer import SecurityIntegration
            return SecurityIntegration()
        except ImportError:
            return None
    
    def _initialize_bedrock_engine(self):
        """Inicializar Bedrock Engine"""
        try:
            from lib.bedrock_conversation_engine import BedrockConversationEngine
            return BedrockConversationEngine()
        except ImportError:
            return None
    
    async def diagnose_problem(self, user_description: str, user_id: str = "default") -> Dict:
        """Diagnóstico principal de problemas"""
        
        # 1. Classificar tipo de problema
        problem_type = self._classify_problem(user_description)
        
        # 2. Executar análise específica
        analysis_result = await self._execute_analysis(problem_type, user_description)
        
        # 3. Gerar diagnóstico inteligente via Bedrock
        diagnosis = await self._generate_intelligent_diagnosis(
            user_description, 
            problem_type, 
            analysis_result,
            user_id
        )
        
        return {
            'problem_type': problem_type,
            'analysis_result': analysis_result,
            'diagnosis': diagnosis,
            'timestamp': datetime.now().isoformat()
        }
    
    def _classify_problem(self, description: str) -> Dict:
        """Classificar tipo de problema baseado na descrição"""
        
        description_lower = description.lower()
        
        # Calcular score para cada tipo de problema
        scores = {}
        for problem_type, config in self.problem_patterns.items():
            score = sum(1 for keyword in config['keywords'] if keyword in description_lower)
            if score > 0:
                scores[problem_type] = {
                    'score': score,
                    'analysis_type': config['analysis_type']
                }
        
        # Retornar tipo com maior score
        if scores:
            best_match = max(scores.items(), key=lambda x: x[1]['score'])
            return {
                'type': best_match[0],
                'confidence': best_match[1]['score'] / len(self.problem_patterns[best_match[0]]['keywords']),
                'analysis_type': best_match[1]['analysis_type']
            }
        
        # Fallback para análise geral
        return {
            'type': 'general',
            'confidence': 0.5,
            'analysis_type': 'general_analysis'
        }
    
    async def _execute_analysis(self, problem_type: Dict, description: str) -> Dict:
        """Executar análise específica baseada no tipo de problema"""
        
        analysis_type = problem_type.get('analysis_type', 'general_analysis')
        
        if analysis_type == 'performance_deep_dive':
            return await self._analyze_performance_issues(description)
        elif analysis_type == 'network_analysis':
            return await self._analyze_network_issues(description)
        elif analysis_type == 'security_analysis':
            return await self._analyze_security_issues(description)
        elif analysis_type == 'application_analysis':
            return await self._analyze_application_issues(description)
        elif analysis_type == 'cost_analysis':
            return await self._analyze_cost_issues(description)
        else:
            return await self._analyze_general_issues(description)
    
    async def _analyze_performance_issues(self, description: str) -> Dict:
        """Análise profunda de problemas de performance"""
        
        analysis = {
            'type': 'performance_analysis',
            'metrics': {},
            'bottlenecks': [],
            'recommendations': []
        }
        
        if self.cloudwatch_analyzer:
            try:
                # Análise de performance EC2
                performance_data = await self.cloudwatch_analyzer.process_monitoring_query("performance analysis")
                
                if performance_data.get('type') == 'ec2_instances':
                    analysis['metrics']['ec2_performance'] = performance_data
                    
                    # Detectar gargalos
                    for instance in performance_data.get('instances', []):
                        cpu_avg = instance.get('performance_metrics', {}).get('cpu', {}).get('average', 0)
                        memory_avg = instance.get('performance_metrics', {}).get('memory', {}).get('average', 0)
                        
                        if cpu_avg > 80:
                            analysis['bottlenecks'].append({
                                'type': 'cpu_bottleneck',
                                'instance': instance['instance_id'],
                                'severity': 'high',
                                'value': f"{cpu_avg}% CPU",
                                'impact': 'Application slowdown, request timeouts'
                            })
                        
                        if memory_avg > 85:
                            analysis['bottlenecks'].append({
                                'type': 'memory_bottleneck',
                                'instance': instance['instance_id'],
                                'severity': 'high',
                                'value': f"{memory_avg}% Memory",
                                'impact': 'Risk of OOM kills, application instability'
                            })
                
                # Gerar recomendações baseadas nos gargalos
                if analysis['bottlenecks']:
                    for bottleneck in analysis['bottlenecks']:
                        if bottleneck['type'] == 'cpu_bottleneck':
                            analysis['recommendations'].append({
                                'action': 'Scale up instance type',
                                'priority': 'high',
                                'estimated_impact': 'Reduce CPU usage by 40-60%',
                                'implementation': f"Upgrade {bottleneck['instance']} to larger instance type"
                            })
                        elif bottleneck['type'] == 'memory_bottleneck':
                            analysis['recommendations'].append({
                                'action': 'Increase memory or optimize application',
                                'priority': 'high',
                                'estimated_impact': 'Prevent OOM kills, improve stability',
                                'implementation': f"Scale up {bottleneck['instance']} or tune application memory usage"
                            })
                
            except Exception as e:
                analysis['error'] = f"CloudWatch analysis failed: {str(e)}"
        
        return analysis
    
    async def _analyze_network_issues(self, description: str) -> Dict:
        """Análise de problemas de rede"""
        
        return {
            'type': 'network_analysis',
            'common_issues': [
                {
                    'issue': 'Security Group misconfiguration',
                    'probability': 'high',
                    'check': 'Verify inbound/outbound rules for required ports',
                    'solution': 'Update Security Group rules to allow traffic'
                },
                {
                    'issue': 'NACLs blocking traffic',
                    'probability': 'medium',
                    'check': 'Review Network ACL rules in VPC',
                    'solution': 'Modify NACL rules to allow required traffic'
                },
                {
                    'issue': 'Route table misconfiguration',
                    'probability': 'medium',
                    'check': 'Verify route tables have correct routes',
                    'solution': 'Add missing routes or fix route targets'
                },
                {
                    'issue': 'DNS resolution problems',
                    'probability': 'low',
                    'check': 'Test DNS resolution from source',
                    'solution': 'Configure DNS settings or use Route 53'
                }
            ],
            'diagnostic_steps': [
                'Test connectivity with telnet/nc to specific port',
                'Check Security Group inbound/outbound rules',
                'Verify NACLs are not blocking traffic',
                'Review VPC Flow Logs for dropped packets',
                'Test DNS resolution if using domain names'
            ]
        }
    
    async def _analyze_security_issues(self, description: str) -> Dict:
        """Análise de problemas de segurança"""
        
        analysis = {
            'type': 'security_analysis',
            'security_events': {},
            'threats': [],
            'recommendations': []
        }
        
        if self.security_analyzer:
            try:
                # Análise de segurança de login
                security_data = await self.security_analyzer.process_security_query(description)
                
                if security_data.get('type') == 'login_security':
                    analysis['security_events'] = security_data
                    
                    # Extrair ameaças
                    threats = security_data.get('threats_detected', [])
                    analysis['threats'] = threats
                    
                    # Gerar recomendações baseadas nas ameaças
                    for threat in threats:
                        if threat.get('type') == 'brute_force_ip':
                            analysis['recommendations'].append({
                                'action': 'Block suspicious IP addresses',
                                'priority': 'high',
                                'implementation': f"Add {threat.get('source_ip')} to Security Group deny rules",
                                'automation': 'Configure AWS WAF rate limiting'
                            })
                        elif threat.get('type') == 'brute_force_user':
                            analysis['recommendations'].append({
                                'action': 'Implement account lockout policy',
                                'priority': 'high',
                                'implementation': f"Enable account lockout for {threat.get('target_user')}",
                                'automation': 'Configure IAM password policy with lockout'
                            })
                
            except Exception as e:
                analysis['error'] = f"Security analysis failed: {str(e)}"
        
        return analysis
    
    async def _analyze_application_issues(self, description: str) -> Dict:
        """Análise de problemas de aplicação"""
        
        return {
            'type': 'application_analysis',
            'common_patterns': [
                {
                    'pattern': 'OutOfMemoryError',
                    'cause': 'Insufficient heap size or memory leak',
                    'solution': 'Increase JVM heap size or fix memory leaks',
                    'monitoring': 'Monitor heap usage and GC metrics'
                },
                {
                    'pattern': 'ConnectionTimeout',
                    'cause': 'Database or external service unavailable',
                    'solution': 'Check database connectivity and increase timeout',
                    'monitoring': 'Monitor database connections and response times'
                },
                {
                    'pattern': 'NullPointerException',
                    'cause': 'Code bug with null reference',
                    'solution': 'Add null checks and defensive programming',
                    'monitoring': 'Review application logs for stack traces'
                },
                {
                    'pattern': 'HTTP 5xx errors',
                    'cause': 'Server-side application errors',
                    'solution': 'Check application logs and fix underlying issues',
                    'monitoring': 'Monitor error rates and response codes'
                }
            ],
            'diagnostic_steps': [
                'Check application logs for error patterns',
                'Monitor JVM metrics (heap, GC, threads)',
                'Verify database connectivity and performance',
                'Check external service dependencies',
                'Review recent deployments for changes'
            ]
        }
    
    async def _analyze_cost_issues(self, description: str) -> Dict:
        """Análise de problemas de custo"""
        
        if self.cloudwatch_analyzer:
            try:
                cost_data = await self.cloudwatch_analyzer.process_monitoring_query("cost anomaly")
                return cost_data
            except Exception as e:
                return {'error': f"Cost analysis failed: {str(e)}"}
        
        return {
            'type': 'cost_analysis',
            'common_causes': [
                'Unoptimized instance types',
                'Idle resources running 24/7',
                'Excessive data transfer costs',
                'Unattached EBS volumes',
                'Over-provisioned RDS instances'
            ]
        }
    
    async def _analyze_general_issues(self, description: str) -> Dict:
        """Análise geral de problemas"""
        
        return {
            'type': 'general_analysis',
            'message': 'General troubleshooting analysis',
            'next_steps': [
                'Provide more specific details about the problem',
                'Check CloudWatch metrics for anomalies',
                'Review recent changes or deployments',
                'Verify service health and dependencies'
            ]
        }
    
    async def _generate_intelligent_diagnosis(self, user_description: str, problem_type: Dict, analysis_result: Dict, user_id: str) -> str:
        """Gerar diagnóstico inteligente via Bedrock"""
        
        if not self.bedrock_engine:
            return self._generate_simple_diagnosis(problem_type, analysis_result)
        
        try:
            # Preparar prompt para Bedrock
            diagnosis_prompt = f"""O usuário relatou o seguinte problema: "{user_description}"

Tipo de problema identificado: {problem_type.get('type', 'unknown')} (confiança: {problem_type.get('confidence', 0):.1%})

Dados da análise técnica:
{json.dumps(analysis_result, indent=2)}

Como especialista em troubleshooting AWS, forneça um diagnóstico claro e acionável:

1. **Resumo do problema** (1-2 frases)
2. **Causa mais provável** baseada na análise
3. **Passos imediatos** para resolver (máximo 3 passos)
4. **Monitoramento** para prevenir recorrência

Use linguagem clara e técnica, com emojis apropriados. Seja específico e acionável."""
            
            # Processar via Bedrock
            bedrock_result = self.bedrock_engine.process_conversation(
                user_input=diagnosis_prompt,
                user_id=user_id
            )
            
            return bedrock_result['response']
            
        except Exception as e:
            return f"❌ Erro no diagnóstico inteligente: {str(e)}\n\n{self._generate_simple_diagnosis(problem_type, analysis_result)}"
    
    def _generate_simple_diagnosis(self, problem_type: Dict, analysis_result: Dict) -> str:
        """Diagnóstico simples (fallback)"""
        
        problem_name = problem_type.get('type', 'unknown').replace('_', ' ').title()
        
        diagnosis = f"🔍 **Diagnóstico: {problem_name}**\n\n"
        
        # Adicionar informações específicas baseadas no tipo
        if analysis_result.get('type') == 'performance_analysis':
            bottlenecks = analysis_result.get('bottlenecks', [])
            if bottlenecks:
                diagnosis += "⚠️ **Gargalos identificados:**\n"
                for bottleneck in bottlenecks[:3]:
                    diagnosis += f"• {bottleneck.get('type', 'Unknown')}: {bottleneck.get('value', 'N/A')}\n"
            
            recommendations = analysis_result.get('recommendations', [])
            if recommendations:
                diagnosis += "\n💡 **Recomendações:**\n"
                for rec in recommendations[:3]:
                    diagnosis += f"• {rec.get('action', 'Unknown action')}\n"
        
        elif analysis_result.get('type') == 'security_analysis':
            threats = analysis_result.get('threats', [])
            if threats:
                diagnosis += f"🚨 **Ameaças detectadas:** {len(threats)}\n"
                for threat in threats[:2]:
                    diagnosis += f"• {threat.get('description', 'Unknown threat')}\n"
        
        elif analysis_result.get('type') == 'network_analysis':
            diagnosis += "🌐 **Problemas de rede mais comuns:**\n"
            for issue in analysis_result.get('common_issues', [])[:3]:
                diagnosis += f"• {issue.get('issue', 'Unknown')}: {issue.get('solution', 'Check configuration')}\n"
        
        return diagnosis

# Integração com sistema principal
class TroubleshootingIntegration:
    """Integração do Troubleshooting Engine"""
    
    def __init__(self):
        self.engine = IALTroubleshootingEngine()
    
    async def process_troubleshooting_request(self, user_input: str, user_id: str = "default") -> Dict:
        """Processar requisição de troubleshooting"""
        
        return await self.engine.diagnose_problem(user_input, user_id)

# Teste do engine
if __name__ == "__main__":
    import asyncio
    
    async def test_troubleshooting():
        engine = IALTroubleshootingEngine()
        
        test_problems = [
            "Minha aplicação está muito lenta",
            "Não consigo conectar no banco de dados",
            "Muitos failed logins no CloudTrail",
            "Aplicação dando OutOfMemoryError",
            "Custo da AWS disparou este mês"
        ]
        
        print("🔍 Testando Troubleshooting Engine...")
        
        for problem in test_problems:
            print(f"\n👤 Problema: {problem}")
            result = await engine.diagnose_problem(problem)
            print(f"🎯 Tipo: {result['problem_type']['type']} ({result['problem_type']['confidence']:.1%})")
            print(f"📊 Análise: {result['analysis_result']['type']}")
    
    asyncio.run(test_troubleshooting())
