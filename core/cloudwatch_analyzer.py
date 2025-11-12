#!/usr/bin/env python3
"""
CloudWatch Analyzer - Análise avançada de métricas e logs via MCP
Implementa observabilidade inteligente com detecção de anomalias
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class CloudWatchAnalyzer:
    """Analisador avançado de métricas CloudWatch"""
    
    def __init__(self):
        self.mcp_client = self._get_cloudwatch_mcp()
        self.thresholds = {
            'cpu_high': 80.0,
            'cpu_low': 10.0,
            'memory_high': 85.0,
            'disk_high': 90.0,
            'network_anomaly': 1000000  # 1MB/s
        }
    
    def _get_cloudwatch_mcp(self):
        """Obter cliente MCP CloudWatch"""
        try:
            from .ial_query_engine import MCPClient
            config = {"command": "python", "args": ["-m", "mcp_aws_cloudwatch"]}
            return MCPClient("aws-cloudwatch", config)
        except ImportError:
            return None
    
    async def analyze_performance_metrics(self, resource_type: str = "ec2") -> Dict:
        """Análise completa de performance"""
        
        if resource_type == "ec2":
            return await self._analyze_ec2_performance()
        elif resource_type == "rds":
            return await self._analyze_rds_performance()
        elif resource_type == "lambda":
            return await self._analyze_lambda_performance()
        else:
            return {"error": f"Resource type {resource_type} not supported"}
    
    async def _analyze_ec2_performance(self) -> Dict:
        """Análise detalhada de performance EC2"""
        
        # Métricas principais EC2
        metrics_to_analyze = [
            {"name": "CPUUtilization", "stat": "Average"},
            {"name": "MemoryUtilization", "stat": "Average"},
            {"name": "DiskReadOps", "stat": "Sum"},
            {"name": "DiskWriteOps", "stat": "Sum"},
            {"name": "NetworkIn", "stat": "Sum"},
            {"name": "NetworkOut", "stat": "Sum"}
        ]
        
        analysis_results = {
            "resource_type": "ec2",
            "analysis_time": datetime.now().isoformat(),
            "instances": [],
            "anomalies": [],
            "recommendations": [],
            "performance_score": 0
        }
        
        # Simular análise de instâncias (seria MCP real)
        instances_data = await self._get_ec2_instances_metrics()
        
        for instance in instances_data:
            instance_analysis = await self._analyze_single_ec2_instance(instance)
            analysis_results["instances"].append(instance_analysis)
            
            # Detectar anomalias
            anomalies = self._detect_ec2_anomalies(instance_analysis)
            analysis_results["anomalies"].extend(anomalies)
            
            # Gerar recomendações
            recommendations = self._generate_ec2_recommendations(instance_analysis)
            analysis_results["recommendations"].extend(recommendations)
        
        # Calcular score geral
        analysis_results["performance_score"] = self._calculate_performance_score(analysis_results["instances"])
        
        return analysis_results
    
    async def _get_ec2_instances_metrics(self) -> List[Dict]:
        """Obter métricas de instâncias EC2 via MCP"""
        
        # Simulação de dados realísticos
        return [
            {
                "instance_id": "i-0123456789abcdef0",
                "instance_type": "t3.large",
                "environment": "production",
                "metrics": {
                    "cpu_utilization": [85.2, 78.9, 92.1, 76.5, 88.3],
                    "memory_utilization": [72.4, 68.9, 79.2, 71.1, 75.8],
                    "disk_read_ops": [1250, 1180, 1420, 1090, 1340],
                    "disk_write_ops": [890, 920, 1050, 780, 960],
                    "network_in": [2048000, 1890000, 2340000, 1750000, 2120000],
                    "network_out": [1560000, 1420000, 1780000, 1340000, 1650000]
                }
            },
            {
                "instance_id": "i-0987654321fedcba0",
                "instance_type": "t3.medium",
                "environment": "staging",
                "metrics": {
                    "cpu_utilization": [45.1, 42.3, 48.7, 39.8, 46.2],
                    "memory_utilization": [58.2, 55.7, 61.4, 52.9, 59.8],
                    "disk_read_ops": [680, 720, 650, 590, 710],
                    "disk_write_ops": [420, 380, 450, 360, 410],
                    "network_in": [890000, 920000, 850000, 780000, 910000],
                    "network_out": [650000, 680000, 620000, 590000, 670000]
                }
            }
        ]
    
    async def _analyze_single_ec2_instance(self, instance: Dict) -> Dict:
        """Análise detalhada de uma instância"""
        
        metrics = instance["metrics"]
        
        # Calcular estatísticas
        cpu_avg = sum(metrics["cpu_utilization"]) / len(metrics["cpu_utilization"])
        cpu_max = max(metrics["cpu_utilization"])
        memory_avg = sum(metrics["memory_utilization"]) / len(metrics["memory_utilization"])
        
        # Detectar tendências
        cpu_trend = self._calculate_trend(metrics["cpu_utilization"])
        memory_trend = self._calculate_trend(metrics["memory_utilization"])
        
        # Calcular IOPS
        read_iops = sum(metrics["disk_read_ops"]) / len(metrics["disk_read_ops"])
        write_iops = sum(metrics["disk_write_ops"]) / len(metrics["disk_write_ops"])
        
        # Calcular throughput de rede
        network_in_avg = sum(metrics["network_in"]) / len(metrics["network_in"])
        network_out_avg = sum(metrics["network_out"]) / len(metrics["network_out"])
        
        return {
            "instance_id": instance["instance_id"],
            "instance_type": instance["instance_type"],
            "environment": instance["environment"],
            "performance_metrics": {
                "cpu": {
                    "average": round(cpu_avg, 1),
                    "maximum": round(cpu_max, 1),
                    "trend": cpu_trend,
                    "status": self._get_cpu_status(cpu_avg, cpu_max)
                },
                "memory": {
                    "average": round(memory_avg, 1),
                    "trend": memory_trend,
                    "status": self._get_memory_status(memory_avg)
                },
                "disk": {
                    "read_iops": round(read_iops, 0),
                    "write_iops": round(write_iops, 0),
                    "total_iops": round(read_iops + write_iops, 0)
                },
                "network": {
                    "in_mbps": round(network_in_avg / 1024 / 1024, 2),
                    "out_mbps": round(network_out_avg / 1024 / 1024, 2),
                    "total_mbps": round((network_in_avg + network_out_avg) / 1024 / 1024, 2)
                }
            },
            "health_score": self._calculate_instance_health_score(cpu_avg, memory_avg, read_iops + write_iops)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcular tendência dos valores"""
        if len(values) < 2:
            return "stable"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff_percent = ((second_half - first_half) / first_half) * 100
        
        if diff_percent > 10:
            return "increasing"
        elif diff_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    def _get_cpu_status(self, avg: float, max_val: float) -> str:
        """Determinar status da CPU"""
        if max_val > 90 or avg > 80:
            return "critical"
        elif max_val > 80 or avg > 70:
            return "warning"
        elif avg < 10:
            return "underutilized"
        else:
            return "normal"
    
    def _get_memory_status(self, avg: float) -> str:
        """Determinar status da memória"""
        if avg > 85:
            return "critical"
        elif avg > 75:
            return "warning"
        elif avg < 20:
            return "underutilized"
        else:
            return "normal"
    
    def _calculate_instance_health_score(self, cpu_avg: float, memory_avg: float, iops: float) -> int:
        """Calcular score de saúde da instância"""
        score = 100
        
        # Penalizar CPU alta
        if cpu_avg > 80:
            score -= 30
        elif cpu_avg > 70:
            score -= 15
        
        # Penalizar memória alta
        if memory_avg > 85:
            score -= 25
        elif memory_avg > 75:
            score -= 10
        
        # Penalizar IOPS muito alto (possível gargalo)
        if iops > 5000:
            score -= 20
        elif iops > 3000:
            score -= 10
        
        # Penalizar recursos subutilizados
        if cpu_avg < 10 and memory_avg < 20:
            score -= 15
        
        return max(0, score)
    
    def _detect_ec2_anomalies(self, instance_analysis: Dict) -> List[Dict]:
        """Detectar anomalias na instância"""
        
        anomalies = []
        metrics = instance_analysis["performance_metrics"]
        instance_id = instance_analysis["instance_id"]
        
        # Anomalia de CPU
        if metrics["cpu"]["status"] == "critical":
            anomalies.append({
                "type": "cpu_critical",
                "instance_id": instance_id,
                "severity": "high",
                "description": f"CPU crítica: {metrics['cpu']['average']}% média, {metrics['cpu']['maximum']}% pico",
                "impact": "Performance degradada, possível timeout de aplicações"
            })
        
        # Anomalia de memória
        if metrics["memory"]["status"] == "critical":
            anomalies.append({
                "type": "memory_critical",
                "instance_id": instance_id,
                "severity": "high",
                "description": f"Memória crítica: {metrics['memory']['average']}% utilização",
                "impact": "Risco de OOM kills, instabilidade da aplicação"
            })
        
        # Anomalia de IOPS
        if metrics["disk"]["total_iops"] > 5000:
            anomalies.append({
                "type": "disk_bottleneck",
                "instance_id": instance_id,
                "severity": "medium",
                "description": f"IOPS elevado: {metrics['disk']['total_iops']} ops/sec",
                "impact": "Possível gargalo de I/O, latência aumentada"
            })
        
        # Anomalia de rede
        if metrics["network"]["total_mbps"] > 100:
            anomalies.append({
                "type": "network_high",
                "instance_id": instance_id,
                "severity": "medium",
                "description": f"Tráfego de rede alto: {metrics['network']['total_mbps']} Mbps",
                "impact": "Possível saturação de banda, latência de rede"
            })
        
        return anomalies
    
    def _generate_ec2_recommendations(self, instance_analysis: Dict) -> List[Dict]:
        """Gerar recomendações para a instância"""
        
        recommendations = []
        metrics = instance_analysis["performance_metrics"]
        instance_id = instance_analysis["instance_id"]
        instance_type = instance_analysis["instance_type"]
        
        # Recomendação de CPU
        if metrics["cpu"]["status"] == "critical":
            recommendations.append({
                "type": "scale_up",
                "instance_id": instance_id,
                "priority": "high",
                "action": f"Scale up de {instance_type} para tipo maior",
                "estimated_cost": "+$30-60/mês",
                "expected_benefit": "Redução de 40-60% na utilização de CPU"
            })
        elif metrics["cpu"]["status"] == "underutilized":
            recommendations.append({
                "type": "scale_down",
                "instance_id": instance_id,
                "priority": "medium",
                "action": f"Scale down de {instance_type} para tipo menor",
                "estimated_cost": "-$15-30/mês",
                "expected_benefit": "Otimização de custos sem impacto na performance"
            })
        
        # Recomendação de auto-scaling
        if metrics["cpu"]["trend"] == "increasing":
            recommendations.append({
                "type": "auto_scaling",
                "instance_id": instance_id,
                "priority": "medium",
                "action": "Configurar Auto Scaling Group",
                "estimated_cost": "Variável baseado na demanda",
                "expected_benefit": "Elasticidade automática, melhor disponibilidade"
            })
        
        # Recomendação de monitoramento
        if instance_analysis["health_score"] < 70:
            recommendations.append({
                "type": "enhanced_monitoring",
                "instance_id": instance_id,
                "priority": "low",
                "action": "Habilitar CloudWatch detailed monitoring",
                "estimated_cost": "+$2-5/mês",
                "expected_benefit": "Visibilidade granular, alertas proativos"
            })
        
        return recommendations
    
    def _calculate_performance_score(self, instances: List[Dict]) -> int:
        """Calcular score geral de performance"""
        
        if not instances:
            return 0
        
        total_score = sum(instance["health_score"] for instance in instances)
        return round(total_score / len(instances))
    
    async def analyze_application_logs(self, log_group: str, time_window: int = 24) -> Dict:
        """Análise de logs de aplicação"""
        
        # Simular análise de logs
        return {
            "log_group": log_group,
            "time_window_hours": time_window,
            "analysis_time": datetime.now().isoformat(),
            "log_statistics": {
                "total_events": 15847,
                "error_events": 234,
                "warning_events": 1205,
                "info_events": 14408,
                "error_rate": 1.48
            },
            "error_patterns": [
                {
                    "pattern": "ConnectionTimeout",
                    "count": 89,
                    "percentage": 38.0,
                    "trend": "increasing",
                    "sample_message": "Connection timeout to database after 30s"
                },
                {
                    "pattern": "OutOfMemoryError",
                    "count": 45,
                    "percentage": 19.2,
                    "trend": "stable",
                    "sample_message": "Java heap space exceeded"
                },
                {
                    "pattern": "NullPointerException",
                    "count": 67,
                    "percentage": 28.6,
                    "trend": "decreasing",
                    "sample_message": "Null pointer in user service"
                }
            ],
            "recommendations": [
                "Investigar timeouts de conexão com database",
                "Considerar aumento de heap size da JVM",
                "Implementar null checks no user service"
            ]
        }
    
    async def detect_cost_anomalies(self) -> Dict:
        """Detectar anomalias de custo"""
        
        # Simular detecção de anomalias de custo
        return {
            "analysis_time": datetime.now().isoformat(),
            "anomalies_detected": 3,
            "cost_anomalies": [
                {
                    "type": "unexpected_spike",
                    "service": "EC2",
                    "current_cost": 245.67,
                    "expected_cost": 180.50,
                    "variance_percent": 36.1,
                    "possible_causes": [
                        "Nova instância t3.large iniciada",
                        "Aumento no tráfego de rede"
                    ]
                },
                {
                    "type": "idle_resources",
                    "service": "RDS",
                    "wasted_cost": 45.20,
                    "resource": "db.t3.medium em staging",
                    "idle_duration": "72 hours",
                    "recommendation": "Parar instância durante off-hours"
                },
                {
                    "type": "storage_growth",
                    "service": "S3",
                    "growth_rate": "15% this month",
                    "current_cost": 23.45,
                    "projected_cost": 35.60,
                    "recommendation": "Implementar lifecycle policies"
                }
            ],
            "total_potential_savings": 78.90
        }

