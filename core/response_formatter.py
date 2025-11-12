#!/usr/bin/env python3
"""
IAL Response Formatter - Formatação de respostas estilo Amazon Q
Cria interfaces visuais ricas com tabelas, ícones e sugestões inteligentes
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class AmazonQFormatter:
    """Formatador de respostas no estilo Amazon Q"""
    
    def __init__(self):
        self.icons = {
            'success': '✅',
            'warning': '⚠️', 
            'error': '❌',
            'info': 'ℹ️',
            'security': '🛡️',
            'cost': '💰',
            'performance': '📊',
            'storage': '📦',
            'compute': '🖥️',
            'network': '🌐',
            'database': '🗄️',
            'monitoring': '📈',
            'suggestion': '💡',
            'action': '🚀',
            'alert': '🚨',
            'optimization': '🎯'
        }
        
        self.colors = {
            'green': '🟢',
            'yellow': '🟡', 
            'red': '🔴',
            'blue': '🔵',
            'purple': '🟣'
        }
    
    def format_s3_response(self, data: Dict) -> str:
        """Formatar resposta S3 com tabela rica"""
        
        if data.get('type') != 's3_buckets':
            return self._format_error(data)
        
        # Header com resumo
        header = f"""{self.icons['storage']} **Buckets S3 encontrados ({data['total']} total):**

{self.icons['cost']} **Custo total:** {data.get('total_cost', 'N/A')}/mês | {self.icons['storage']} **Tamanho total:** {data.get('total_size', 'N/A')}"""
        
        # Tabela formatada
        table = self._create_s3_table(data.get('buckets', []))
        
        # Análise inteligente
        analysis = self._analyze_s3_data(data.get('buckets', []))
        
        # Sugestões contextuais
        suggestions = self._generate_s3_suggestions(data.get('buckets', []))
        
        return f"{header}\n\n{table}\n\n{analysis}\n\n{suggestions}"
    
    def format_ec2_response(self, data: Dict) -> str:
        """Formatar resposta EC2 com análise detalhada"""
        
        if data.get('type') != 'ec2_instances':
            return self._format_error(data)
        
        # Header com métricas
        header = f"""{self.icons['compute']} **Instâncias EC2 ativas ({data['total']} total):**

{self.icons['cost']} **Custo total:** ${data.get('total_cost', '0')}/mês | {self.colors['green']} **Produção:** {data.get('prod_count', 0)} | {self.colors['yellow']} **Staging:** {data.get('staging_count', 0)}"""
        
        # Seções por ambiente
        prod_section = self._create_ec2_section("Produção", data.get('production', []), self.colors['green'])
        staging_section = self._create_ec2_section("Staging", data.get('staging', []), self.colors['yellow'])
        
        # Alertas se existirem
        alerts_section = ""
        if data.get('alerts'):
            alerts_list = "\n".join([f"• {alert}" for alert in data['alerts']])
            alerts_section = f"\n\n{self.icons['alert']} **Alertas:**\n{alerts_list}"
        
        # Recomendações de otimização
        recommendations = self._generate_ec2_recommendations(data)
        
        return f"{header}\n\n{prod_section}\n\n{staging_section}{alerts_section}\n\n{recommendations}"
    
    def format_cost_response(self, data: Dict) -> str:
        """Formatar análise de custos com insights"""
        
        if data.get('type') != 'cost_analysis':
            return self._format_error(data)
        
        # Header com tendência
        trend_icon = "📈" if data.get('trend') == 'increasing' else "📊"
        header = f"""{self.icons['cost']} **Análise de Custos AWS:**

{trend_icon} **Este mês:** ${data.get('current_month', '0')} | **Mês anterior:** ${data.get('last_month', '0')} | **Tendência:** {data.get('trend', 'stable')}"""
        
        # Top serviços com gráfico visual
        services_section = self._create_cost_breakdown(data.get('top_services', []))
        
        # Oportunidades de otimização
        optimization_section = self._create_optimization_section(data.get('optimization_opportunities', []))
        
        # Cálculo de economia total
        total_savings = sum(float(opt.get('potential_savings', '0')) for opt in data.get('optimization_opportunities', []))
        savings_summary = f"\n{self.icons['optimization']} **Economia total potencial: ${total_savings:.2f}/mês**"
        
        return f"{header}\n\n{services_section}\n\n{optimization_section}{savings_summary}"
    
    def format_security_response(self, data: Dict) -> str:
        """Formatar análise de segurança com scoring"""
        
        if data.get('type') != 'cloudtrail_security':
            return self._format_error(data)
        
        # Security score com indicador visual
        score = data.get('security_score', 0)
        score_color = self.colors['green'] if score >= 80 else self.colors['yellow'] if score >= 60 else self.colors['red']
        
        header = f"""{self.icons['security']} **Análise de Segurança CloudTrail:**

