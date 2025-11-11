#!/usr/bin/env python3
"""
MCP Orchestrator - Coordena execução de múltiplos MCPs
Parte do MCP Router Inteligente
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class MCPStatus(Enum):
    INACTIVE = "inactive"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class MCPExecution:
    mcp_name: str
    status: MCPStatus
    start_time: float
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None

class MCPOrchestrator:
    def __init__(self):
        self.active_mcps = {}
        self.execution_history = []
        self.max_concurrent_loads = 3
        self.default_timeout = 10.0

    async def execute_coordinated(self, mcps: List, context: Dict, user_input: str) -> Dict:
        """Executa múltiplos MCPs de forma coordenada"""
        execution_start = time.time()
        
        # Organizar MCPs por fases
        phases = self._organize_by_phases(mcps)
        
        results = {
            'execution_id': f"exec_{int(execution_start)}",
            'user_input': user_input,
            'phases': {},
            'total_mcps': len(mcps),
            'success': False,
            'execution_time': 0.0,
            'errors': []
        }
        
        try:
            # Executar fases sequencialmente
            for phase_name, phase_mcps in phases.items():
                print(f"🔄 Executando fase: {phase_name} ({len(phase_mcps)} MCPs)")
                
                phase_result = await self._execute_phase(phase_mcps, context, user_input)
                results['phases'][phase_name] = phase_result
                
                # Se fase crítica falhar, parar execução
                if not phase_result['success'] and phase_name in ['foundation', 'security']:
                    results['errors'].append(f"Fase crítica {phase_name} falhou")
                    break
            
            # Determinar sucesso geral
            results['success'] = all(
                phase['success'] for phase in results['phases'].values()
            )
            
        except Exception as e:
            results['errors'].append(f"Erro na orquestração: {str(e)}")
        
        finally:
            results['execution_time'] = time.time() - execution_start
        
        return results

    async def _execute_phase(self, mcps: List, context: Dict, user_input: str) -> Dict:
        """Executa uma fase específica com MCPs em paralelo"""
        phase_start = time.time()
        
        # Garantir que MCPs estão carregados
        await self._ensure_mcps_loaded(mcps)
        
        # Executar MCPs em paralelo (dentro da fase)
        tasks = []
        for mcp in mcps:
            task = self._execute_single_mcp(mcp, context, user_input)
            tasks.append(task)
        
        # Aguardar conclusão de todos os MCPs da fase
        mcp_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        phase_result = {
            'mcps': len(mcps),
            'success': True,
            'execution_time': time.time() - phase_start,
            'results': {},
            'errors': []
        }
        
        for i, result in enumerate(mcp_results):
            mcp_name = mcps[i].mcp_name if hasattr(mcps[i], 'mcp_name') else f"mcp_{i}"
            
            if isinstance(result, Exception):
                phase_result['success'] = False
                phase_result['errors'].append(f"{mcp_name}: {str(result)}")
            else:
                phase_result['results'][mcp_name] = result
        
        return phase_result

    async def _execute_single_mcp(self, mcp, context: Dict, user_input: str) -> Dict:
        """Executa um MCP individual"""
        mcp_name = getattr(mcp, 'mcp_name', 'unknown')
        execution = MCPExecution(mcp_name, MCPStatus.LOADING, time.time())
        
        try:
            # Simular execução do MCP (substituir por chamada real)
            await asyncio.sleep(0.1)  # Simular latência
            
            # Aqui seria a chamada real para o MCP
            result = await self._call_mcp(mcp, context, user_input)
            
            execution.status = MCPStatus.ACTIVE
            execution.result = result
            execution.end_time = time.time()
            
            return {
                'mcp': mcp_name,
                'success': True,
                'result': result,
                'execution_time': execution.end_time - execution.start_time
            }
            
        except asyncio.TimeoutError:
            execution.status = MCPStatus.TIMEOUT
            execution.error = "Timeout na execução"
            execution.end_time = time.time()
            
            return {
                'mcp': mcp_name,
                'success': False,
                'error': 'Timeout',
                'execution_time': execution.end_time - execution.start_time
            }
            
        except Exception as e:
            execution.status = MCPStatus.ERROR
            execution.error = str(e)
            execution.end_time = time.time()
            
            return {
                'mcp': mcp_name,
                'success': False,
                'error': str(e),
                'execution_time': execution.end_time - execution.start_time
            }
        
        finally:
            self.execution_history.append(execution)

    async def _call_mcp(self, mcp, context: Dict, user_input: str) -> Dict:
        """Chama um MCP específico (placeholder para implementação real)"""
        mcp_name = getattr(mcp, 'mcp_name', 'unknown')
        
        # ESTRATÉGIA HÍBRIDA: aws-real-executor + CDK seletivo
        if mcp_name == 'aws-real-executor':
            import subprocess
            import json
            
            # Verificar se precisa de CDK para recursos complexos
            if self._needs_cdk_deployment(user_input):
                return await self._deploy_via_cdk_selector(user_input, context)
            
            # Usar aws-real-executor para recursos simples
            try:
                result = subprocess.run([
                    'python3', '/home/ial/mcp-tools/aws_real_server.py', 
                    'execute', user_input
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    real_result = json.loads(result.stdout)
                    return real_result
                else:
                    return {
                        'success': False,
                        'error': result.stderr,
                        'action': 'aws_real_execution_failed'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'action': 'aws_real_execution_error'
                }
        
        # Fallback para outros MCPs (simulação)
        return {
            'action': 'generic_action',
            'resources': ['resource'],
            'template': 'generic-template.yaml'
        }
    
    def _needs_cdk_deployment(self, user_input: str) -> bool:
        """Verifica se recurso precisa de CDK (código complexo)"""
        complex_resources = [
            'lambda function',
            'step functions state machine',
            'bedrock workflow',
            'migration workflow'
        ]
        
        user_input_lower = user_input.lower()
        return any(resource in user_input_lower for resource in complex_resources)
    
    async def _deploy_via_cdk_selector(self, user_input: str, context: Dict) -> Dict:
        """Deploy via CDK Selector para recursos complexos"""
        try:
            from core.cdk_selector import deploy_complex_resources
            
            project_name = context.get('project_name', 'ial-foundation')
            executor_name = context.get('executor_name', 'ial-executor')
            
            # Determinar tipo de recurso e nomes
            if 'lambda function' in user_input.lower():
                # Extrair nomes de funções Lambda
                function_names = self._extract_lambda_names(user_input)
                return deploy_complex_resources('lambda', function_names, project_name)
            
            elif 'step functions state machine' in user_input.lower():
                # Extrair nomes de state machines
                sm_names = self._extract_stepfunctions_names(user_input)
                return deploy_complex_resources('stepfunctions', sm_names, project_name)
            
            else:
                return {
                    'success': False,
                    'error': 'Complex resource type not recognized',
                    'action': 'cdk_selector_failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'cdk_selector_error'
            }
    
    def _extract_lambda_names(self, user_input: str) -> List[str]:
        """Extrai nomes de funções Lambda do input"""
        # Parse simples - melhorar conforme necessário
        if 'processor' in user_input.lower():
            return ['processor']
        elif 'validator' in user_input.lower():
            return ['validator']
        elif 'drift' in user_input.lower():
            return ['drift-detector']
        else:
            return ['generic-function']
    
    def _extract_stepfunctions_names(self, user_input: str) -> List[str]:
        """Extrai nomes de state machines do input"""
        # Parse simples - melhorar conforme necessário
        if 'orchestrator' in user_input.lower():
            return ['orchestrator']
        elif 'migration' in user_input.lower():
            return ['migration']
        elif 'bedrock' in user_input.lower():
            return ['bedrock-workflow']
        else:
            return ['generic-workflow']

    async def _ensure_mcps_loaded(self, mcps: List) -> None:
        """Garante que todos os MCPs estão carregados (lazy loading)"""
        load_tasks = []
        
        for mcp in mcps:
            mcp_name = getattr(mcp, 'mcp_name', 'unknown')
            if mcp_name not in self.active_mcps:
                task = self._load_mcp(mcp)
                load_tasks.append(task)
        
        if load_tasks:
            await asyncio.gather(*load_tasks)

    async def _load_mcp(self, mcp) -> None:
        """Carrega um MCP específico (lazy loading)"""
        mcp_name = getattr(mcp, 'mcp_name', 'unknown')
        timeout = getattr(mcp, 'load_timeout', self.default_timeout)
        
        try:
            # Simular carregamento do MCP
            await asyncio.wait_for(
                self._simulate_mcp_load(mcp_name),
                timeout=timeout
            )
            
            self.active_mcps[mcp_name] = {
                'status': MCPStatus.ACTIVE,
                'loaded_at': time.time(),
                'config': mcp
            }
            
            
        except asyncio.TimeoutError:
            print(f"⏰ Timeout carregando MCP {mcp_name}")
            self.active_mcps[mcp_name] = {
                'status': MCPStatus.TIMEOUT,
                'loaded_at': time.time(),
                'config': mcp
            }
        except Exception as e:
            print(f"❌ Erro carregando MCP {mcp_name}: {e}")
            self.active_mcps[mcp_name] = {
                'status': MCPStatus.ERROR,
                'loaded_at': time.time(),
                'config': mcp,
                'error': str(e)
            }

    async def _simulate_mcp_load(self, mcp_name: str) -> None:
        """Simula carregamento de MCP (substituir por implementação real)"""
        # Simular diferentes tempos de carregamento
        load_times = {
            'core-mcp': 0.5,
            'aws-iam-mcp': 1.0,
            'aws-cloudformation-mcp': 1.5,
            'aws-lambda-mcp': 2.0,
            'aws-ecs-mcp': 3.0,
            'aws-rds-mcp': 2.5
        }
        
        load_time = load_times.get(mcp_name, 1.0)
        await asyncio.sleep(load_time)

    def _organize_by_phases(self, mcps: List) -> Dict[str, List]:
        """Organiza MCPs em fases de execução"""
        phases = {
            'foundation': [],
            'security': [],
            'networking': [],
            'data': [],
            'compute': [],
            'application': [],
            'observability': []
        }
        
        for mcp in mcps:
            mcp_name = getattr(mcp, 'mcp_name', 'unknown')
            
            # AWS REAL EXECUTOR - PRIORIDADE MÁXIMA NA FOUNDATION
            if mcp_name == 'aws-real-executor':
                phases['foundation'].append(mcp)
            elif 'core' in mcp_name or 'cloudformation' in mcp_name:
                phases['foundation'].append(mcp)
            elif 'iam' in mcp_name or 'kms' in mcp_name or 'secrets' in mcp_name:
                phases['security'].append(mcp)
            elif 'vpc' in mcp_name or 'elb' in mcp_name or 'apigateway' in mcp_name:
                phases['networking'].append(mcp)
            elif 'rds' in mcp_name or 'dynamodb' in mcp_name or 'elasticache' in mcp_name:
                phases['data'].append(mcp)
            elif 'ecs' in mcp_name or 'lambda' in mcp_name or 'eks' in mcp_name:
                phases['compute'].append(mcp)
            elif 'stepfunctions' in mcp_name or 'sns' in mcp_name or 'sqs' in mcp_name:
                phases['application'].append(mcp)
            elif 'cloudwatch' in mcp_name or 'xray' in mcp_name:
                phases['observability'].append(mcp)
        
        # Remover fases vazias e manter ordem
        return {phase: mcps for phase, mcps in phases.items() if mcps}

    def get_active_mcps(self) -> Dict[str, Dict]:
        """Retorna MCPs atualmente ativos"""
        return {
            name: info for name, info in self.active_mcps.items()
            if info['status'] == MCPStatus.ACTIVE
        }

    def get_execution_stats(self) -> Dict:
        """Retorna estatísticas de execução"""
        if not self.execution_history:
            return {'total_executions': 0}
        
        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e.status == MCPStatus.ACTIVE)
        avg_time = sum(
            (e.end_time or time.time()) - e.start_time 
            for e in self.execution_history
        ) / total
        
        return {
            'total_executions': total,
            'successful': successful,
            'success_rate': successful / total,
            'average_execution_time': avg_time,
            'active_mcps': len(self.get_active_mcps())
        }
