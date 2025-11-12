#!/usr/bin/env python3
"""
MCP Query Client - Interface para MCP servers de consulta AWS
"""

import json
import subprocess
import asyncio
from typing import Dict, Any, Optional

class MCPQueryClient:
    """Cliente para MCP servers de consulta AWS"""
    
    def __init__(self):
        self.mcp_servers = {
            'aws_resources': {
                'command': ['python', '/home/ial/mcp-tools/aws_real_server.py'],
                'available': self._check_mcp_availability('aws_resources')
            },
            'cost_explorer': {
                'command': ['python', '-m', 'mcp_cost_explorer'],
                'available': self._check_mcp_availability('cost_explorer')
            },
            'cloudwatch': {
                'command': ['python', '-m', 'mcp_cloudwatch'],
                'available': self._check_mcp_availability('cloudwatch')
            },
            'cloudtrail': {
                'command': ['python', '-m', 'mcp_cloudtrail'],
                'available': self._check_mcp_availability('cloudtrail')
            }
        }
    
    def call_tool(self, server_name: str, tool_name: str, params: Dict) -> Optional[Dict]:
        """Chamar ferramenta MCP"""
        
        if not self.mcp_servers.get(server_name, {}).get('available'):
            return None
        
        try:
            # Preparar comando MCP
            command = self.mcp_servers[server_name]['command']
            
            # Preparar payload
            payload = {
                'tool': tool_name,
                'params': params
            }
            
            # Executar MCP server
            result = subprocess.run(
                command + ['call_tool', json.dumps(payload)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"⚠️ MCP {server_name} falhou: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"⚠️ Erro chamando MCP {server_name}: {e}")
            return None
    
    def list_s3_buckets(self) -> Optional[Dict]:
        """Listar buckets S3 via MCP"""
        return self.call_tool('aws_resources', 'list_resources', {
            'resource_type': 'AWS::S3::Bucket'
        })
    
    def list_ec2_instances(self) -> Optional[Dict]:
        """Listar instâncias EC2 via MCP"""
        return self.call_tool('aws_resources', 'list_resources', {
            'resource_type': 'AWS::EC2::Instance'
        })
    
    def get_cost_and_usage(self, start_date: str, end_date: str) -> Optional[Dict]:
        """Obter custos via MCP Cost Explorer"""
        return self.call_tool('cost_explorer', 'get_cost_and_usage', {
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'granularity': 'MONTHLY',
            'group_by': 'SERVICE'
        })
    
    def lookup_cloudtrail_events(self, event_name: str, hours_back: int = 24) -> Optional[Dict]:
        """Buscar eventos CloudTrail via MCP"""
        from datetime import datetime, timedelta
        
        start_time = (datetime.now() - timedelta(hours=hours_back)).isoformat()
        
        return self.call_tool('cloudtrail', 'lookup_events', {
            'attribute_key': 'EventName',
            'attribute_value': event_name,
            'start_time': start_time
        })
    
    def get_cloudwatch_metrics(self, namespace: str, metric_name: str, dimensions: Dict = None) -> Optional[Dict]:
        """Obter métricas CloudWatch via MCP"""
        from datetime import datetime, timedelta
        
        return self.call_tool('cloudwatch', 'get_metric_data', {
            'namespace': namespace,
            'metric_name': metric_name,
            'start_time': (datetime.now() - timedelta(hours=24)).isoformat(),
            'dimensions': dimensions or []
        })
    
    def _check_mcp_availability(self, server_name: str) -> bool:
        """Verificar se MCP server está disponível"""
        try:
            # Verificação simples - tentar executar help
            if server_name == 'aws_resources':
                # Verificar se aws_real_server.py existe
                import os
                return os.path.exists('/home/ial/mcp-tools/aws_real_server.py')
            else:
                # Para outros MCPs, assumir disponível se importável
                return True
        except:
            return False
    
    def get_server_status(self) -> Dict[str, bool]:
        """Obter status de todos os MCP servers"""
        return {
            server: config['available'] 
            for server, config in self.mcp_servers.items()
        }