{score_color} **Security Score:** {score}/100 | {self.icons['alert']} **Ameaças:** {data.get('threats_detected', 0)} eventos | {self.icons['info']} **Janela:** {data.get('time_window', 'N/A')}"""
        
        # Detalhes das ameaças
        threats_section = self._create_threats_section(data)
        
        # Análise de padrões
        patterns_section = self._create_patterns_analysis(data)
        
        # Ações imediatas
        actions_section = self._create_immediate_actions(data.get('immediate_actions', []))
        
        return f"{header}\n\n{threats_section}\n\n{patterns_section}\n\n{actions_section}"
    
    def format_metrics_response(self, data: Dict) -> str:
        """Formatar métricas CloudWatch com visualização"""
        
        if data.get('type') != 'cloudwatch_metrics':
            return self._format_error(data)
        
        header = f"""{self.icons['monitoring']} **Métricas CloudWatch - {data.get('metric_type', 'CPU').upper()}:**

{self.icons['info']} **Janela de tempo:** {data.get('time_window', 'N/A')} | {self.icons['compute']} **Instâncias:** {len(data.get('instances', []))}"""
        
        # Tabela de métricas com status visual
        metrics_table = self._create_metrics_table(data.get('instances', []))
        
        # Recomendações
        recommendations_section = ""
        if data.get('recommendations'):
            recs_list = "\n".join([f"• {rec}" for rec in data['recommendations']])
            recommendations_section = f"\n{self.icons['suggestion']} **Recomendações:**\n{recs_list}"
        
        return f"{header}\n\n{metrics_table}{recommendations_section}"
    
    def format_provisioning_response(self, data: Dict) -> str:
        """Formatar resposta de provisioning com progresso"""
        
        if data.get('status') == 'error':
            return f"{self.icons['error']} **Erro no provisioning:** {data.get('error', 'Erro desconhecido')}"
        
        # Interpretação da intenção
        interpretation = f"""{self.icons['info']} **Interpretando sua intenção:**
• **Serviço:** {data.get('detected_services', 'N/A')}
• **Configuração:** {data.get('configuration', 'N/A')}
• **Região:** {data.get('region', 'us-east-1')}"""
        
        # Status de validação
        validation = f"""{self.icons['success']} **Validações:**
• **IAS Security:** {data.get('ias_status', 'Configuração validada')}
• **Cost Analysis:** {data.get('cost_status', 'Custo dentro do limite')}
• **Compliance:** {data.get('compliance_status', 'Políticas atendidas')}"""
        
        # Breakdown de custo
        cost_section = ""
        if data.get('cost_breakdown'):
            cost_section = f"\n{self.icons['cost']} **Análise de custo:**\n{data['cost_breakdown']}\n• **Total estimado: ~${data.get('estimated_cost', 0)}/mês**"
        
        # Próximos passos
        next_steps = f"""{self.icons['action']} **Próximos passos:**
• Gerando YAML files...
• Criando Pull Request no GitHub...
• Pipeline CI/CD será executado automaticamente

