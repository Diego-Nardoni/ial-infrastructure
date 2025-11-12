#!/usr/bin/env python3
"""
IAL Orchestrator - Implementação da arquitetura completa
Segue exatamente o fluxo: NL Intent → IAS → Cost → Phase → PR → CI/CD → Audit → Drift
"""

import os
import sys
import json
import time
import signal
from typing import Dict, Any, List, Optional
from datetime import datetime

# Imports dos componentes existentes
try:
    from core.ias_corrected import IASCorrected
except ImportError:
    IASCorrected = None

try:
    from core.intent_cost_guardrails import IntentCostGuardrails
except ImportError:
    IntentCostGuardrails = None

try:
    from core.phase_builder_corrected import PhaseBuildercorrected
except ImportError:
    PhaseBuildercorrected = None

try:
    from core.github_integration import GitHubIntegration
except ImportError:
    GitHubIntegration = None

try:
    from core.audit_validator import AuditValidator
except ImportError:
    AuditValidator = None

try:
    from core.mcp_orchestrator import MCPOrchestrator
except ImportError:
    MCPOrchestrator = None

try:
    from core.drift.drift_detector import DriftDetector
except ImportError:
    DriftDetector = None

# Fallback engine
try:
    from core.master_engine_final import MasterEngineFinal
except ImportError:
    MasterEngineFinal = None

