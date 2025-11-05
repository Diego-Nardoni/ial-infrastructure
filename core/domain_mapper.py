#!/usr/bin/env python3
"""
Domain Mapper - Mapeia domínios de serviços para MCPs específicos
Parte do MCP Router Inteligente
"""

from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class MCPMapping:
    mcp_name: str
    priority: int
    load_timeout: float
    health_check: bool

class DomainMapper:
    def __init__(self):
        # Mapeamento de domínios para MCPs
        self.domain_to_mcps = {
            'compute': [
                MCPMapping('aws-ecs-mcp', 1, 5.0, True),
                MCPMapping('aws-lambda-mcp', 1, 3.0, True),
                MCPMapping('aws-eks-mcp', 2, 8.0, True),
                MCPMapping('aws-ec2-mcp', 2, 5.0, True)
            ],
            'data': [
                MCPMapping('aws-rds-mcp', 1, 6.0, True),
                MCPMapping('aws-dynamodb-mcp', 1, 4.0, True),
                MCPMapping('aws-elasticache-mcp', 2, 5.0, True),
                MCPMapping('aws-s3-mcp', 2, 3.0, True)
            ],
            'networking': [
                MCPMapping('aws-elb-mcp', 1, 4.0, True),
                MCPMapping('aws-vpc-mcp', 1, 5.0, True),
                MCPMapping('aws-apigateway-mcp', 2, 4.0, True)
            ],
            'security': [
                MCPMapping('aws-iam-mcp', 1, 3.0, True),  # Core - sempre ativo
                MCPMapping('aws-kms-mcp', 2, 3.0, True),
                MCPMapping('aws-secrets-mcp', 2, 3.0, True)
            ],
            'serverless': [
                MCPMapping('aws-stepfunctions-mcp', 1, 5.0, True),
                MCPMapping('aws-sns-mcp', 2, 3.0, True),
                MCPMapping('aws-sqs-mcp', 2, 3.0, True)
            ],
            'observability': [
                MCPMapping('aws-cloudwatch-mcp', 1, 4.0, True),  # Core - sempre ativo
                MCPMapping('aws-xray-mcp', 2, 4.0, True)
            ],
            'devops': [
                MCPMapping('github-mcp-server', 1, 4.0, True)
            ]
            ],
            'finops': [
                MCPMapping('aws-cost-explorer-mcp', 1, 5.0, True),
                MCPMapping('aws-pricing-mcp', 2, 4.0, True),
                MCPMapping('aws-billing-mcp', 2, 4.0, True)
            ]
        }
        
        # MCPs sempre ativos (core)
        self.core_mcps = [
            MCPMapping('aws-cloudformation-mcp', 1, 3.0, True),
            MCPMapping('aws-iam-mcp', 1, 3.0, True),
            MCPMapping('aws-cloudwatch-mcp', 1, 4.0, True),
            MCPMapping('core-mcp', 1, 2.0, True)  # IAL internal tools
        ]
        
        # Mapeamento de serviços específicos para MCPs
        self.service_to_mcp = {
            'ecs': 'aws-ecs-mcp',
            'lambda': 'aws-lambda-mcp',
            'eks': 'aws-eks-mcp',
            'ec2': 'aws-ec2-mcp',
            'rds': 'aws-rds-mcp',
            'dynamodb': 'aws-dynamodb-mcp',
            'elasticache': 'aws-elasticache-mcp',
            's3': 'aws-s3-mcp',
            'elb': 'aws-elb-mcp',
            'vpc': 'aws-vpc-mcp',
            'apigateway': 'aws-apigateway-mcp',
            'iam': 'aws-iam-mcp',
            'kms': 'aws-kms-mcp',
            'secrets': 'aws-secrets-mcp',
            'stepfunctions': 'aws-stepfunctions-mcp',
            'sns': 'aws-sns-mcp',
            'sqs': 'aws-sqs-mcp',
            'cloudwatch': 'aws-cloudwatch-mcp',
            'xray': 'aws-xray-mcp'
        }

    def map_domains_to_mcps(self, domains: List[str]) -> List[MCPMapping]:
        """Mapeia lista de domínios para MCPs necessários"""
        required_mcps = []
        seen_mcps = set()
        
        # Sempre incluir core MCPs
        for core_mcp in self.core_mcps:
            if core_mcp.mcp_name not in seen_mcps:
                required_mcps.append(core_mcp)
                seen_mcps.add(core_mcp.mcp_name)
        
        # Adicionar MCPs específicos dos domínios
        for domain in domains:
            if domain in self.domain_to_mcps:
                for mcp in self.domain_to_mcps[domain]:
                    if mcp.mcp_name not in seen_mcps:
                        required_mcps.append(mcp)
                        seen_mcps.add(mcp.mcp_name)
        
        # Ordenar por prioridade
        required_mcps.sort(key=lambda x: x.priority)
        
        return required_mcps

    def map_services_to_mcps(self, services: List[str]) -> List[MCPMapping]:
        """Mapeia serviços específicos para MCPs"""
        required_mcps = []
        seen_mcps = set()
        
        # Sempre incluir core MCPs
        for core_mcp in self.core_mcps:
            if core_mcp.mcp_name not in seen_mcps:
                required_mcps.append(core_mcp)
                seen_mcps.add(core_mcp.mcp_name)
        
        # Mapear serviços específicos
        for service in services:
            if service in self.service_to_mcp:
                mcp_name = self.service_to_mcp[service]
                if mcp_name not in seen_mcps:
                    # Encontrar configuração do MCP
                    mcp_config = self._find_mcp_config(mcp_name)
                    if mcp_config:
                        required_mcps.append(mcp_config)
                        seen_mcps.add(mcp_name)
        
        # Ordenar por prioridade
        required_mcps.sort(key=lambda x: x.priority)
        
        return required_mcps

    def _find_mcp_config(self, mcp_name: str) -> MCPMapping:
        """Encontra configuração de um MCP específico"""
        # Procurar em todos os domínios
        for domain_mcps in self.domain_to_mcps.values():
            for mcp in domain_mcps:
                if mcp.mcp_name == mcp_name:
                    return mcp
        
        # Procurar nos core MCPs
        for mcp in self.core_mcps:
            if mcp.mcp_name == mcp_name:
                return mcp
        
        return None

    def get_deployment_phases(self, mcps: List[MCPMapping]) -> Dict[str, List[MCPMapping]]:
        """Organiza MCPs em fases de deployment baseado em dependências"""
        phases = {
            'foundation': [],
            'security': [],
            'networking': [],
            'data': [],
            'compute': [],
            'application': [],
            'observability': []
        }
        
        # Classificar MCPs por fase
        for mcp in mcps:
            if 'cloudformation' in mcp.mcp_name or 'core' in mcp.mcp_name:
                phases['foundation'].append(mcp)
            elif 'iam' in mcp.mcp_name or 'kms' in mcp.mcp_name or 'secrets' in mcp.mcp_name:
                phases['security'].append(mcp)
            elif 'vpc' in mcp.mcp_name or 'elb' in mcp.mcp_name or 'apigateway' in mcp.mcp_name:
                phases['networking'].append(mcp)
            elif 'rds' in mcp.mcp_name or 'dynamodb' in mcp.mcp_name or 'elasticache' in mcp.mcp_name or 's3' in mcp.mcp_name:
                phases['data'].append(mcp)
            elif 'ecs' in mcp.mcp_name or 'lambda' in mcp.mcp_name or 'eks' in mcp.mcp_name or 'ec2' in mcp.mcp_name:
                phases['compute'].append(mcp)
            elif 'stepfunctions' in mcp.mcp_name or 'sns' in mcp.mcp_name or 'sqs' in mcp.mcp_name:
                phases['application'].append(mcp)
            elif 'cloudwatch' in mcp.mcp_name or 'xray' in mcp.mcp_name:
                phases['observability'].append(mcp)
        
        # Remover fases vazias
        return {phase: mcps for phase, mcps in phases.items() if mcps}

    def get_mcp_capabilities(self, mcp_name: str) -> Dict[str, List[str]]:
        """Retorna capacidades conhecidas de um MCP"""
        capabilities = {
            'aws-ecs-mcp': ['create_cluster', 'create_service', 'create_task_definition', 'scale_service'],
            'aws-lambda-mcp': ['create_function', 'update_code', 'create_trigger', 'manage_layers'],
            'aws-rds-mcp': ['create_database', 'create_subnet_group', 'manage_snapshots', 'configure_security'],
            'aws-elb-mcp': ['create_load_balancer', 'create_target_group', 'configure_listeners', 'health_checks'],
            'aws-vpc-mcp': ['create_vpc', 'create_subnets', 'create_security_groups', 'configure_routing'],
            'aws-iam-mcp': ['create_roles', 'create_policies', 'attach_policies', 'manage_users'],
            'aws-cloudwatch-mcp': ['create_alarms', 'create_dashboards', 'query_logs', 'get_metrics']
        }
        
        return capabilities.get(mcp_name, [])