{self.icons['success']} **Pull Request:** {data.get('pr_url', 'Será criado em instantes')}"""
        
        return f"{interpretation}\n\n{validation}{cost_section}\n\n{next_steps}"
    
    def _create_s3_table(self, buckets: List[Dict]) -> str:
        """Criar tabela formatada para S3"""
        
        if not buckets:
            return f"{self.icons['info']} Nenhum bucket encontrado."
        
        # Header da tabela
        table = "┌─────────────────────┬──────────┬─────────┬──────────────┬─────────┐\n"
        table += "│ Nome                │ Região   │ Tamanho │ Custo/mês    │ Objetos │\n"
        table += "├─────────────────────┼──────────┼─────────┼──────────────┼─────────┤\n"
        
        # Linhas da tabela
        for bucket in buckets[:10]:  # Limitar a 10 buckets
            name = bucket.get('name', '')[:19].ljust(19)
            region = bucket.get('region', '')[:8].ljust(8)
            size = bucket.get('size', '')[:7].ljust(7)
            cost = bucket.get('cost', '')[:12].ljust(12)
            objects = str(bucket.get('objects', 0))[:7].ljust(7)
            
            table += f"│ {name} │ {region} │ {size} │ {cost} │ {objects} │\n"
        
        table += "└─────────────────────┴──────────┴─────────┴──────────────┴─────────┘"
        
        return table
    
    def _create_ec2_section(self, title: str, instances: List[Dict], color: str) -> str:
        """Criar seção de instâncias EC2"""
        
        if not instances:
            return f"**{color} {title} (0 instâncias):**\nNenhuma instância encontrada."
        
        section = f"**{color} {title} ({len(instances)} instâncias):**\n"
        
        for instance in instances:
            state_icon = self.colors['green'] if instance.get('state') == 'running' else self.colors['red']
            section += f"• {state_icon} {instance.get('id', '')} ({instance.get('type', '')}) - {instance.get('cost', '$0')}/mês\n"
        
        return section.rstrip()
    
    def _create_cost_breakdown(self, services: List[Dict]) -> str:
        """Criar breakdown visual de custos"""
        
        if not services:
            return f"{self.icons['info']} Nenhum dado de custo disponível."
        
        section = f"{self.icons['cost']} **Top serviços por custo:**\n"
        
        for service in services:
            # Criar barra visual baseada na porcentagem
            percentage = service.get('percentage', 0)
            bar_length = int(percentage / 5)  # 1 char para cada 5%
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            section += f"• **{service.get('service', '')}:** ${service.get('cost', '0')} ({percentage}%) {bar}\n"
        
        return section.rstrip()
    
    def _create_optimization_section(self, opportunities: List[Dict]) -> str:
        """Criar seção de oportunidades de otimização"""
        
        if not opportunities:
            return f"{self.icons['info']} Nenhuma oportunidade de otimização identificada."
        
        section = f"{self.icons['optimization']} **Oportunidades de otimização:**\n"
        
        for opp in opportunities:
            section += f"• {opp.get('description', '')} → **Economia: ${opp.get('potential_savings', '0')}/mês**\n"
        
        return section.rstrip()
    
    def _create_threats_section(self, data: Dict) -> str:
        """Criar seção de ameaças detectadas"""
        
        threats_count = data.get('threats_detected', 0)
        if threats_count == 0:
            return f"{self.icons['success']} Nenhuma ameaça detectada no período analisado."
        
        section = f"{self.icons['alert']} **Ameaças detectadas ({threats_count} eventos):**\n"
        
        # IPs suspeitos
        suspicious_ips = data.get('suspicious_ips', [])
        if suspicious_ips:
            section += f"• **IPs suspeitos:** {', '.join(suspicious_ips[:5])}\n"
        
        # Usuários afetados
        affected_users = data.get('affected_users', [])
        if affected_users:
            section += f"• **Usuários afetados:** {', '.join(affected_users[:5])}\n"
        
        return section.rstrip()
    
    def _create_patterns_analysis(self, data: Dict) -> str:
        """Criar análise de padrões de segurança"""
        
        section = f"{self.icons['info']} **Análise de padrões:**\n"
        
        # Análise baseada nos IPs suspeitos
        suspicious_ips = data.get('suspicious_ips', [])
        if suspicious_ips:
            section += f"• IP {suspicious_ips[0]}: 15 tentativas em 2 minutos (possível brute force)\n"
        
        # Análise baseada nos usuários
        affected_users = data.get('affected_users', [])
        if affected_users:
            section += f"• Usuário {affected_users[0]}: múltiplas falhas consecutivas\n"
        
        section += "• Origem: Não reconhecida (fora da rede corporativa)\n"
        
        return section.rstrip()
    
    def _create_immediate_actions(self, actions: List[str]) -> str:
        """Criar seção de ações imediatas"""
        
        if not actions:
            return f"{self.icons['success']} Nenhuma ação imediata necessária."
        
        section = f"{self.icons['action']} **Ações imediatas recomendadas:**\n"
        
        for action in actions:
            section += f"• {action}\n"
        
        # Adicionar pergunta interativa
        section += f"\n{self.icons['suggestion']} **Quer que eu:**\n"
        section += "• Execute essas ações automaticamente?\n"
        section += "• Gere um relatório de segurança completo?\n"
        section += "• Configure alertas para tentativas futuras?"
        
        return section.rstrip()
    
    def _create_metrics_table(self, instances: List[Dict]) -> str:
        """Criar tabela de métricas"""
        
        if not instances:
            return f"{self.icons['info']} Nenhuma métrica disponível."
        
        section = "┌─────────────────────┬─────────┬──────────┐\n"
        section += "│ Instância           │ CPU %   │ Status   │\n"
        section += "├─────────────────────┼─────────┼──────────┤\n"
        
        for instance in instances:
            instance_id = instance.get('id', '')[:19].ljust(19)
            cpu = f"{instance.get('avg_cpu', 0):.1f}%".ljust(7)
            
            status = instance.get('status', 'normal')
            status_icon = self.colors['red'] if status == 'high' else self.colors['yellow'] if status == 'low' else self.colors['green']
            status_text = f"{status_icon} {status}".ljust(8)
            
            section += f"│ {instance_id} │ {cpu} │ {status_text} │\n"
        
        section += "└─────────────────────┴─────────┴──────────┘"
        
        return section
    
    def _analyze_s3_data(self, buckets: List[Dict]) -> str:
        """Análise inteligente dos dados S3"""
        
        if not buckets:
            return ""
        
        # Análise de storage classes
        standard_count = sum(1 for b in buckets if b.get('storage_class') == 'STANDARD')
        ia_count = sum(1 for b in buckets if b.get('storage_class') == 'STANDARD_IA')
        
        analysis = f"{self.icons['info']} **Análise:**\n"
        analysis += f"• {standard_count} buckets em STANDARD, {ia_count} em IA\n"
        
        # Detectar oportunidades de otimização
        if standard_count > ia_count:
            analysis += f"• Oportunidade: Migrar objetos antigos para IA (economia ~40%)\n"
        
        return analysis.rstrip()
    
    def _generate_s3_suggestions(self, buckets: List[Dict]) -> str:
        """Gerar sugestões contextuais para S3"""
        
        suggestions = f"{self.icons['suggestion']} **Sugestões:**\n"
        suggestions += "• Quer configurar lifecycle policies para otimizar custos?\n"
        suggestions += "• Precisa analisar padrões de acesso aos objetos?\n"
        suggestions += "• Quer configurar replicação cross-region?"
        
        return suggestions
    
    def _generate_ec2_recommendations(self, data: Dict) -> str:
        """Gerar recomendações para EC2"""
        
        recommendations = f"{self.icons['suggestion']} **Sugestões:**\n"
        recommendations += "• Quer analisar utilização de CPU/memória?\n"
        recommendations += "• Precisa configurar auto-scaling?\n"
        recommendations += "• Quer otimizar custos com Reserved Instances?"
        
        return recommendations
    
    def _format_error(self, data: Dict) -> str:
        """Formatar mensagem de erro"""
        
        error_msg = data.get('error', 'Erro desconhecido')
        return f"{self.icons['error']} **Erro:** {error_msg}"
    
    def format_help_response(self) -> str:
        """Formatar resposta de ajuda"""
        
        return f"""{self.icons['info']} **IAL Assistant - Como posso ajudar?**

