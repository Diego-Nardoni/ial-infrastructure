#!/usr/bin/env python3
"""
Cost Optimization Engine - Otimização inteligente de custos AWS
Análise de custos + recomendações + automação via MCP + Bedrock
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class CostOptimizationEngine:
    """Engine de otimização de custos inteligente"""
    
    def __init__(self):
        self.cost_analyzer = self._initialize_cost_analyzer()
        self.bedrock_engine = self._initialize_bedrock_engine()
        
        # Thresholds de otimização
        self.optimization_thresholds = {
            'cpu_underutilized': 10.0,  # CPU < 10%
            'memory_underutilized': 20.0,  # Memory < 20%
            'idle_hours': 72,  # 3 dias idle
            'storage_ia_eligible_days': 30,  # S3 IA elegível
            'reserved_instance_threshold': 0.7  # 70% utilização
        }
    
    def _initialize_cost_analyzer(self):
        """Inicializar analisador de custos"""
        try:
            from .cloudwatch_analyzer import CloudWatchIntegration
            return CloudWatchIntegration()
        except ImportError:
            return None
    
    def _initialize_bedrock_engine(self):
        """Inicializar Bedrock Engine"""
        try:
            from lib.bedrock_conversation_engine import BedrockConversationEngine
            return BedrockConversationEngine()
        except ImportError:
            return None
    
    async def analyze_cost_optimization(self, user_query: str = "", user_id: str = "default") -> Dict:
        """Análise completa de otimização de custos"""
        
        optimization_result = {
            'analysis_type': 'cost_optimization',
            'timestamp': datetime.now().isoformat(),
            'current_costs': {},
            'optimization_opportunities': [],
            'potential_savings': 0.0,
            'recommendations': [],
            'implementation_plan': []
        }
        
        # 1. Análise de custos atuais
        if self.cost_analyzer:
            try:
                cost_data = await self.cost_analyzer.process_monitoring_query("cost anomaly")
                optimization_result['current_costs'] = cost_data
            except Exception as e:
                optimization_result['error'] = f"Cost analysis failed: {str(e)}"
        
        # 2. Identificar oportunidades de otimização
        opportunities = await self._identify_optimization_opportunities()
        optimization_result['optimization_opportunities'] = opportunities
        
        # 3. Calcular economia potencial
        total_savings = sum(opp.get('monthly_savings', 0) for opp in opportunities)
        optimization_result['potential_savings'] = total_savings
        
        # 4. Gerar recomendações priorizadas
        recommendations = self._generate_prioritized_recommendations(opportunities)
        optimization_result['recommendations'] = recommendations
        
        # 5. Criar plano de implementação
        implementation_plan = self._create_implementation_plan(recommendations)
        optimization_result['implementation_plan'] = implementation_plan
        
        return optimization_result
    
    async def _identify_optimization_opportunities(self) -> List[Dict]:
        """Identificar oportunidades de otimização"""
        
        opportunities = []
        
        # 1. EC2 Right-sizing
        ec2_opportunities = await self._analyze_ec2_rightsizing()
        opportunities.extend(ec2_opportunities)
        
        # 2. Storage optimization
        storage_opportunities = await self._analyze_storage_optimization()
        opportunities.extend(storage_opportunities)
        
        # 3. Reserved Instances
        ri_opportunities = await self._analyze_reserved_instances()
        opportunities.extend(ri_opportunities)
        
        # 4. Idle resources
        idle_opportunities = await self._analyze_idle_resources()
        opportunities.extend(idle_opportunities)
        
        # 5. Data transfer optimization
        transfer_opportunities = await self._analyze_data_transfer()
        opportunities.extend(transfer_opportunities)
        
        return opportunities
    
    async def _analyze_ec2_rightsizing(self) -> List[Dict]:
        """Análise de rightsizing EC2"""
        
        opportunities = []
        
        # Simular dados de instâncias (seria via CloudWatch real)
        instances_data = [
            {
                'instance_id': 'i-0123456789abcdef0',
                'instance_type': 't3.large',
                'avg_cpu': 8.5,
                'avg_memory': 15.2,
                'current_cost': 61.32,
                'environment': 'staging'
            },
            {
                'instance_id': 'i-0987654321fedcba0',
                'instance_type': 't3.xlarge',
                'avg_cpu': 12.1,
                'avg_memory': 18.7,
                'current_cost': 122.64,
                'environment': 'development'
            }
        ]
        
        for instance in instances_data:
            # Detectar subutilização
            if (instance['avg_cpu'] < self.optimization_thresholds['cpu_underutilized'] and 
                instance['avg_memory'] < self.optimization_thresholds['memory_underutilized']):
                
                # Sugerir instância menor
                recommended_type = self._suggest_smaller_instance_type(instance['instance_type'])
                if recommended_type:
                    savings = instance['current_cost'] * 0.5  # 50% economia estimada
                    
                    opportunities.append({
                        'type': 'ec2_rightsizing',
                        'resource_id': instance['instance_id'],
                        'current_type': instance['instance_type'],
                        'recommended_type': recommended_type,
                        'reason': f"Low utilization: {instance['avg_cpu']:.1f}% CPU, {instance['avg_memory']:.1f}% Memory",
                        'monthly_savings': savings,
                        'implementation_effort': 'medium',
                        'risk_level': 'low',
                        'environment': instance['environment']
                    })
        
        return opportunities
    
    async def _analyze_storage_optimization(self) -> List[Dict]:
        """Análise de otimização de storage"""
        
        opportunities = []
        
        # S3 Lifecycle policies
        opportunities.append({
            'type': 's3_lifecycle',
            'resource_id': 'ial-logs-backup',
            'current_storage_class': 'STANDARD',
            'recommended_action': 'Implement lifecycle policy: IA after 30 days, Glacier after 90 days',
            'reason': 'Objects older than 30 days rarely accessed',
            'monthly_savings': 12.50,
            'implementation_effort': 'low',
            'risk_level': 'very_low'
        })
        
        # EBS volume optimization
        opportunities.append({
            'type': 'ebs_optimization',
            'resource_id': 'vol-0123456789abcdef0',
            'current_type': 'gp3',
            'current_size': '100GB',
            'recommended_action': 'Resize to 50GB based on actual usage',
            'reason': 'Volume utilization < 40%',
            'monthly_savings': 5.75,
            'implementation_effort': 'low',
            'risk_level': 'low'
        })
        
        return opportunities
    
    async def _analyze_reserved_instances(self) -> List[Dict]:
        """Análise de Reserved Instances"""
        
        opportunities = []
        
        # Simular análise de RI
        opportunities.append({
            'type': 'reserved_instances',
            'resource_type': 'EC2',
            'instance_types': ['t3.large', 't3.medium'],
            'recommended_action': 'Purchase 1-year Reserved Instances for production workloads',
            'reason': 'Consistent usage pattern for 8+ months',
            'monthly_savings': 45.20,
            'upfront_cost': 1200.00,
            'payback_period': '26 months',
            'implementation_effort': 'low',
            'risk_level': 'low'
        })
        
        return opportunities
    
    async def _analyze_idle_resources(self) -> List[Dict]:
        """Análise de recursos idle"""
        
        opportunities = []
        
        # Instâncias idle
        opportunities.append({
            'type': 'idle_instance',
            'resource_id': 'i-0abcdef123456789',
            'resource_type': 't3.medium',
            'idle_duration': '5 days',
            'recommended_action': 'Stop instance during off-hours or terminate if unused',
            'reason': 'No significant activity detected',
            'monthly_savings': 30.66,
            'implementation_effort': 'low',
            'risk_level': 'medium'
        })
        
        # Load Balancers sem targets
        opportunities.append({
            'type': 'unused_load_balancer',
            'resource_id': 'alb-staging-unused',
            'recommended_action': 'Delete unused Application Load Balancer',
            'reason': 'No active targets for 30+ days',
            'monthly_savings': 22.50,
            'implementation_effort': 'low',
            'risk_level': 'low'
        })
        
        return opportunities
    
    async def _analyze_data_transfer(self) -> List[Dict]:
        """Análise de otimização de data transfer"""
        
        opportunities = []
        
        # CloudFront optimization
        opportunities.append({
            'type': 'cloudfront_optimization',
            'recommended_action': 'Enable CloudFront for static assets',
            'reason': 'High data transfer costs from S3 to users',
            'monthly_savings': 18.75,
            'implementation_effort': 'medium',
            'risk_level': 'low'
        })
        
        return opportunities
    
    def _suggest_smaller_instance_type(self, current_type: str) -> Optional[str]:
        """Sugerir tipo de instância menor"""
        
        downsize_map = {
            't3.xlarge': 't3.large',
            't3.large': 't3.medium',
            't3.medium': 't3.small',
            't3.small': 't3.micro',
            'm5.xlarge': 'm5.large',
            'm5.large': 'm5.medium',
            'c5.xlarge': 'c5.large',
            'c5.large': 'c5.medium'
        }
        
        return downsize_map.get(current_type)
    
    def _generate_prioritized_recommendations(self, opportunities: List[Dict]) -> List[Dict]:
        """Gerar recomendações priorizadas"""
        
        # Calcular score de prioridade
        for opp in opportunities:
            savings = opp.get('monthly_savings', 0)
            effort_score = {'low': 3, 'medium': 2, 'high': 1}.get(opp.get('implementation_effort', 'medium'), 2)
            risk_score = {'very_low': 4, 'low': 3, 'medium': 2, 'high': 1}.get(opp.get('risk_level', 'medium'), 2)
            
            # Score = (savings * effort * risk) / 100
            opp['priority_score'] = (savings * effort_score * risk_score) / 100
        
        # Ordenar por prioridade
        sorted_opportunities = sorted(opportunities, key=lambda x: x.get('priority_score', 0), reverse=True)
        
        # Gerar recomendações estruturadas
        recommendations = []
        for i, opp in enumerate(sorted_opportunities[:10]):  # Top 10
            recommendations.append({
                'rank': i + 1,
                'title': self._generate_recommendation_title(opp),
                'description': self._generate_recommendation_description(opp),
                'monthly_savings': opp.get('monthly_savings', 0),
                'implementation_effort': opp.get('implementation_effort', 'medium'),
                'risk_level': opp.get('risk_level', 'medium'),
                'priority_score': opp.get('priority_score', 0),
                'resource_id': opp.get('resource_id', ''),
                'type': opp.get('type', '')
            })
        
        return recommendations
    
    def _generate_recommendation_title(self, opportunity: Dict) -> str:
        """Gerar título da recomendação"""
        
        opp_type = opportunity.get('type', '')
        savings = opportunity.get('monthly_savings', 0)
        
        titles = {
            'ec2_rightsizing': f"Rightsize EC2 instance (${savings:.2f}/mês)",
            's3_lifecycle': f"Implement S3 lifecycle policy (${savings:.2f}/mês)",
            'reserved_instances': f"Purchase Reserved Instances (${savings:.2f}/mês)",
            'idle_instance': f"Stop idle EC2 instance (${savings:.2f}/mês)",
            'unused_load_balancer': f"Remove unused Load Balancer (${savings:.2f}/mês)",
            'cloudfront_optimization': f"Enable CloudFront caching (${savings:.2f}/mês)"
        }
        
        return titles.get(opp_type, f"Cost optimization opportunity (${savings:.2f}/mês)")
    
    def _generate_recommendation_description(self, opportunity: Dict) -> str:
        """Gerar descrição da recomendação"""
        
        resource_id = opportunity.get('resource_id', 'N/A')
        reason = opportunity.get('reason', 'Cost optimization opportunity')
        action = opportunity.get('recommended_action', 'Review and optimize')
        
        return f"Resource: {resource_id}\nReason: {reason}\nAction: {action}"
    
    def _create_implementation_plan(self, recommendations: List[Dict]) -> List[Dict]:
        """Criar plano de implementação"""
        
        plan = []
        
        # Agrupar por esforço de implementação
        low_effort = [r for r in recommendations if r.get('implementation_effort') == 'low']
        medium_effort = [r for r in recommendations if r.get('implementation_effort') == 'medium']
        high_effort = [r for r in recommendations if r.get('implementation_effort') == 'high']
        
        # Fase 1: Quick wins (low effort)
        if low_effort:
            plan.append({
                'phase': 1,
                'title': 'Quick Wins (Week 1)',
                'description': 'Low effort, immediate impact optimizations',
                'recommendations': low_effort[:5],
                'estimated_savings': sum(r.get('monthly_savings', 0) for r in low_effort[:5]),
                'duration': '1 week'
            })
        
        # Fase 2: Medium effort optimizations
        if medium_effort:
            plan.append({
                'phase': 2,
                'title': 'Strategic Optimizations (Week 2-3)',
                'description': 'Medium effort optimizations with significant impact',
                'recommendations': medium_effort[:3],
                'estimated_savings': sum(r.get('monthly_savings', 0) for r in medium_effort[:3]),
                'duration': '2 weeks'
            })
        
        # Fase 3: High effort, long-term optimizations
        if high_effort:
            plan.append({
                'phase': 3,
                'title': 'Long-term Optimizations (Month 2)',
                'description': 'High effort optimizations for sustained savings',
                'recommendations': high_effort[:2],
                'estimated_savings': sum(r.get('monthly_savings', 0) for r in high_effort[:2]),
                'duration': '1 month'
            })
        
        return plan
    
    async def generate_intelligent_report(self, optimization_result: Dict, user_id: str = "default") -> str:
        """Gerar relatório inteligente via Bedrock"""
        
        if not self.bedrock_engine:
            return self._generate_simple_report(optimization_result)
        
        try:
            # Preparar prompt para Bedrock
            report_prompt = f"""Análise de otimização de custos AWS concluída:

