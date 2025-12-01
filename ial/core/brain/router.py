#!/usr/bin/env python3
"""
IAL Brain Router - Roteamento inteligente consolidado
"""

import os
import sys
from pathlib import Path

# Adicionar path do IAL
IAL_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(IAL_ROOT))

class BrainRouter:
    """Router principal do sistema cognitivo IAL"""
    
    def __init__(self):
        self.offline_mode = os.getenv('IAL_MODE') == 'offline'
        self._init_engines()
    
    def _init_engines(self):
        """Inicializar engines disponíveis"""
        try:
            from core.cognitive_engine import CognitiveEngine
            self.cognitive_engine = CognitiveEngine()
        except ImportError:
            self.cognitive_engine = None
        
        try:
            from core.master_engine_final import MasterEngineFinal
            self.master_engine = MasterEngineFinal()
        except ImportError:
            self.master_engine = None
    
    def route_request(self, request: str) -> dict:
        """Rotear solicitação para o engine apropriado"""
        
        if self.offline_mode:
            return self._handle_offline(request)
        
        # Usar Master Engine como principal
        if self.master_engine:
            return self.master_engine.process_request(request)
        
        # Fallback para Cognitive Engine
        if self.cognitive_engine:
            return self.cognitive_engine.process_user_request(request)
        
        return {
            'status': 'error',
            'message': 'No cognitive engines available'
        }
    
    def _handle_offline(self, request: str) -> dict:
        """Lidar com solicitações em modo offline"""
        return {
            'status': 'offline',
            'message': 'Processing in offline mode',
            'request': request
        }
