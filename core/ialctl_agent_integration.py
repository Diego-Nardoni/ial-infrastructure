#!/usr/bin/env python3
"""
IALCTL Agent Integration
Connects CLI to Bedrock Agent Core with fallback to NLP
"""

import sys
import os
from typing import Dict, Any, Optional

class IALCTLAgentIntegration:
    def __init__(self):
        self.agent_core = None
        self.fallback_engine = None
        self.offline_mode = False
        
        # Try to initialize Bedrock Agent Core
        try:
            from core.bedrock_agent_core import BedrockAgentCore
            self.agent_core = BedrockAgentCore()
            print("🧠 Bedrock Agent Core initialized")
        except Exception as e:
            print(f"⚠️ Agent Core unavailable: {e}")
            self._init_fallback()
    
    def _init_fallback(self):
        """Initialize fallback NLP system"""
        try:
            from core.cognitive_engine import CognitiveEngine
            from core.master_engine_final import MasterEngineFinal
            
            self.fallback_engine = {
                'cognitive': CognitiveEngine(),
                'master': MasterEngineFinal()
            }
            print("🔄 Fallback NLP system initialized")
        except Exception as e:
            print(f"❌ Fallback initialization failed: {e}")
    
    def process_message(self, message: str, offline: bool = False) -> Dict[str, Any]:
        """Process user message via Agent Core or fallback"""
        
        # Force offline mode if requested
        if offline or self.offline_mode:
            return self._process_fallback(message)
        
        # Try Agent Core first
        if self.agent_core:
            try:
                result = self.agent_core.invoke_agent(message)
                if result.get('success'):
                    return {
                        'success': True,
                        'response': result.get('response', ''),
                        'source': 'bedrock_agent',
                        'session_id': result.get('session_id')
                    }
                else:
                    print(f"⚠️ Agent Core error: {result.get('error')}")
                    return self._process_fallback(message)
                    
            except Exception as e:
                print(f"⚠️ Agent Core exception: {e}")
                return self._process_fallback(message)
        
        # Use fallback
        return self._process_fallback(message)
    
    def _process_fallback(self, message: str) -> Dict[str, Any]:
        """Process message using fallback NLP system"""
        
        if not self.fallback_engine:
            self._init_fallback()
        
        if not self.fallback_engine:
            return {
                'success': False,
                'error': 'No processing engine available',
                'source': 'none'
            }
        
        try:
            # Use existing cognitive engine
            result = self.fallback_engine['cognitive'].process_intent(message)
            
            return {
                'success': True,
                'response': result,
                'source': 'fallback_nlp'
            }
            
        except Exception as e:
            try:
                # Fallback to master engine
                result = self.fallback_engine['master'].process_request(message)
                
                return {
                    'success': True,
                    'response': result,
                    'source': 'fallback_master'
                }
                
            except Exception as e2:
                return {
                    'success': False,
                    'error': f'All engines failed: {e}, {e2}',
                    'source': 'error'
                }
    
    def set_offline_mode(self, offline: bool):
        """Set offline mode"""
        self.offline_mode = offline
        if offline:
            print("🔄 Switched to offline mode")
        else:
            print("🧠 Switched to online mode")
    
    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            'agent_core_available': self.agent_core is not None,
            'fallback_available': self.fallback_engine is not None,
            'offline_mode': self.offline_mode,
            'agent_info': self.agent_core.get_agent_info() if self.agent_core else None
        }
    
    def setup_agent(self) -> Dict[str, Any]:
        """Setup Bedrock Agent if not exists"""
        if not self.agent_core:
            return {'success': False, 'error': 'Agent Core not available'}
        
        try:
            result = self.agent_core.create_agent()
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
