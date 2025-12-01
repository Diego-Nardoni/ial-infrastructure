#!/usr/bin/env python3
"""
IAL Natural Language Processor - Safe Version
Versão segura sem supressões perigosas de erro
"""

import sys
import os
import uuid
import json
import readline
import asyncio
import warnings
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path

# Importar logger seguro
IAL_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(IAL_ROOT))

try:
    from ial.core.logging.error_logger import log_error, log_warning, log_info, log_debug
except ImportError:
    # Fallback para print se logger não disponível
    def log_error(msg, exc_info=None): print(f"ERROR: {msg}")
    def log_warning(msg): print(f"WARNING: {msg}")
    def log_info(msg): print(f"INFO: {msg}")
    def log_debug(msg): print(f"DEBUG: {msg}")

# Configurar warnings de forma segura (não suprimir tudo)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

# Configure readline for better input handling
readline.parse_and_bind('Control-l: clear-screen')

class IaLNaturalProcessor:
    def __init__(self):
        """Inicializar processador de linguagem natural"""
        log_info("Initializing IAL Natural Language Processor")
        
        # Verificar modo offline
        self.offline_mode = os.getenv('IAL_MODE') == 'offline' or '--offline' in sys.argv
        if self.offline_mode:
            log_info("Running in OFFLINE mode")
        
        # Inicializar componentes
        self._init_components()
    
    def _init_components(self):
        """Inicializar componentes do sistema"""
        try:
            # Tentar importar Master Engine
            from core.master_engine_final import MasterEngineFinal
            self.master_engine = MasterEngineFinal()
            log_info("Master Engine initialized successfully")
        except ImportError as e:
            log_error(f"Failed to import Master Engine: {e}")
            self.master_engine = None
        
        try:
            # Tentar importar Intelligent Router
            from core.intelligent_mcp_router_sophisticated import IntelligentMCPRouterSophisticated
            self.intelligent_router = IntelligentMCPRouterSophisticated()
            log_info("Intelligent MCP Router initialized successfully")
        except ImportError as e:
            log_warning(f"Intelligent MCP Router not available: {e}")
            self.intelligent_router = None
    
    def process_request(self, user_input: str) -> Dict:
        """Processar solicitação do usuário"""
        try:
            log_info(f"Processing request: {user_input[:50]}...")
            
            if self.offline_mode:
                return self._process_offline(user_input)
            
            # Usar Master Engine se disponível
            if self.master_engine:
                return self.master_engine.process_request(user_input)
            
            # Fallback básico
            return {
                'status': 'error',
                'message': 'No processing engine available',
                'offline_mode': self.offline_mode
            }
            
        except Exception as e:
            log_error(f"Error processing request: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'offline_mode': self.offline_mode
            }
    
    def _process_offline(self, user_input: str) -> Dict:
        """Processar em modo offline (sem chamadas externas)"""
        log_info("Processing in offline mode")
        
        # Lógica básica offline
        if any(word in user_input.lower() for word in ['start', 'deploy', 'foundation']):
            return {
                'status': 'success',
                'message': 'Foundation deployment initiated (offline mode)',
                'action': 'deploy_foundation',
                'offline_mode': True
            }
        
        return {
            'status': 'info',
            'message': 'Request processed in offline mode',
            'offline_mode': True
        }

def main():
    """Função principal do NLP"""
    try:
        processor = IaLNaturalProcessor()
        
        if len(sys.argv) > 1:
            # Processar comando da linha de comando
            user_input = ' '.join(sys.argv[1:])
            result = processor.process_request(user_input)
            print(json.dumps(result, indent=2))
        else:
            # Modo interativo
            print("IAL Natural Language Processor - Safe Mode")
            print("Type 'exit' to quit")
            
            while True:
                try:
                    user_input = input("ial> ").strip()
                    if user_input.lower() in ['exit', 'quit']:
                        break
                    
                    if user_input:
                        result = processor.process_request(user_input)
                        print(json.dumps(result, indent=2))
                        
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except EOFError:
                    break
    
    except Exception as e:
        log_error(f"Fatal error in main: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
