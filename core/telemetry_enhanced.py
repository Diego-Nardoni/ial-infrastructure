#!/usr/bin/env python3
"""
Enhanced Telemetry System
Integração com CloudWatch Logs e OpenTelemetry
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class TelemetryConfig:
    """Configuração de telemetria"""
    cloudwatch_enabled: bool = False
    opentelemetry_enabled: bool = False
    log_group_name: str = "/aws/ial/telemetry"
    service_name: str = "ial-system"

class EnhancedTelemetrySystem:
    """Sistema de telemetria aprimorado com CloudWatch e OpenTelemetry"""
    
    def __init__(self, config: Optional[TelemetryConfig] = None):
        self.config = config or TelemetryConfig()
        self._setup_logging()
        self._setup_cloudwatch()
        self._setup_opentelemetry()
    
    def _setup_logging(self):
        """Configura logging local"""
        log_dir = "/home/ial/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        self.logger = logging.getLogger("ial_telemetry")
        self.logger.setLevel(logging.INFO)
        
        # Handler para arquivo local
        handler = logging.FileHandler(f"{log_dir}/ial_telemetry.log")
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def _setup_cloudwatch(self):
        """Configura integração com CloudWatch Logs"""
        self.cloudwatch_client = None
        
        if self.config.cloudwatch_enabled:
            try:
                import boto3
                self.cloudwatch_client = boto3.client('logs')
                self._ensure_log_group_exists()
            except Exception as e:
                print(f"⚠️ CloudWatch Logs não disponível: {e}")
                self.config.cloudwatch_enabled = False
    
    def _setup_opentelemetry(self):
        """Configura OpenTelemetry"""
        self.tracer = None
        
        if self.config.opentelemetry_enabled:
            try:
                from opentelemetry import trace
                from opentelemetry.sdk.trace import TracerProvider
                from opentelemetry.sdk.trace.export import BatchSpanProcessor
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter
                
                # Configurar provider
                trace.set_tracer_provider(TracerProvider())
                
                # Configurar exporter (Jaeger)
                jaeger_exporter = JaegerExporter(
                    agent_host_name="localhost",
                    agent_port=6831,
                )
                
                span_processor = BatchSpanProcessor(jaeger_exporter)
                trace.get_tracer_provider().add_span_processor(span_processor)
                
                self.tracer = trace.get_tracer(self.config.service_name)
                
            except Exception as e:
                print(f"⚠️ OpenTelemetry não disponível: {e}")
                self.config.opentelemetry_enabled = False
    
    def _ensure_log_group_exists(self):
        """Garante que o log group existe no CloudWatch"""
        try:
            self.cloudwatch_client.create_log_group(
                logGroupName=self.config.log_group_name
            )
        except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
            pass  # Log group já existe
        except Exception as e:
            print(f"⚠️ Erro criando log group: {e}")
    
    def log_event(self, event_type: str, data: Dict[str, Any], request_id: str = None):
        """Log de evento com múltiplos destinos"""
        
        # Criar entrada de log
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "request_id": request_id or self._generate_request_id(),
            "data": data
        }
        
        # Log local (sempre)
        self.logger.info(json.dumps(log_entry))
        
        # CloudWatch Logs (se habilitado)
        if self.config.cloudwatch_enabled and self.cloudwatch_client:
            self._send_to_cloudwatch(log_entry)
        
        # OpenTelemetry (se habilitado)
        if self.config.opentelemetry_enabled and self.tracer:
            self._create_span(event_type, data, request_id)
    
    def _send_to_cloudwatch(self, log_entry: Dict[str, Any]):
        """Envia log para CloudWatch"""
        try:
            import time
            
            self.cloudwatch_client.put_log_events(
                logGroupName=self.config.log_group_name,
                logStreamName=f"ial-{datetime.now().strftime('%Y-%m-%d')}",
                logEvents=[{
                    'timestamp': int(time.time() * 1000),
                    'message': json.dumps(log_entry)
                }]
            )
        except Exception as e:
            print(f"⚠️ Erro enviando para CloudWatch: {e}")
    
    def _create_span(self, event_type: str, data: Dict[str, Any], request_id: str):
        """Cria span OpenTelemetry"""
        try:
            with self.tracer.start_as_current_span(event_type) as span:
                span.set_attribute("request_id", request_id)
                span.set_attribute("event_type", event_type)
                
                # Adicionar atributos dos dados
                for key, value in data.items():
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(f"data.{key}", value)
        except Exception as e:
            print(f"⚠️ Erro criando span: {e}")
    
    def _generate_request_id(self) -> str:
        """Gera request ID único"""
        import uuid
        return str(uuid.uuid4())
    
    def create_operation_span(self, operation_name: str):
        """Cria span para operação (context manager)"""
        if self.config.opentelemetry_enabled and self.tracer:
            return self.tracer.start_as_current_span(operation_name)
        else:
            # Mock context manager se OpenTelemetry não disponível
            class MockSpan:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
                def set_attribute(self, key, value):
                    pass
            return MockSpan()

# Instância global
_telemetry_system = None

def get_telemetry_system() -> EnhancedTelemetrySystem:
    """Obtém instância global do sistema de telemetria"""
    global _telemetry_system
    
    if _telemetry_system is None:
        # Configuração baseada em variáveis de ambiente
        config = TelemetryConfig(
            cloudwatch_enabled=os.environ.get('IAL_CLOUDWATCH_LOGS', 'false').lower() == 'true',
            opentelemetry_enabled=os.environ.get('IAL_OPENTELEMETRY', 'false').lower() == 'true',
            log_group_name=os.environ.get('IAL_LOG_GROUP', '/aws/ial/telemetry'),
            service_name=os.environ.get('IAL_SERVICE_NAME', 'ial-system')
        )
        _telemetry_system = EnhancedTelemetrySystem(config)
    
    return _telemetry_system

def log_event(event_type: str, data: Dict[str, Any], request_id: str = None):
    """Função de conveniência para logging"""
    get_telemetry_system().log_event(event_type, data, request_id)

def create_operation_span(operation_name: str):
    """Função de conveniência para spans"""
    return get_telemetry_system().create_operation_span(operation_name)

if __name__ == "__main__":
    # Teste do sistema
    print("🧪 Testando Enhanced Telemetry System...")
    
    # Teste básico
    log_event("test_event", {"test": "data"})
    
    # Teste com span
    with create_operation_span("test_operation"):
        log_event("operation_event", {"operation": "test"})
    
    print("✅ Telemetria testada com sucesso!")