Economia potencial total: ${optimization_result.get('potential_savings', 0):.2f}/mês

Oportunidades identificadas:
{json.dumps(optimization_result.get('optimization_opportunities', []), indent=2)}

Recomendações priorizadas:
{json.dumps(optimization_result.get('recommendations', []), indent=2)}

Plano de implementação:
{json.dumps(optimization_result.get('implementation_plan', []), indent=2)}

Como especialista em FinOps AWS, crie um relatório executivo claro e acionável:

1. **Resumo Executivo** (economia total e principais oportunidades)
2. **Top 3 Recomendações** (maior impacto)
3. **Plano de Ação** (fases de implementação)
4. **ROI Esperado** (payback e benefícios)

Use linguagem executiva, emojis apropriados e seja específico com valores."""
            
            # Processar via Bedrock
            bedrock_result = self.bedrock_engine.process_conversation(
                user_input=report_prompt,
                user_id=user_id
            )
            
            return bedrock_result['response']
            
        except Exception as e:
            return f"❌ Erro no relatório inteligente: {str(e)}\n\n{self._generate_simple_report(optimization_result)}"
    
    def _generate_simple_report(self, optimization_result: Dict) -> str:
        """Relatório simples (fallback)"""
        
        total_savings = optimization_result.get('potential_savings', 0)
        recommendations = optimization_result.get('recommendations', [])
        
        report = f"💰 **Relatório de Otimização de Custos**\n\n"
        report += f"🎯 **Economia potencial:** ${total_savings:.2f}/mês\n\n"
        
        if recommendations:
            report += "🏆 **Top 3 Recomendações:**\n"
            for i, rec in enumerate(recommendations[:3], 1):
                report += f"{i}. {rec.get('title', 'Otimização')} - ${rec.get('monthly_savings', 0):.2f}/mês\n"
        
        return report

# Integração com sistema principal
class CostOptimizationIntegration:
    """Integração do Cost Optimization Engine"""
    
    def __init__(self):
        self.engine = CostOptimizationEngine()
    
    async def process_cost_optimization_request(self, user_input: str, user_id: str = "default") -> Dict:
        """Processar requisição de otimização de custos"""
        
        # Análise completa
        optimization_result = await self.engine.analyze_cost_optimization(user_input, user_id)
        
        # Gerar relatório inteligente
        intelligent_report = await self.engine.generate_intelligent_report(optimization_result, user_id)
        
        return {
            'optimization_analysis': optimization_result,
            'intelligent_report': intelligent_report
        }

# Teste do engine
if __name__ == "__main__":
    import asyncio
    
    async def test_cost_optimization():
        engine = CostOptimizationEngine()
        
        print("💰 Testando Cost Optimization Engine...")
        
        result = await engine.analyze_cost_optimization("como reduzir custos AWS")
        
        print(f"💵 Economia potencial: ${result['potential_savings']:.2f}/mês")
        print(f"🎯 Oportunidades: {len(result['optimization_opportunities'])}")
        print(f"📋 Recomendações: {len(result['recommendations'])}")
        print(f"📅 Fases do plano: {len(result['implementation_plan'])}")
    
    asyncio.run(test_cost_optimization())