# Integração com conversational engine
class CloudWatchIntegration:
    """Integração do CloudWatch Analyzer com o sistema conversacional"""
    
    def __init__(self):
        self.analyzer = CloudWatchAnalyzer()
    
    async def process_monitoring_query(self, query: str) -> Dict:
        """Processar queries de monitoramento"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['performance', 'cpu', 'memory', 'disk']):
            return await self.analyzer.analyze_performance_metrics("ec2")
        elif any(keyword in query_lower for keyword in ['logs', 'error', 'exception']):
            return await self.analyzer.analyze_application_logs("/aws/lambda/my-function")
        elif any(keyword in query_lower for keyword in ['cost', 'anomaly', 'spike']):
            return await self.analyzer.detect_cost_anomalies()
        else:
            return {
                "type": "monitoring_help",
                "message": "Análise de monitoramento disponível",
                "options": [
                    "Análise de performance (CPU, memória, disk)",
                    "Análise de logs de aplicação",
                    "Detecção de anomalias de custo"
                ]
            }

# Teste do analyzer
if __name__ == "__main__":
    import asyncio
    
    async def test_analyzer():
        analyzer = CloudWatchAnalyzer()
        
        print("🔍 Testando CloudWatch Analyzer...")
        
        # Teste análise de performance
        performance_result = await analyzer.analyze_performance_metrics("ec2")
        print(f"📊 Performance Score: {performance_result['performance_score']}")
        print(f"🚨 Anomalias detectadas: {len(performance_result['anomalies'])}")
        print(f"💡 Recomendações: {len(performance_result['recommendations'])}")
        
        # Teste análise de logs
        logs_result = await analyzer.analyze_application_logs("/aws/lambda/test")
        print(f"📝 Error rate: {logs_result['log_statistics']['error_rate']}%")
        
        # Teste anomalias de custo
        cost_result = await analyzer.detect_cost_anomalies()
        print(f"💰 Economia potencial: ${cost_result['total_potential_savings']}")
    
    asyncio.run(test_analyzer())
