#!/usr/bin/env python3
"""
Master Engine Final - Integração CORE + USER Paths
Entrada única que decide entre Bootstrap CORE ou Pipeline USER
"""

import sys
import os
from typing import Dict, Any
from datetime import datetime

class MasterEngineFinal:
    def __init__(self):
        """Inicializar Resource Router e engines"""
        
        try:
            from core.resource_router import ResourceRouter
            self.resource_router = ResourceRouter()
            print("✅ Resource Router carregado")
        except ImportError as e:
            print(f"❌ Resource Router não disponível: {e}")
            self.resource_router = None
        
        try:
            from core.cognitive_engine import CognitiveEngine
            self.cognitive_engine = CognitiveEngine()
            print("✅ Cognitive Engine carregado")
        except ImportError as e:
            print(f"❌ Cognitive Engine não disponível: {e}")
            self.cognitive_engine = None
        
        try:
            from core.mcp_infrastructure_manager import MCPInfrastructureManager
            from core.intelligent_mcp_router import IntelligentMCPRouter
            router = IntelligentMCPRouter()
            self.mcp_infrastructure_manager = MCPInfrastructureManager(router)
            print("✅ MCP Infrastructure Manager carregado")
        except ImportError as e:
            print(f"❌ MCP Infrastructure Manager não disponível: {e}")
            self.mcp_infrastructure_manager = None
    
    def process_request(self, nl_intent: str, config: Dict = None) -> Dict[str, Any]:
        """
        ENTRADA ÚNICA: Decide CORE ou USER path baseado na intenção
        
        Args:
            nl_intent: Intenção em linguagem natural
            config: Configuração opcional
            
        Returns:
            Resultado do processamento
        """
        
        print(f"🎯 Master Engine processando: '{nl_intent[:50]}...'")
        
        if not self.resource_router:
            return {'error': 'Resource Router não disponível', 'status': 'error'}
        
        # Routing Decision
        path = self.resource_router.route_request(nl_intent)
        routing_explanation = self.resource_router.get_routing_explanation(nl_intent)
        
        print(f"🔀 Routing: {path}")
        print(f"📋 Rationale: {routing_explanation['rationale']}")
        
        if path == "CORE_PATH":
            return self.process_core_path(nl_intent, config or {})
        
        elif path == "USER_PATH":
            return self.process_user_path(nl_intent)
        
        else:
            return {
                'error': f'Unknown routing path: {path}',
                'status': 'error',
                'routing': routing_explanation
            }
    
    def process_core_path(self, nl_intent: str, config: Dict) -> Dict[str, Any]:
        """
        CORE PATH: Bootstrap CORE resources via MCP Infrastructure Manager
        """
        
        print("🔧 Executando CORE PATH - Bootstrap IAL Foundation")
        
        if not self.mcp_infrastructure_manager:
            return {
                'error': 'MCP Infrastructure Manager não disponível',
                'status': 'error',
                'path': 'CORE_PATH'
            }
        
        try:
            # Deploy via MCP Infrastructure Manager (42 componentes)
            import asyncio
            result = asyncio.run(
                self.mcp_infrastructure_manager.deploy_ial_infrastructure(config)
            )
            
            return {
                'status': 'success',
                'path': 'CORE_PATH',
                'method': 'mcp_infrastructure_manager',
                'components_created': result.get('deployment_summary', {}).get('foundation_components', 0),
                'details': result,
                'processing_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ CORE PATH error: {str(e)}")
            return {
                'status': 'error',
                'path': 'CORE_PATH',
                'error': str(e),
                'method': 'mcp_infrastructure_manager'
            }
    
    def process_user_path(self, nl_intent: str) -> Dict[str, Any]:
        """
        USER PATH: Arquitetura de referência completa via Cognitive Engine
        """
        
        print("👤 Executando USER PATH - Arquitetura de Referência")
        
        if not self.cognitive_engine:
            return {
                'error': 'Cognitive Engine não disponível',
                'status': 'error',
                'path': 'USER_PATH'
            }
        
        try:
            # Pipeline completo: NL → IAS → Cost → Phase Builder → GitHub PR → CI/CD → Audit → Auto-Heal
            result = self.cognitive_engine.process_user_request(nl_intent)
            
            result['path'] = 'USER_PATH'
            return result
            
        except Exception as e:
            print(f"❌ USER PATH error: {str(e)}")
            return {
                'status': 'error',
                'path': 'USER_PATH',
                'error': str(e),
                'method': 'cognitive_engine'
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Verificar status do sistema"""
        
        return {
            'master_engine': 'active',
            'resource_router': self.resource_router is not None,
            'cognitive_engine': self.cognitive_engine is not None,
            'mcp_infrastructure_manager': self.mcp_infrastructure_manager is not None,
            'timestamp': datetime.now().isoformat()
        }
