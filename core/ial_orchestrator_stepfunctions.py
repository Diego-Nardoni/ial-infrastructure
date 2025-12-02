#!/usr/bin/env python3
"""
IAL Orchestrator - Step Functions Integration
Elimina lambda cola usando Step Functions como orquestrador
"""

import boto3
import json
import time
from typing import Dict, Any

class IALOrchestratorStepFunctions:
    """Orquestrador usando Step Functions (SEM lambda cola)"""
    
    def __init__(self):
        self.stepfunctions = boto3.client('stepfunctions')
        self.state_machines = {
            'phase_pipeline': self._get_state_machine_arn('ial-fork-phase-manager'),
            'audit_validator': self._get_state_machine_arn('ial-fork-audit-validator'),
            'drift_autoheal': self._get_state_machine_arn('ial-fork-healing-orchestrator')
        }
        
        # Fallback para Python (apenas se Step Functions falhar)
        try:
            from core.master_engine_final import MasterEngineFinal
            self.python_fallback = MasterEngineFinal()
        except ImportError:
            self.python_fallback = None
    
    def process_nl_intent(self, nl_intent: str) -> Dict[str, Any]:
        """
        Processar via Step Functions (ELIMINA lambda cola)
        """
        
        print(f"🔄 Processando via Step Functions: {nl_intent[:50]}...")
        
        # Preparar input para Step Functions
        execution_input = {
            'nl_intent': nl_intent,
            'timestamp': int(time.time()),
            'execution_id': f"ial-{int(time.time())}",
            'correlation_id': f"ial-{int(time.time())}",  # Adicionar correlation_id
            'mcp_first': True,
            'python_fallback_available': self.python_fallback is not None
        }
        
        try:
            # EXECUTAR via Step Functions (SEM lambda cola)
            response = self.stepfunctions.start_execution(
                stateMachineArn=self.state_machines['phase_pipeline'],
                name=execution_input['execution_id'],
                input=json.dumps(execution_input)
            )
            
            print(f"✅ Step Functions iniciado: {response['executionArn']}")
            
            # Aguardar conclusão (ou retornar para async)
            return self._wait_for_execution(response['executionArn'])
            
        except Exception as e:
            print(f"⚠️ Step Functions falhou: {e}")
            
            # Fallback para Python (apenas se Step Functions falhar)
            if self.python_fallback:
                print("🔄 Usando Python fallback...")
                return self.python_fallback.process_request(nl_intent)
            else:
                return {
                    'status': 'error',
                    'message': 'Step Functions e Python fallback indisponíveis',
                    'error': str(e)
                }
    
    def _wait_for_execution(self, execution_arn: str, timeout: int = 300) -> Dict[str, Any]:
        """Aguardar conclusão da execução Step Functions"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.stepfunctions.describe_execution(
                    executionArn=execution_arn
                )
                
                status = response['status']
                
                if status == 'SUCCEEDED':
                    output = json.loads(response.get('output', '{}'))
                    return {
                        'status': 'success',
                        'path': 'STEP_FUNCTIONS_ORCHESTRATED',
                        'execution_arn': execution_arn,
                        'processing_time': time.time() - start_time,
                        'response': self._format_step_functions_output(output),
                        'data': output
                    }
                
                elif status == 'FAILED':
                    return {
                        'status': 'error',
                        'path': 'STEP_FUNCTIONS_FAILED',
                        'execution_arn': execution_arn,
                        'error': response.get('error', 'Unknown error'),
                        'cause': response.get('cause', 'Unknown cause')
                    }
                
                elif status in ['RUNNING', 'PENDING']:
                    print(f"⏳ Step Functions executando... ({status})")
                    time.sleep(5)
                    continue
                
                else:
                    return {
                        'status': 'error',
                        'path': 'STEP_FUNCTIONS_UNKNOWN_STATUS',
                        'execution_status': status
                    }
                    
            except Exception as e:
                return {
                    'status': 'error',
                    'path': 'STEP_FUNCTIONS_MONITORING_ERROR',
                    'error': str(e)
                }
        
        # Timeout
        return {
            'status': 'timeout',
            'path': 'STEP_FUNCTIONS_TIMEOUT',
            'execution_arn': execution_arn,
            'timeout_seconds': timeout
        }
    
    def _format_step_functions_output(self, output: Dict) -> str:
        """Formatar saída do Step Functions"""
        
        lines = []
        
        # Status geral
        if output.get('mcp_results'):
            lines.append("✅ MCP servers executados com sucesso")
        elif output.get('python_fallback_used'):
            lines.append("🔄 Python fallback utilizado")
        
        # IAS
        if 'ias' in output:
            ias_status = output['ias'].get('rationale', 'Validado')
            lines.append(f"🔍 IAS: {ias_status}")
        
        # Cost
        if 'cost' in output:
            cost = output['cost'].get('estimated_cost', 0)
            lines.append(f"💰 Custo estimado: ~USD {cost}/mês")
        
        # Phases
        if 'phases' in output:
            phase_count = len(output['phases'].get('yaml_files', []))
            lines.append(f"📦 {phase_count} phases geradas")
        
        # PR
        if 'pr_url' in output:
            lines.append(f"📬 Pull Request: {output['pr_url']}")
        
        # Execution info
        lines.append(f"🔄 Orquestrado via Step Functions (SEM lambda cola)")
        
        return "\n".join(lines)
    
    def _get_state_machine_arn(self, name: str) -> str:
        """Obter ARN da State Machine"""
        try:
            # Listar state machines e encontrar por nome
            response = self.stepfunctions.list_state_machines()
            
            for sm in response.get('stateMachines', []):
                if name in sm['name']:
                    return sm['stateMachineArn']
            
            # Se não encontrar, usar ARN padrão (ajustar conforme ambiente)
            region = boto3.Session().region_name or 'us-east-1'
            account_id = boto3.client('sts').get_caller_identity()['Account']
            return f"arn:aws:states:{region}:{account_id}:stateMachine:{name}"
            
        except Exception as e:
            print(f"⚠️ Erro obtendo ARN da State Machine {name}: {e}")
            # Retornar ARN padrão
            return f"arn:aws:states:us-east-1:123456789012:stateMachine:{name}"

# Função de conveniência
def process_infrastructure_intent_stepfunctions(nl_intent: str) -> Dict[str, Any]:
    """Processar via Step Functions (elimina lambda cola)"""
    orchestrator = IALOrchestratorStepFunctions()
    return orchestrator.process_nl_intent(nl_intent)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        intent = " ".join(sys.argv[1:])
        result = process_infrastructure_intent_stepfunctions(intent)
        print("\n" + "="*60)
        print("RESULTADO VIA STEP FUNCTIONS (SEM LAMBDA COLA)")
        print("="*60)
        print(result.get('response', 'Erro no processamento'))
        print("="*60)
    else:
        print("Uso: python ial_orchestrator_stepfunctions.py 'sua intenção aqui'")
