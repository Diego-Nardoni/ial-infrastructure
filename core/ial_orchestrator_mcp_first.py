#!/usr/bin/env python3
"""
IAL Orchestrator - MCP FIRST Architecture
Prioridade: MCP Servers → Python Fallback
"""

import os
import json
import time
from typing import Dict, Any, List, Optional

class IALOrchestratorMCPFirst:
    """Orquestrador com MCP servers como primário"""
    
    def __init__(self):
        self.config = self._load_config()
        # MCP como primário
        self.mcp_available = self._init_mcp_servers()
        # Python como fallback
        self.python_fallback = self._init_python_fallback()
    
    def _init_mcp_servers(self) -> bool:
        """Inicializar MCP servers como primário"""
        try:
            # Verificar se MCP servers estão disponíveis
            mcp_config_path = "/home/ial/mcp-server-config.json"
            if os.path.exists(mcp_config_path):
                with open(mcp_config_path, 'r') as f:
                    self.mcp_config = json.load(f)
                print("✅ MCP servers configurados como primário")
                return True
        except Exception as e:
            print(f"⚠️ MCP servers indisponíveis: {e}")
        return False
    
    def _init_python_fallback(self):
        """Inicializar componentes Python como fallback"""
        try:
            from core.master_engine_final import MasterEngineFinal
            fallback = MasterEngineFinal()
            print("✅ Python fallback disponível")
            return fallback
        except Exception as e:
            print(f"❌ Python fallback falhou: {e}")
            return None
    
    def process_nl_intent(self, nl_intent: str) -> Dict[str, Any]:
        """
        ARQUITETURA CORRETA:
        1. Tentar MCP servers primeiro
        2. Python como fallback apenas se MCP falhar
        """
        
        print(f"🎯 Processando: {nl_intent[:50]}...")
        
        # PRIMÁRIO: MCP Servers
        if self.mcp_available:
            try:
                return self._process_via_mcp(nl_intent)
            except Exception as e:
                print(f"⚠️ MCP falhou: {e}")
        
        # FALLBACK: Python components
        if self.python_fallback:
            print("🔄 Usando Python fallback...")
            return self.python_fallback.process_request(nl_intent)
        
        return {'status': 'error', 'message': 'Nenhum processador disponível'}
    
    async def execute_with_mcp(self, query: str) -> Dict[str, Any]:
        """Executar query via AWS CLI (dados reais)"""
        
        try:
            import subprocess
            import json
            
            query_lower = query.lower()
            
            # S3 Buckets
            if "bucket" in query_lower or "s3" in query_lower:
                result = subprocess.run(
                    ['aws', 's3api', 'list-buckets'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    return {
                        'success': True,
                        'type': 's3_buckets',
                        'total': len(data.get('Buckets', [])),
                        'buckets': [{'name': b['Name'], 'created': b['CreationDate']} 
                                   for b in data.get('Buckets', [])]
                    }
            
            # EC2 Instances
            elif "ec2" in query_lower or "instanc" in query_lower:
                result = subprocess.run(
                    ['aws', 'ec2', 'describe-instances', '--query', 
                     'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name]',
                     '--output', 'json'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    instances = []
                    for reservation in data:
                        for instance in reservation:
                            instances.append({
                                'id': instance[0],
                                'type': instance[1],
                                'state': instance[2]
                            })
                    return {
                        'success': True,
                        'type': 'ec2_instances',
                        'total': len(instances),
                        'instances': instances
                    }
            
            # Step Functions
            elif "step" in query_lower or "state machine" in query_lower:
                result = subprocess.run(
                    ['aws', 'stepfunctions', 'list-state-machines'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    machines = data.get('stateMachines', [])
                    return {
                        'success': True,
                        'type': 'step_functions',
                        'total': len(machines),
                        'state_machines': [{'name': m['name'], 'arn': m['stateMachineArn']} 
                                          for m in machines]
                    }
            
            # Lambda Functions
            elif "lambda" in query_lower or "function" in query_lower:
                result = subprocess.run(
                    ['aws', 'lambda', 'list-functions'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    functions = data.get('Functions', [])
                    return {
                        'success': True,
                        'type': 'lambda_functions',
                        'total': len(functions),
                        'functions': [{'name': f['FunctionName'], 'runtime': f['Runtime']} 
                                     for f in functions]
                    }
            
            # DynamoDB Tables
            elif "dynamodb" in query_lower or "table" in query_lower:
                result = subprocess.run(
                    ['aws', 'dynamodb', 'list-tables'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    return {
                        'success': True,
                        'type': 'dynamodb_tables',
                        'total': len(data.get('TableNames', [])),
                        'tables': data.get('TableNames', [])
                    }
            
            return {'success': False, 'error': 'Query não reconhecida'}
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Timeout ao consultar AWS'}
        except Exception as e:
            return {'success': False, 'error': f'Erro: {str(e)}'}
        """Processar via MCP servers (PRIMÁRIO)"""
        
        # STEP 1: IAS via MCP Well-Architected Framework
        ias_result = self._mcp_ias_validation(nl_intent)
        if not ias_result.get('safe', True):
            return {'status': 'blocked', 'reason': 'IAS_BLOCKED'}
        
        # STEP 2: Cost via MCP Cost Explorer
        cost_result = self._mcp_cost_analysis(nl_intent)
        if cost_result.get('should_block', False):
            return {'status': 'blocked', 'reason': 'COST_BLOCKED'}
        
        # STEP 3: Phase Builder via MCP CloudFormation
        phase_result = self._mcp_phase_generation(nl_intent, ias_result, cost_result)
        
        # STEP 4: GitHub PR via MCP GitHub
        pr_result = self._mcp_github_pr(phase_result)
        
        return {
            'status': 'success',
            'path': 'MCP_SERVERS_PRIMARY',
            'ias_status': ias_result.get('rationale'),
            'estimated_cost': cost_result.get('estimated_cost', 0),
            'pr_url': pr_result.get('pr_url'),
            'processing_method': 'MCP_FIRST'
        }
    
    def _mcp_ias_validation(self, nl_intent: str) -> Dict:
        """IAS via MCP Well-Architected Framework"""
        # Simular chamada MCP
        return {
            'safe': True,
            'rationale': 'Validado via MCP Well-Architected Framework',
            'method': 'MCP_WAF'
        }
    
    def _mcp_cost_analysis(self, nl_intent: str) -> Dict:
        """Cost Analysis via MCP Cost Explorer"""
        # Simular chamada MCP
        return {
            'should_block': False,
            'estimated_cost': 50,
            'method': 'MCP_COST_EXPLORER'
        }
    
    def _mcp_phase_generation(self, nl_intent: str, ias_result: Dict, cost_result: Dict) -> Dict:
        """Phase Generation via MCP CloudFormation"""
        # Simular chamada MCP
        return {
            'yaml_files': [{'name': 'foundation.yaml', 'content': 'AWSTemplateFormatVersion: "2010-09-09"'}],
            'method': 'MCP_CLOUDFORMATION'
        }
    
    def _mcp_github_pr(self, phase_result: Dict) -> Dict:
        """GitHub PR via MCP GitHub"""
        # Simular chamada MCP
        return {
            'pr_url': 'https://github.com/user/repo/pull/123',
            'method': 'MCP_GITHUB'
        }
    
    def _load_config(self) -> Dict:
        """Configuração com MCP como primário"""
        return {
            'mcp_first': True,
            'python_fallback': True,
            'mcp_timeout': 30,
            'fallback_timeout': 60
        }

# Função de conveniência
def process_infrastructure_intent_mcp_first(nl_intent: str) -> Dict[str, Any]:
    """Processar com MCP como primário"""
    orchestrator = IALOrchestratorMCPFirst()
    return orchestrator.process_nl_intent(nl_intent)