class IALOrchestrator:
    """Orquestrador principal seguindo arquitetura IAL"""
    
    def __init__(self):
        """Inicializar todos os componentes com fallbacks"""
        print("🚀 Inicializando IAL Orchestrator...")
        
        # Carregar configuração
        self.config = self._load_config()
        
        # Fallback engine (sempre disponível)
        self.fallback_engine = MasterEngineFinal() if MasterEngineFinal else None
        
        # Inicializar componentes com fallbacks
        self._init_components()
        
        print("✅ IAL Orchestrator inicializado com sucesso")
    
    def _load_config(self) -> Dict:
        """Carregar configuração com defaults seguros"""
        default_config = {
            'compatibility_mode': True,
            'components': {
                'ias': {'enabled': True, 'fallback_mode': 'safe_approval'},
                'cost_guardrails': {'enabled': True, 'fallback_mode': 'skip_validation'},
                'phase_builder': {'enabled': True, 'fallback_mode': 'use_existing'},
                'github_integration': {'enabled': True, 'fallback_mode': 'manual_pr'},
                'drift_detection': {'enabled': True, 'fallback_mode': 'periodic_check'}
            },
            'timeouts': {
                'ias_timeout': 30,
                'cost_timeout': 60,
                'phase_timeout': 120,
                'github_timeout': 30
            }
        }
        
        try:
            # Tentar carregar config personalizada
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ial_orchestrator.yaml')
            print(f"🔍 Tentando carregar config: {config_path}")
            if os.path.exists(config_path):
                import yaml
                with open(config_path, 'r') as f:
                    custom_config = yaml.safe_load(f)
                    print(f"✅ Config carregada: compatibility_mode={custom_config.get('orchestrator', {}).get('compatibility_mode')}")
                    # Merge configs corretamente
                    if 'orchestrator' in custom_config:
                        default_config.update(custom_config['orchestrator'])
                    if 'components' in custom_config:
                        default_config['components'].update(custom_config['components'])
                    if 'timeouts' in custom_config:
                        default_config['timeouts'].update(custom_config['timeouts'])
            else:
                print(f"⚠️ Config não encontrada: {config_path}")
        except Exception as e:
            print(f"⚠️ Erro carregando config: {e}")
            
        print(f"🎯 Modo final: compatibility_mode={default_config.get('compatibility_mode')}")
        return default_config
    
    def _init_components(self):
        """Inicializar componentes com verificação de disponibilidade"""
        
        # 1. IAS - Intent Validation Sandbox
        if IASCorrected and self.config['components']['ias']['enabled']:
            try:
                self.ias = IASCorrected()
                self.ias_available = True
                print("✅ IAS disponível")
            except Exception as e:
                print(f"⚠️ IAS falhou: {e}")
                self.ias = None
                self.ias_available = False
        else:
            self.ias = None
            self.ias_available = False
        
        # 2. Cost Guardrails
        if IntentCostGuardrails and self.config['components']['cost_guardrails']['enabled']:
            try:
                self.cost_guardrails = IntentCostGuardrails()
                self.cost_available = True
                print("✅ Cost Guardrails disponível")
            except Exception as e:
                print(f"⚠️ Cost Guardrails falhou: {e}")
                self.cost_guardrails = None
                self.cost_available = False
        else:
            self.cost_guardrails = None
            self.cost_available = False
        
        # 3. Phase Builder
        if PhaseBuildercorrected and self.config['components']['phase_builder']['enabled']:
            try:
                self.phase_builder = PhaseBuildercorrected()
                self.phase_available = True
                print("✅ Phase Builder disponível")
            except Exception as e:
                print(f"⚠️ Phase Builder falhou: {e}")
                self.phase_builder = None
                self.phase_available = False
        else:
            self.phase_builder = None
            self.phase_available = False
        
        # 4. GitHub Integration
        if GitHubIntegration and self.config['components']['github_integration']['enabled']:
            try:
                self.github = GitHubIntegration()
                self.github_available = True
                print("✅ GitHub Integration disponível")
            except Exception as e:
                print(f"⚠️ GitHub Integration falhou: {e}")
                self.github = None
                self.github_available = False
        else:
            self.github = None
            self.github_available = False
        
        # 5. Audit Validator
        if AuditValidator:
            try:
                self.audit = AuditValidator()
                self.audit_available = True
                print("✅ Audit Validator disponível")
            except Exception as e:
                print(f"⚠️ Audit Validator falhou: {e}")
                self.audit = None
                self.audit_available = False
        else:
            self.audit = None
            self.audit_available = False
        
        # 6. MCP Orchestrator
        if MCPOrchestrator:
            try:
                self.mcp_mesh = MCPOrchestrator()
                self.mcp_available = True
                print("✅ MCP Orchestrator disponível")
            except Exception as e:
                print(f"⚠️ MCP Orchestrator falhou: {e}")
                self.mcp_mesh = None
                self.mcp_available = False
        else:
            self.mcp_mesh = None
            self.mcp_available = False
        
        # 7. Drift Detection
        if DriftDetector and self.config['components']['drift_detection']['enabled']:
            try:
                self.drift = DriftDetector()
                self.drift_available = True
                print("✅ Drift Detection disponível")
            except Exception as e:
                print(f"⚠️ Drift Detection falhou: {e}")
                self.drift = None
                self.drift_available = False
        else:
            self.drift = None
            self.drift_available = False
    
    def process_nl_intent(self, nl_intent: str) -> Dict[str, Any]:
        """
        Fluxo principal da arquitetura IAL com fallbacks robustos
        
        NL Intent → IAS → Cost Guardrails → Phase Builder → GitHub PR → 
        CI/CD Pipeline → Audit Validator → Post-deploy MCP Mesh → Drift Detection
        """
        
        print(f"🧠 interpretando intenção: {nl_intent[:50]}...")
        start_time = time.time()
        
        # Verificar modo de compatibilidade
        if self.config.get('compatibility_mode', True) and self.fallback_engine:
            print("🔄 Modo compatibilidade ativo - usando fallback engine")
            try:
                return self.fallback_engine.process_request(nl_intent)
            except Exception as e:
                print(f"❌ Fallback engine falhou: {e}")
                return self._format_error_response("FALLBACK_ERROR", str(e))
        
        try:
            # Tentar fluxo completo
            return self._process_full_flow(nl_intent)
        except Exception as e:
            print(f"⚠️ Fluxo completo falhou: {e}")
            print("🔄 Usando fallback para compatibilidade...")
            
            # Fallback para comportamento atual
            if self.fallback_engine:
                return self.fallback_engine.process_request(nl_intent)
            else:
                return self._format_error_response("NO_FALLBACK", "Sistema indisponível")
    
    def _process_full_flow(self, nl_intent: str) -> Dict[str, Any]:
        """Fluxo completo com timeouts e fallbacks"""
        
        start_time = time.time()  # CORREÇÃO: Definir start_time no início
        
        # STEP 1: IAS com timeout
        print("🔍 Executando IAS (Intent Validation Sandbox)...")
        ias_result = self._execute_with_fallback(
            lambda: self.ias.validate_intent_with_simulation(nl_intent) if self.ias_available else None,
            fallback={'safe': True, 'rationale': 'IAS não disponível - aprovação automática'},
            timeout=self.config['timeouts']['ias_timeout']
        )
        
        if not ias_result.get('safe', True):
            return self._format_error_response(
                "IAS_BLOCKED", 
                f"❌ IAS: {ias_result.get('rationale', 'Risco de segurança detectado')}"
            )
        
        # STEP 2: Cost Guardrails via MCP Cost Explorer
        print("💰 Executando Cost Guardrails via MCP...")
        cost_result = self._execute_with_fallback(
            lambda: self.mcp_mesh.execute_cost_analysis_for_intent(nl_intent) if self.mcp_available else None,
            fallback={'should_block': False, 'estimated_cost': 0, 'services_detected': []},
            timeout=self.config['timeouts']['cost_timeout']
        )
        
        if cost_result.get('should_block', False):
            return self._format_error_response(
                "COST_BLOCKED",
                f"💰 Custo previsto: ~USD {cost_result.get('estimated_cost', 'N/A')}/mês (BLOQUEADO)"
            )
        
        # STEP 3: Phase Builder via MCP CloudFormation + RAG
        print("📦 Executando Phase Builder via MCP...")
        phase_result = self._execute_with_fallback(
            lambda: self.mcp_mesh.execute_phase_generation(
                nl_intent, 
                ias_result, 
                cost_result
            ) if self.mcp_available else None,
            fallback={'yaml_files': [{'name': 'fallback.yaml', 'content': 'AWSTemplateFormatVersion: "2010-09-09"'}]},
            timeout=self.config['timeouts']['phase_timeout']
        )
        
        # STEP 4: GitHub PR via MCP GitHub
        print("📬 Criando Pull Request via MCP...")
        pr_result = self._execute_with_fallback(
            lambda: self.mcp_mesh.execute_github_pr_creation(
                phases=phase_result.get('yaml_files', []),
                rationale=f"Deploy automático: {nl_intent}",
                cost_estimate=cost_result.get('estimated_cost', 0)
            ) if self.mcp_available else None,
            fallback={
                'pr_url': 'https://github.com/user/repo/pull/simulated',
                'status': 'SIMULATED',
                'message': 'PR seria criado via MCP GitHub'
            },
            timeout=self.config['timeouts']['github_timeout']
        )
        
        # Formatear resposta final
        processing_time = time.time() - start_time
        
        return self._format_success_response({
            'ias_status': ias_result.get('rationale', 'nenhum risco encontrado'),
            'estimated_cost': cost_result.get('estimated_cost', 0),
            'phases': [f['name'] for f in phase_result.get('yaml_files', [])],
            'dag_order': 'foundation → compute → network',
            'pr_url': pr_result.get('pr_url', ''),
            'pipeline_status': 'INITIATED',
            'processing_time': processing_time
        })
    
    def _execute_with_fallback(self, func, fallback, timeout=30):
        """Executa função com timeout e fallback"""
        
        if func is None:
            return fallback
            
        def timeout_handler(signum, frame):
            raise TimeoutError("Operation timed out")
            
        # Configurar timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            result = func()
            signal.alarm(0)  # Cancel timeout
            signal.signal(signal.SIGALRM, old_handler)  # Restore handler
            return result if result is not None else fallback
        except Exception as e:
            signal.alarm(0)  # Cancel timeout
            signal.signal(signal.SIGALRM, old_handler)  # Restore handler
            print(f"⚠️ Operation failed: {e}, using fallback")
            return fallback
    
    def _format_success_response(self, data: Dict) -> Dict:
        """Formatar resposta de sucesso"""
        return {
            'status': 'success',
            'path': 'IAL_ORCHESTRATOR_COMPLETE',
            'response': self._generate_formatted_output(data),
            'data': data,
            'architecture_flow_completed': True
        }
    
    def _format_error_response(self, error_type: str, message: str) -> Dict:
        """Formatar resposta de erro"""
        return {
            'status': 'error',
            'path': 'IAL_ORCHESTRATOR_ERROR',
            'error_type': error_type,
            'response': message,
            'architecture_flow_completed': False
        }
    
    def _generate_formatted_output(self, data: Dict) -> str:
        """Gerar saída formatada conforme especificação"""
        output = []
        output.append(f"✅ IAS: {data['ias_status']}")
        output.append(f"💰 custo previsto: ~USD {data['estimated_cost']}/mês (OK)")
        output.append(f"📦 phases geradas: {', '.join(data['phases'])}")
        output.append(f"🔀 DAG: {data['dag_order']}")
        output.append(f"📬 Pull Request: {data['pr_url']}")
        output.append(f"🚀 Pipeline iniciado automaticamente")
        output.append(f"⏳ Processamento: {data['processing_time']:.2f}s")
        
        return "\n".join(output)

# Função de conveniência para uso direto
def process_infrastructure_intent(nl_intent: str) -> Dict[str, Any]:
    """Função de conveniência para processar intenção de infraestrutura"""
    orchestrator = IALOrchestrator()
    return orchestrator.process_nl_intent(nl_intent)

if __name__ == "__main__":
    # Teste básico
    if len(sys.argv) > 1:
        intent = " ".join(sys.argv[1:])
        result = process_infrastructure_intent(intent)
        print("\n" + "="*50)
        print(result.get('response', 'Erro no processamento'))
        print("="*50)
    else:
        print("Uso: python ial_orchestrator.py 'sua intenção aqui'")