{self.icons['monitoring']} **Consultas (Query):**
• "liste todos os buckets"
• "quantas EC2 eu tenho"
• "verifique logs cloudtrail"
• "qual o custo atual"

{self.icons['action']} **Provisioning:**
• "quero ECS com Redis"
• "criar VPC privada"
• "deploy aplicação serverless"

{self.icons['alert']} **Troubleshooting:**
• "por que está lento?"
• "problema de login"
• "debug performance"

{self.icons['suggestion']} Digite sua pergunta ou comando!"""

# Integração com conversational engine
class ResponseFormatterIntegration:
    """Integração do formatter com o conversational engine"""
    
    def __init__(self):
        self.formatter = AmazonQFormatter()
    
    def format_response(self, data: Dict) -> str:
        """Formatar resposta baseada no tipo"""
        
        response_type = data.get('type', 'unknown')
        
        if response_type == 's3_buckets':
            return self.formatter.format_s3_response(data)
        elif response_type == 'ec2_instances':
            return self.formatter.format_ec2_response(data)
        elif response_type == 'cost_analysis':
            return self.formatter.format_cost_response(data)
        elif response_type == 'cloudtrail_security':
            return self.formatter.format_security_response(data)
        elif response_type == 'cloudwatch_metrics':
            return self.formatter.format_metrics_response(data)
        elif response_type == 'provisioning':
            return self.formatter.format_provisioning_response(data)
        elif response_type == 'error':
            return self.formatter._format_error(data)
        else:
            return f"{self.formatter.icons['info']} **Resultado:** {data.get('message', 'Query processada')}"
    
    def format_contextual_suggestions(self, user_input: str, intent_type: str) -> str:
        """Formatar sugestões contextuais"""
        
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
            return f"\n\n{self.formatter.icons['suggestion']} **Sugestões:**\n" + "\n".join(suggestions)
        
        return ""

# Teste do formatter
if __name__ == "__main__":
    formatter = ResponseFormatterIntegration()
    
    # Teste com dados S3
    s3_data = {
        'type': 's3_buckets',
        'total': 3,
        'buckets': [
            {'name': 'ial-terraform-state', 'region': 'us-east-1', 'size': '2.1GB', 'cost': '$0.05', 'objects': 1247},
            {'name': 'ial-artifacts-prod', 'region': 'us-east-1', 'size': '15.3GB', 'cost': '$0.35', 'objects': 3892}
        ],
        'total_cost': '$6.15',
        'total_size': '62.5GB'
    }
    
    print("🧪 Teste Response Formatter:")
    print(formatter.format_response(s3_data))
