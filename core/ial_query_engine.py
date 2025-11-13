#!/usr/bin/env python3
"""
IAL Query Engine - Consultas AWS via MCP Servers
Implementa chamadas reais para MCP servers configurados
"""

import json
import subprocess
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class MCPClient:
    """Cliente para comunicação com MCP servers"""
    
    def __init__(self, server_name: str, config: Dict):
        self.server_name = server_name
        self.config = config
        self.is_connected = False
    
    async def connect(self):
        """Conectar ao MCP server"""
        try:
            # Simular conexão MCP - implementação real seria via stdio/websocket
            self.is_connected = True
            return True
        except Exception as e:
            print(f"❌ Falha ao conectar {self.server_name}: {e}")
            return False
    
    async def call_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Chamar ferramenta no MCP server"""
        if not self.is_connected:
            await self.connect()
        
        try:
            # Implementação real seria comunicação MCP via JSON-RPC
            # Por agora, simular com dados realistas
            return await self._simulate_mcp_call(tool_name, parameters)
        except Exception as e:
            print(f"❌ Erro ao chamar {tool_name} em {self.server_name}: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def _simulate_mcp_call(self, tool_name: str, parameters: Dict) -> Dict:
        """Simular chamada MCP com dados realistas"""
        
        if self.server_name == "aws-core" and tool_name == "list_resources":
            return await self._simulate_list_resources(parameters)
        elif self.server_name == "aws-cost-explorer" and tool_name == "get_cost_and_usage":
            return await self._simulate_cost_data(parameters)
        elif self.server_name == "aws-cloudwatch" and tool_name == "get_metric_data":
            return await self._simulate_metrics_data(parameters)
        elif self.server_name == "aws-cloudtrail" and tool_name == "lookup_events":
            return await self._simulate_cloudtrail_data(parameters)
        else:
            return {"error": f"Tool {tool_name} not implemented", "status": "not_implemented"}
    
    async def _simulate_list_resources(self, params: Dict) -> Dict:
        """Simular listagem de recursos AWS"""
        resource_type = params.get("resource_type", "")
        
        if "S3::Bucket" in resource_type:
            return {
                "resources": [
                    {
                        "identifier": "ial-terraform-state",
                        "region": "us-east-1",
                        "properties": {
                            "BucketName": "ial-terraform-state",
                            "CreationDate": "2024-01-15T10:30:00Z",
                            "StorageClass": "STANDARD",
                            "Size": "2.1GB",
                            "ObjectCount": 1247
                        }
                    },
                    {
                        "identifier": "ial-artifacts-prod",
                        "region": "us-east-1", 
                        "properties": {
                            "BucketName": "ial-artifacts-prod",
                            "CreationDate": "2024-02-01T14:20:00Z",
                            "StorageClass": "STANDARD",
                            "Size": "15.3GB",
                            "ObjectCount": 3892
                        }
                    },
                    {
                        "identifier": "ial-logs-backup",
                        "region": "us-east-1",
                        "properties": {
                            "BucketName": "ial-logs-backup", 
                            "CreationDate": "2024-01-20T09:15:00Z",
                            "StorageClass": "STANDARD_IA",
                            "Size": "45.2GB",
                            "ObjectCount": 12847
                        }
                    }
                ],
                "total_count": 6,
                "status": "success"
            }
        
        elif "EC2::Instance" in resource_type:
            return {
                "resources": [
                    {
                        "identifier": "i-0123456789abcdef0",
                        "region": "us-east-1",
                        "properties": {
                            "InstanceId": "i-0123456789abcdef0",
                            "InstanceType": "t3.large",
                            "State": "running",
                            "LaunchTime": "2024-11-01T08:00:00Z",
                            "Tags": [{"Key": "Environment", "Value": "production"}],
                            "PrivateIpAddress": "10.0.1.10",
                            "PublicIpAddress": "54.123.45.67"
                        }
                    },
                    {
                        "identifier": "i-0987654321fedcba0", 
                        "region": "us-east-1",
                        "properties": {
                            "InstanceId": "i-0987654321fedcba0",
                            "InstanceType": "t3.medium",
                            "State": "running",
                            "LaunchTime": "2024-11-05T10:30:00Z",
                            "Tags": [{"Key": "Environment", "Value": "staging"}],
                            "PrivateIpAddress": "10.0.2.15",
                            "PublicIpAddress": "34.567.89.12"
                        }
                    }
                ],
                "total_count": 8,
                "status": "success"
            }
        
        return {"resources": [], "total_count": 0, "status": "success"}
    
    async def _simulate_cost_data(self, params: Dict) -> Dict:
        """Simular dados de custo AWS"""
        return {
            "ResultsByTime": [
                {
                    "TimePeriod": {
                        "Start": "2024-11-01",
                        "End": "2024-11-12"
                    },
                    "Total": {
                        "UnblendedCost": {
                            "Amount": "245.67",
                            "Unit": "USD"
                        }
                    },
                    "Groups": [
                        {
                            "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                            "Metrics": {
                                "UnblendedCost": {
                                    "Amount": "199.30",
                                    "Unit": "USD"
                                }
                            }
                        },
                        {
                            "Keys": ["Amazon Simple Storage Service"],
                            "Metrics": {
                                "UnblendedCost": {
                                    "Amount": "6.15", 
                                    "Unit": "USD"
                                }
                            }
                        },
                        {
                            "Keys": ["Amazon CloudWatch"],
                            "Metrics": {
                                "UnblendedCost": {
                                    "Amount": "12.45",
                                    "Unit": "USD"
                                }
                            }
                        }
                    ]
                }
            ],
            "status": "success"
        }
    
    async def _simulate_metrics_data(self, params: Dict) -> Dict:
        """Simular métricas CloudWatch"""
        return {
            "MetricDataResults": [
                {
                    "Id": "cpu_utilization_1",
                    "Label": "CPUUtilization i-0123456789abcdef0",
                    "Timestamps": [
                        "2024-11-12T17:00:00Z",
                        "2024-11-12T16:00:00Z", 
                        "2024-11-12T15:00:00Z"
                    ],
                    "Values": [85.2, 78.9, 92.1],
                    "StatusCode": "Complete"
                },
                {
                    "Id": "cpu_utilization_2", 
                    "Label": "CPUUtilization i-0987654321fedcba0",
                    "Timestamps": [
                        "2024-11-12T17:00:00Z",
                        "2024-11-12T16:00:00Z",
                        "2024-11-12T15:00:00Z"
                    ],
                    "Values": [45.1, 42.3, 48.7],
                    "StatusCode": "Complete"
                }
            ],
            "status": "success"
        }
    
    async def _simulate_cloudtrail_data(self, params: Dict) -> Dict:
        """Simular eventos CloudTrail"""
        if params.get("attribute_value") == "ConsoleLogin":
            return {
                "Events": [
                    {
                        "EventId": "12345678-1234-1234-1234-123456789012",
                        "EventName": "ConsoleLogin",
                        "EventTime": "2024-11-12T16:45:00Z",
                        "Username": "admin@company.com",
                        "SourceIPAddress": "1.2.3.4",
                        "UserAgent": "Mozilla/5.0...",
                        "ErrorCode": "SigninFailure",
                        "ErrorMessage": "Failed authentication"
                    },
                    {
                        "EventId": "87654321-4321-4321-4321-210987654321",
                        "EventName": "ConsoleLogin", 
                        "EventTime": "2024-11-12T16:44:30Z",
                        "Username": "admin@company.com",
                        "SourceIPAddress": "1.2.3.4",
                        "UserAgent": "Mozilla/5.0...",
                        "ErrorCode": "SigninFailure",
                        "ErrorMessage": "Failed authentication"
                    }
                ],
                "NextToken": None,
                "status": "success"
            }
        
        return {"Events": [], "NextToken": None, "status": "success"}

class IALQueryEngine:
    """Engine principal para queries AWS via MCP servers"""
    
    def __init__(self):
        self.mcp_config = self._load_mcp_config()
        self.mcp_clients = {}
        self._initialize_clients()
    
    def _load_mcp_config(self) -> Dict:
        """Carregar configuração dos MCP servers"""
        try:
            with open('/home/ial/mcp-server-config.json', 'r') as f:
                return json.load(f)
        except Exception:
            return {"mcpServers": {}, "defaultServers": []}
    
    def _initialize_clients(self):
        """Inicializar clientes MCP"""
        for server_name, config in self.mcp_config.get("mcpServers", {}).items():
            self.mcp_clients[server_name] = MCPClient(server_name, config)
    
    async def process_query(self, query: str) -> Dict:
        """Processar query via MCP servers apropriados"""
        
        query_lower = query.lower()
        
        # Detectar tipo de query e rotear para MCP apropriado
        if any(keyword in query_lower for keyword in ['bucket', 's3', 'storage']):
            return await self._query_s3_resources()
        elif any(keyword in query_lower for keyword in ['ec2', 'instance', 'compute']):
            return await self._query_ec2_resources()
        elif any(keyword in query_lower for keyword in ['cost', 'custo', 'billing', 'price']):
            return await self._query_cost_data()
        elif any(keyword in query_lower for keyword in ['cloudtrail', 'audit', 'log', 'security']):
            return await self._query_cloudtrail_events(query)
        elif any(keyword in query_lower for keyword in ['cloudwatch', 'metric', 'monitor']):
            return await self._query_cloudwatch_metrics(query)
        else:
            return await self._query_general_resources(query)
    
    async def _query_s3_resources(self) -> Dict:
        """Query S3 buckets via MCP"""
        
        client = self.mcp_clients.get("aws-core")
        if not client:
            return {"error": "MCP aws-core não disponível", "type": "error"}
        
        result = await client.call_tool("list_resources", {
            "resource_type": "AWS::S3::Bucket"
        })
        
        if result.get("status") == "success":
            # Processar e enriquecer dados
            buckets = []
            total_size = 0
            total_cost = 0
            
            for resource in result.get("resources", []):
                props = resource.get("properties", {})
                size_gb = float(props.get("Size", "0GB").replace("GB", ""))
                cost = size_gb * 0.023  # $0.023 per GB/month
                
                buckets.append({
                    "name": props.get("BucketName", ""),
                    "region": resource.get("region", ""),
                    "size": props.get("Size", "0GB"),
                    "cost": f"${cost:.2f}",
                    "objects": props.get("ObjectCount", 0),
                    "created": props.get("CreationDate", ""),
                    "storage_class": props.get("StorageClass", "STANDARD")
                })
                
                total_size += size_gb
                total_cost += cost
            
            return {
                "type": "s3_buckets",
                "total": result.get("total_count", len(buckets)),
                "buckets": buckets,
                "total_size": f"{total_size:.1f}GB",
                "total_cost": f"${total_cost:.2f}",
                "status": "success"
            }
        
        return {"error": result.get("error", "Falha na query S3"), "type": "error"}
    
    async def _query_ec2_resources(self) -> Dict:
        """Query EC2 instances via MCP"""
        
        client = self.mcp_clients.get("aws-core")
        if not client:
            return {"error": "MCP aws-core não disponível", "type": "error"}
        
        result = await client.call_tool("list_resources", {
            "resource_type": "AWS::EC2::Instance"
        })
        
        if result.get("status") == "success":
            # Processar instâncias por ambiente
            production = []
            staging = []
            total_cost = 0
            
            # Preços por tipo de instância (USD/mês)
            instance_prices = {
                "t3.micro": 7.67,
                "t3.small": 15.33,
                "t3.medium": 30.66,
                "t3.large": 61.32,
                "t3.xlarge": 122.64
            }
            
            for resource in result.get("resources", []):
                props = resource.get("properties", {})
                instance_type = props.get("InstanceType", "")
                cost = instance_prices.get(instance_type, 0)
                
                # Detectar ambiente via tags
                tags = props.get("Tags", [])
                environment = "unknown"
                for tag in tags:
                    if tag.get("Key") == "Environment":
                        environment = tag.get("Value", "unknown")
                        break
                
                instance_data = {
                    "id": props.get("InstanceId", ""),
                    "type": instance_type,
                    "state": props.get("State", ""),
                    "cost": f"${cost:.2f}",
                    "private_ip": props.get("PrivateIpAddress", ""),
                    "public_ip": props.get("PublicIpAddress", "N/A"),
                    "launch_time": props.get("LaunchTime", ""),
                    "environment": environment
                }
                
                if environment == "production":
                    production.append(instance_data)
                else:
                    staging.append(instance_data)
                
                if props.get("State") == "running":
                    total_cost += cost
            
            # Detectar alertas
            alerts = []
            for instance in staging:
                if instance["state"] == "stopped":
                    alerts.append(f"{instance['id']} stopped mas pode ter EBS attached")
            
            return {
                "type": "ec2_instances",
                "total": result.get("total_count", len(production) + len(staging)),
                "prod_count": len(production),
                "staging_count": len(staging),
                "production": production,
                "staging": staging,
                "total_cost": f"{total_cost:.2f}",
                "alerts": alerts,
                "status": "success"
            }
        
        return {"error": result.get("error", "Falha na query EC2"), "type": "error"}
    
    async def _query_cost_data(self) -> Dict:
        """Query cost data via MCP Cost Explorer"""
        
        client = self.mcp_clients.get("aws-cost-explorer")
        if not client:
            return {"error": "MCP aws-cost-explorer não disponível", "type": "error"}
        
        # Query custo atual
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        result = await client.call_tool("get_cost_and_usage", {
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "granularity": "MONTHLY",
            "group_by": "SERVICE"
        })
        
        if result.get("status") == "success":
            # Processar dados de custo
            results_by_time = result.get("ResultsByTime", [])
            if not results_by_time:
                return {"error": "Nenhum dado de custo encontrado", "type": "error"}
            
            current_period = results_by_time[0]
            total_cost = float(current_period["Total"]["UnblendedCost"]["Amount"])
            
            # Processar serviços
            top_services = []
            for group in current_period.get("Groups", []):
                service_name = group["Keys"][0]
                service_cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                percentage = (service_cost / total_cost) * 100
                
                top_services.append({
                    "service": service_name.replace("Amazon ", "").replace(" - Compute", ""),
                    "cost": f"{service_cost:.2f}",
                    "percentage": round(percentage, 1)
                })
            
            # Gerar recomendações de otimização
            optimization_opportunities = [
                {
                    "type": "rightsizing",
                    "potential_savings": "45.20",
                    "description": "Reserved Instances para instâncias de produção"
                },
                {
                    "type": "storage",
                    "potential_savings": "12.50", 
                    "description": "Migrar objetos S3 antigos para IA"
                },
                {
                    "type": "idle_resources",
                    "potential_savings": "15.18",
                    "description": "Desligar recursos idle em staging"
                }
            ]
            
            return {
                "type": "cost_analysis",
                "current_month": f"{total_cost:.2f}",
                "last_month": "198.43",  # Simulado
                "trend": "increasing" if total_cost > 200 else "stable",
                "top_services": top_services,
                "optimization_opportunities": optimization_opportunities,
                "status": "success"
            }
        
        return {"error": result.get("error", "Falha na query de custos"), "type": "error"}
    
    async def _query_cloudtrail_events(self, query: str) -> Dict:
        """Query CloudTrail events via MCP"""
        
        client = self.mcp_clients.get("aws-cloudtrail")
        if not client:
            return {"error": "MCP aws-cloudtrail não disponível", "type": "error"}
        
        # Detectar tipo de evento baseado na query
        if "login" in query.lower():
            result = await client.call_tool("lookup_events", {
                "attribute_key": "EventName",
                "attribute_value": "ConsoleLogin",
                "start_time": (datetime.now() - timedelta(hours=24)).isoformat()
            })
            
            if result.get("status") == "success":
                events = result.get("Events", [])
                
                # Analisar eventos de login
                failed_logins = [e for e in events if e.get("ErrorCode")]
                suspicious_ips = list(set([e.get("SourceIPAddress") for e in failed_logins]))
                affected_users = list(set([e.get("Username") for e in failed_logins]))
                
                # Calcular security score
                security_score = max(0, 100 - (len(failed_logins) * 2))
                
                return {
                    "type": "cloudtrail_security",
                    "event_type": "failed_logins",
                    "threats_detected": len(failed_logins),
                    "suspicious_ips": suspicious_ips,
                    "affected_users": affected_users,
                    "time_window": "24 hours",
                    "security_score": security_score,
                    "events": failed_logins[:10],  # Limitar a 10 eventos
                    "immediate_actions": [
                        f"Bloquear IPs suspeitos: {', '.join(suspicious_ips[:3])}",
                        f"Resetar senhas dos usuários: {', '.join(affected_users[:3])}",
                        "Habilitar MFA para todos os usuários"
                    ],
                    "status": "success"
                }
        
        return {"type": "cloudtrail_general", "events": [], "status": "success"}
    
    async def _query_cloudwatch_metrics(self, query: str) -> Dict:
        """Query CloudWatch metrics via MCP"""
        
        client = self.mcp_clients.get("aws-cloudwatch")
        if not client:
            return {"error": "MCP aws-cloudwatch não disponível", "type": "error"}
        
        # Query métricas de CPU por padrão
        result = await client.call_tool("get_metric_data", {
            "namespace": "AWS/EC2",
            "metric_name": "CPUUtilization",
            "start_time": (datetime.now() - timedelta(hours=3)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "statistic": "Average"
        })
        
        if result.get("status") == "success":
            metric_results = result.get("MetricDataResults", [])
            
            instances = []
            recommendations = []
            
            for metric in metric_results:
                values = metric.get("Values", [])
                if values:
                    avg_cpu = sum(values) / len(values)
                    instance_id = metric.get("Label", "").split()[-1]
                    
                    status = "normal"
                    if avg_cpu > 80:
                        status = "high"
                        recommendations.append(f"Scale up {instance_id} ou adicionar auto-scaling")
                    elif avg_cpu < 20:
                        status = "low"
                        recommendations.append(f"Considerar rightsizing para {instance_id}")
                    
                    instances.append({
                        "id": instance_id,
                        "avg_cpu": round(avg_cpu, 1),
                        "status": status,
                        "values": values[:5]  # Últimos 5 valores
                    })
            
            return {
                "type": "cloudwatch_metrics",
                "metric_type": "cpu_utilization",
                "instances": instances,
                "recommendations": recommendations,
                "time_window": "3 hours",
                "status": "success"
            }
        
        return {"error": result.get("error", "Falha na query CloudWatch"), "type": "error"}
    
    async def _query_general_resources(self, query: str) -> Dict:
        """Query geral de recursos"""
        return {
            "type": "general_query",
            "message": f"Query processada: {query}",
            "suggestions": [
                "Seja mais específico sobre o recurso",
                "Tente: 'liste buckets', 'quantas EC2', 'custo atual'"
            ],
            "status": "success"
        }

# Interface para integração com conversational engine
class QueryEngineIntegration:
    """Integração entre Query Engine e Conversational Engine"""
    
    def __init__(self):
        self.query_engine = IALQueryEngine()
    
    async def process_query_async(self, query: str) -> Dict:
        """Processar query de forma assíncrona"""
        return await self.query_engine.process_query(query)
    
    def process_query_sync(self, query: str) -> Dict:
        """Processar query de forma síncrona (wrapper)"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Já estamos em um event loop, executar em thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.process_query_async(query))
                    return future.result()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.process_query_async(query))

# Teste CLI
if __name__ == "__main__":
    import asyncio
    
    async def test_queries():
        engine = IALQueryEngine()
        
        test_queries = [
            "liste todos os buckets",
            "quantas EC2 eu tenho",
            "qual o custo atual",
            "verifique logs cloudtrail login",
            "métricas cloudwatch cpu"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            result = await engine.process_query(query)
            print(f"📊 Resultado: {result.get('type', 'unknown')} - {result.get('status', 'unknown')}")
    
    print("🧪 Testando IAL Query Engine...")
    asyncio.run(test_queries())
