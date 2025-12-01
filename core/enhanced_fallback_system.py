#!/usr/bin/env python3
"""
Enhanced Fallback System - Sistema de Fallback Inteligente
Gerencia fallback entre Bedrock Agent Core e NLP Local
"""

import json
import uuid
import time
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class ProcessingMode(Enum):
    AGENT_CORE = "agent_core"
    FALLBACK_NLP = "fallback_nlp"
    SANDBOX = "sandbox"

@dataclass
class TelemetryEvent:
    request_id: str
    timestamp: str
    event_type: str
    mode: ProcessingMode
    data: Dict[str, Any]
    duration_ms: Optional[float] = None

class EnhancedFallbackSystem:
    def __init__(self):
        self.request_id = str(uuid.uuid4())
        self.telemetry_events = []
        
    def determine_processing_mode(self, user_input: str, flags: Dict[str, Any]) -> ProcessingMode:
        """Determina o modo de processamento baseado em flags e disponibilidade"""
        
        # Modo sandbox forçado
        if flags.get('sandbox') or self._is_sandbox_mode():
            self._log_event("sandbox_mode_processing", {"reason": "sandbox_flag_or_env"})
            return ProcessingMode.SANDBOX
        
        # Modo offline forçado
        if flags.get('offline'):
            self._log_event("using_fallback_nlp", {"reason": "offline_flag"})
            return ProcessingMode.FALLBACK_NLP
        
        # Tentar Agent Core primeiro
        if self._is_agent_core_available():
            self._log_event("attempting_agent_core", {"user_input_length": len(user_input)})
            return ProcessingMode.AGENT_CORE
        else:
            self._log_event("using_fallback_nlp", {"reason": "agent_core_unavailable"})
            return ProcessingMode.FALLBACK_NLP
    
    def process_with_fallback(self, user_input: str, mode: ProcessingMode) -> Dict[str, Any]:
        """Processa com fallback automático em caso de erro"""
        start_time = time.time()
        
        try:
            if mode == ProcessingMode.AGENT_CORE:
                result = self._process_agent_core(user_input)
                self._log_event("agent_core_success", {"response_length": len(str(result))}, 
                              duration_ms=(time.time() - start_time) * 1000)
                return result
            
            elif mode == ProcessingMode.SANDBOX:
                result = self._process_sandbox(user_input)
                self._log_event("sandbox_processing_complete", {"preview_generated": True},
                              duration_ms=(time.time() - start_time) * 1000)
                return result
            
            else:  # FALLBACK_NLP
                result = self._process_nlp_fallback(user_input)
                self._log_event("fallback_nlp_success", {"response_length": len(str(result))},
                              duration_ms=(time.time() - start_time) * 1000)
                return result
                
        except Exception as e:
            # Fallback automático para NLP se Agent Core falhar
            if mode == ProcessingMode.AGENT_CORE:
                self._log_event("agent_core_failed", {"error": str(e), "falling_back": True})
                return self.process_with_fallback(user_input, ProcessingMode.FALLBACK_NLP)
            else:
                self._log_event("processing_error", {"mode": mode.value, "error": str(e)})
                raise
    
    def _process_agent_core(self, user_input: str) -> Dict[str, Any]:
        """Processa via Bedrock Agent Core"""
        try:
            from core.bedrock_agent_core import BedrockAgentCore
            agent = BedrockAgentCore()
            return agent.invoke_agent(user_input, session_id=self.request_id)
        except ImportError:
            raise Exception("Bedrock Agent Core not available")
    
    def _process_nlp_fallback(self, user_input: str) -> Dict[str, Any]:
        """Processa via NLP Local (fallback)"""
        try:
            from core.cognitive_engine import CognitiveEngine
            engine = CognitiveEngine()
            return engine.process_intent(user_input)
        except ImportError:
            from core.master_engine_final import MasterEngineFinal
            engine = MasterEngineFinal()
            return engine.process_request(user_input)
    
    def _process_sandbox(self, user_input: str) -> Dict[str, Any]:
        """Processa em modo sandbox (sem AWS operations)"""
        import os
        from datetime import datetime
        
        # Criar diretório sandbox
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sandbox_dir = f"/home/ial/sandbox_outputs/{timestamp}"
        os.makedirs(sandbox_dir, exist_ok=True)
        
        # Gerar preview usando Phase Builder
        try:
            from core.desired_state import DesiredStateBuilder
            builder = DesiredStateBuilder()
            preview = builder.build_desired_spec(user_input, preview_mode=True)
            
            # Salvar preview
            preview_file = f"{sandbox_dir}/phases_preview.yaml"
            with open(preview_file, 'w') as f:
                f.write(str(preview))
            
            return {
                "mode": "sandbox",
                "preview_generated": True,
                "output_path": preview_file,
                "message": f"Preview gerado em {preview_file}. Nenhuma operação AWS executada."
            }
        except Exception as e:
            return {
                "mode": "sandbox",
                "error": str(e),
                "message": "Erro ao gerar preview em modo sandbox"
            }
    
    def _is_agent_core_available(self) -> bool:
        """Verifica se Bedrock Agent Core está disponível via arquivo de configuração"""
        try:
            import os
            import json
            
            config_file = os.path.expanduser('~/.ial/agent_config.json')
            
            if not os.path.exists(config_file):
                return False
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            return (
                config.get('bedrock_supported', False) and
                config.get('agent_id') is not None and
                config.get('agent_alias_id') is not None
            )
            
        except Exception:
            return False
    
    def _is_sandbox_mode(self) -> bool:
        """Verifica se está em modo sandbox via environment"""
        import os
        return os.getenv('IAL_MODE') == 'sandbox'
    
    def _log_event(self, event_type: str, data: Dict[str, Any], duration_ms: Optional[float] = None):
        """Registra evento de telemetria"""
        event = TelemetryEvent(
            request_id=self.request_id,
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            mode=ProcessingMode.AGENT_CORE,  # Will be updated by caller
            data=data,
            duration_ms=duration_ms
        )
        self.telemetry_events.append(event)
        
        # Log estruturado
        self._write_telemetry_log(event)
    
    def _write_telemetry_log(self, event: TelemetryEvent):
        """Escreve log de telemetria estruturado"""
        import os
        
        log_entry = {
            "request_id": event.request_id,
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "mode": event.mode.value,
            "data": event.data,
            "duration_ms": event.duration_ms
        }
        
        # Escrever para arquivo de log
        log_dir = "/home/ial/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = f"{log_dir}/ial_telemetry.log"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Retorna resumo da telemetria da sessão"""
        return {
            "request_id": self.request_id,
            "total_events": len(self.telemetry_events),
            "events": [
                {
                    "event_type": e.event_type,
                    "timestamp": e.timestamp,
                    "duration_ms": e.duration_ms
                } for e in self.telemetry_events
            ]
        }
